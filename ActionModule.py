"""
* ActionModule (does things) [Alex/Marco/Mauro]
  - Maintains a list of Actions that can be performed
  - Handles conflicting concurrent gestures (note: we need to talk about how to resolve this)
  - Handles gestures that would take the system out of range (such as chaining gestures in one direction, providing illegal parameters, etc)
  - Handles eye stabilisation
  - Handles zero-finding during startup (in case of unexpected shutdown)
"""

import Queue
import threading
import json
import os
import glob
import csv
import warnings

import ArduinoCommunicator
import time

from Action import *
from Marionette import *

from threading import Thread
from time import sleep

class ActionModule(object):

    def __init__(self, dummy=False):
        """ port = usb port of the arduino controling the motors
            set to "" on a computer without arduino
        """

        self.dummy = dummy

        # this variable is True when no gestures are being executed
        self.isIdle = True

        self.headDataUpdated = False

        # TODO: hardcoded configs?
        gesture_files = {
            "neutral": "gestures/neutral_gestures.csv",
            "fear": "gestures/fear_gestures.csv",
            "longing": "gestures/longing_gestures.csv",
            "surprise": "gestures/surprise_gestures.csv",
            "shame": "gestures/shame_gestures.csv"
        }

        # contains a dictionary of emotions to sequences
        self.gestureNameToSeq = {}
        # reading gesture files
        for gesture_type, filename in gesture_files.iteritems():
            with open(filename, "r") as f:
                reader = csv.reader(f)
                reader.next()
                for row in reader:
                    self.gestureNameToSeq[gesture_type + "_" + row[0]] = (float(row[1]),row[2:])

        # Read the positions from the Positions.json file
        self.positions = {}


        # Read the positions from the json files
        fileList = ["Positions.json"]
        try:
            os.chdir("./Positions")
            for filename in glob.glob("*.json"):
                fileList.append("Positions/" + filename)
            os.chdir("..")
        except:
            pass

        for filename in fileList:
            self.loadPositionsFromFile(filename)

        self.timeInterval = 0.25 # (1/4 second)

        # Initialize the angles to the marionette's default (0 everywhere)
        self.currentAngles = Marionette().getAngles()
        self.currentTargetAngles = Marionette().getAngles()
        self.targetReached = False

        # Head IMU angles:
        self.roll = 0
        self.pitch = 0
        self.yawn = 0
        self.pitchMax = 0
        self.pitchMin = 0
        self.yawnMax = 0
        self.yawnMin = 0

        # Max x and y in camera coordinates space
        self.cameraMaxX = 1920
        self.cameraMaxY = 1080

        # Read the calibration file
        self.calibration = []
        filename = "IMUCameraCalibration.json"
        with open(filename, "r") as read_file:
            self.calibration = json.load(read_file)
            print self.calibration
            self.pitchMax = self.calibration["up"][1]
            self.pitchMin = self.calibration["down"][1]
            self.yawnMax = self.calibration["left"][2]
            self.yawnMin = self.calibration["right"][2]

        # motor name to Arduino motor id
        self.arduinoID = {}
        self.arduinoID['motorH'] = 'head'
        self.arduinoID['motorS'] = 'shoulder'
        self.arduinoID['motorHR'] = 0    # "Right head"
        self.arduinoID['motorHL'] = 1    # "Left head"
        self.arduinoID['motorSR'] = 9    # "Right shoulder"
        self.arduinoID['motorSL'] = 8    # "Left shoulder"
        self.arduinoID['motorAR'] = -1   # "Right arm"
        self.arduinoID['motorAL'] = 7    # "Left arm"
        self.arduinoID['motorWR'] = 2    # "Right hand"
        self.arduinoID['motorWL'] = 3    # "Left hand"
        self.arduinoID['motorFR'] = 5    # "Right foot"
        self.arduinoID['motorFL'] = 4    # "Left foot"
        self.arduinoID['motorEX'] = 'eyeX'    # "Eye horizontal"
        self.arduinoID['motorEY'] = 'eyeY'    # "Eye vertical"

        # Arduino motor id to index of the angle in the angles list
        # motor:       'S' 'SR' 'SL' 'AR' 'AL' 'H' 'HR' 'HL' 'FR' 'FL' 'WR' 'WL' 'EX' 'EY'
        # angle index:  0    1    2    3    4   5    6    7    8    9   10   11   12   13
        # arduino id:   s  m,9  m,8   -1  m,7   h  m,0  m,1  m,5  m,4  m,2  m,3      e
        self.arduinoIDToAngleIndex = {}
        self.arduinoIDToAngleIndex['h'] = 5
        self.arduinoIDToAngleIndex['s'] = 0
        self.arduinoIDToAngleIndex['0'] = 6     # "Right head"
        self.arduinoIDToAngleIndex['1'] = 7     # "Left head"
        self.arduinoIDToAngleIndex['9'] = 1     # "Right shoulder"
        self.arduinoIDToAngleIndex['8'] = 2     # "Left shoulder"
        #self.arduinoIDToAngleIndex['6'] = 3   # "Right arm"
        self.arduinoIDToAngleIndex['7'] = 4     # "Left arm"
        self.arduinoIDToAngleIndex['2'] = 10    # "Right hand"
        self.arduinoIDToAngleIndex['3'] = 11    # "Left hand"
        self.arduinoIDToAngleIndex['5'] = 8     # "Right foot"
        self.arduinoIDToAngleIndex['4'] = 9     # "Left foot"
        self.arduinoIDToAngleIndex['e,x'] = 12  # "Eye horizontal"
        self.arduinoIDToAngleIndex['e,y'] = 13  # "Eye vertical"

        # Thread related variables
        self.movementCount = long(0)

        self.qMotorCmds = Queue.PriorityQueue()
        self.running = False
        self.arduino_thread = None
        self.start()

    def __del__(self):
        self.stop()


    def stop(self):
        if self.running:
            self.running = False
            self.arduino_thread.join()


    def start(self):
        if not self.running:
            # Starts the thread
            self.running = True
            self.arduino_thread = threading.Thread(name='Arduino', target=self.threadFunc, args=(self.dummy,))
            self.arduino_thread.setDaemon(True)
            self.arduino_thread.start()


    def clearQueue(self):
        while not self.qMotorCmds.empty():
            try:
                self.qMotorCmds.get(False)
            except Empty:
                continue
            self.qMotorCmds.task_done()


    def getMovementCount(self):
        self.movementCount += 1
        return self.movementCount

    def threadFunc(self, dummy):
        if dummy:
            print "Dummy Arduino thread started."
            while(self.running):
                self.isIdle = True
                if not self.qMotorCmds.empty():
                    self.isIdle = False
                    cmds = self.qMotorCmds.get()
                    #This line of code unwraps the actual command from its priority, since we're now using a PriorityQueue
                    cmds = cmds[1]
                    for cmd in cmds:
                        id = self.arduinoID[cmd[0]]
                        angle = int(cmd[1])
                        speed = int(cmd[2])
                        #print "id:",id," angle:",angle," speed:",speed
                    #time.sleep(1)
            print "Dummy Arduino thread stopped."
        else:

            print "Arduino thread started."
            self.ac = ArduinoCommunicator.ArduinoCommunicator("/dev/ttyUSB0")

            while(self.running):
                if not self.qMotorCmds.empty():
                    self.isIdle = False
                    cmds = self.qMotorCmds.get()
                    #This line of code unwraps the actual command from its priority, since we're now using a PriorityQueue
                    cmds = cmds[1]

                    eyeMotion = False
                    # Sets the eye angles to the current value
                    eyeAngleX = self.currentAngles[12]
                    eyeAngleY = self.currentAngles[13]
                    eyeSpeedX = 0
                    eyeSpeedY = 0
                    self.targetReached = False
                    for cmd in cmds:
                        # print "step = ", step
                        if cmd[0] == 'requestHeadData':
                            self.ac.requestHeadData()
                        elif cmd[0] == 'IMU':
                            on = bool(cmd[1])
                            if on:
                                self.ac.engageIMU()
                            else:
                                self.ac.disengageIMU()
                        else:
                            # Motor command
                            id = self.arduinoID[cmd[0]]
                            angle = int(cmd[1])
                            speed = int(cmd[2])
                            if angle is None or speed == 0:
                                # No motion
                                continue
                            if id == -1:
                                # Obsolete motor AR
                                continue
                            if id == 'head':
                                self.ac.rotateHead(angle, speed)
                            elif id == 'shoulder':
                                self.ac.rotateShoulder(angle, speed)
                            elif id == 'eyeX':
                                eyeMotion = True
                                eyeAngleX = angle
                                eyeSpeedX = speed
                            elif id == 'eyeY':
                                eyeMotion = True
                                eyeAngleY = angle
                                eyeSpeedY = speed
                            else:
                                # Other motors
                                self.ac.rotateStringMotor(id, angle, speed)

                    if eyeMotion:
                        self.ac.rotateEyes(eyeAngleX, eyeAngleY, eyeSpeedX, eyeSpeedY)

                # Read from the arduino
                receivedData = self.ac.receive()
                if receivedData != '':
                    #print "received data: ", receivedData
                    self.updateAnglesFromFeedback(receivedData)

                # Check for target reached:
                if self.checkTargetReached():
                    self.targetReached = True
                    self.isIdle = True
                    #print "Target reached!!!!! \n"

            print "Arduino thread stopped."


    def checkTargetReached(self):
	reached_target = True
	motors_to_ignore = [self.arduinoIDToAngleIndex['h'], self.arduinoIDToAngleIndex['e,x'], self.arduinoIDToAngleIndex['e,y']]
        for angleIndex in range(0, len(self.currentAngles)):
            # ignoring some motors
            if angleIndex in motors_to_ignore:
                continue
            if abs(self.currentAngles[angleIndex] - self.currentTargetAngles[angleIndex]) > 1:
	        reached_target = False
	#if not reached_target:
	#    print "currentAngles = ", self.currentAngles
	#    print "targetAngles = ", self.currentTargetAngles
 	#    return False
        return True


    def updateAnglesFromFeedback(self, receivedData):
        # Parse data: m,<id>,<angle>
        id = -1
        data = receivedData.split(",")
        #print "Data received = ", receivedData
        if data[0] == "m":
            if len(data) == 3:
                id = self.arduinoIDToAngleIndex[data[1]]
                angle = int(data[2])
                self.currentAngles[id] = angle
        elif data[0] == "s" or data[0] == "h":
            if len(data) == 2:
                id = self.arduinoIDToAngleIndex[data[0]]
                angle = int(data[1])
                self.currentAngles[id] = angle
        elif data[0] == "e":
            if len(data) == 3:
                id = self.arduinoIDToAngleIndex['e,x']
                angle = int(data[1])
                self.currentAngles[id] = angle
                id = self.arduinoIDToAngleIndex['e,y']
                angle = int(data[2])
                self.currentAngles[id] = angle
        elif data[0] == "a":
            if len(data) == 4:
                self.roll = int(data[1])
                self.pitch = int(data[2])
                self.yawn = int(data[3])
                self.headDataUpdated = True
        #print "currentAngles = ", self.currentAngles
	#print "targetAngles = ", self.currentTargetAngles


    def moveToAngles(self, target, speeds):
        action = Action(target, self.timeInterval)
        output = action.getCmdsToTarget(self.currentAngles, speeds)
        newTargetAngles = []
        for oldAngle, newAngle in zip(self.currentTargetAngles, target):
            if newAngle is None:
                newTargetAngles.append(oldAngle)
            else:
                newTargetAngles.append(newAngle)
        # print "self.currentAngles = ", self.currentAngles
        # print "target = ", target
        # print "newTargetAngles = ", newTargetAngles
        self.currentTargetAngles = newTargetAngles

        #This wraps the actual command in a tuple, the first element of which is the priority, which is another tuple of
        #  the form (1,movementCount). The second element is the actual output. Eye and head movements are instead
        #  inserted with priority (0,movementCount).  The tuple for priority is required because PriorityQueue does not
        #  respect insertion order, just priority.  --Kaz.
        self.qMotorCmds.put(((1,self.getMovementCount()),output))
        return self.currentTargetAngles


    def moveTo(self, targetKey):
        if targetKey not in self.positions.keys():
            print "No targetKey = ", targetKey
            return None

        position = self.positions[targetKey]
        return self.moveToAngles(position['angles'], position['speeds'])

    def executeGesture(self, sequenceList):

        # This function will be executed by a thread to execute a sequence
        def executeSequence(seqList):
            print("executing: " + str(seqList))
            for item in seqList:
                try:
                    # if int -> sleep
                    delay = float(item)
                    sleep(delay)
                except:
                    # if str -> execute
                    if type(item) is tuple:
                        if item[0] == "eyes":
                            self.moveEyes(item[1:])
			    #pass
                        if item[0] == "eyes+head":
                            self.moveEyesAndHead(item[1:])
			    #pass
                    else:
                        self.moveTo(item)

        seqThread = Thread(target=executeSequence, args=[sequenceList])
        seqThread.start()


    def isMarionetteIdle(self):
        return self.isIdle

    def cameraCoordsToEyeWorld(self, targetCameraCoords):
        # From a target in camera coordinates, get the eye pitch/yawn in world space
        # to look at that point
        # Uses the current angles data (caller should update first if needed)
        pitchRange = self.pitchMax - self.pitchMin
        yawnRange = self.yawnMax - self.yawnMin
        pitchFactor = targetCameraCoords[1] / self.cameraMaxY
        yawnFactor = targetCameraCoords[0] / self.cameraMaxX
        eyePitch = self.pitchMax - pitchFactor * pitchRange
        eyeYawn = self.yawnMax - yawnFactor * yawnRange
        return eyePitch, eyeYawn


    def eyeWorldToCameraCoords(self, eyePitch, eyeYawn):
        # Inverse from cameraCoordsToEyeWorld
        pitchRange = self.pitchMax - self.pitchMin
        yawnRange = self.yawnMax - self.yawnMin
        pitchFactor = (self.pitchMax - eyePitch) / pitchRange
        yawnFactor = (self.yawnMax - eyeYawn) / yawnRange
        x = yawnFactor * self.cameraMaxX
        y = pitchFactor * self.cameraMaxY
        return [x, y]


    def moveEyes(self, targetCameraCoords):
#        print "Move eyes to",targetCameraCoords
        self.updateHeadData()
        targetPitch, targetYawn = self.cameraCoordsToEyeWorld(targetCameraCoords)
        # Current eye pitch and yawn (includes head orientation)
        eyePitch = targetPitch - self.pitch
        eyeYawn = targetYawn - self.yawn
        eyeAngleX = 90 + eyePitch
        eyeAngleY = 90 + eyeYawn
        speed = 25 # arbitrary speed value
        command = [['motorEX', eyeAngleX, speed], ['motorEY', eyeAngleY, speed]]
        self.qMotorCmds.put(((0,self.getMovementCount()), command))

    def moveEyesAndHead(self, targetCameraCoords):
#        print "Move eyes and head to", targetCameraCoords
        # First move the eyes to the target
        self.moveEyes(targetCameraCoords)
        # Then engage IMU
        self.qMotorCmds.put(((0,self.getMovementCount()), [['IMU' , 1]]))
        # Then move the head to face the target (data already updated when calling moveEyes)
        targetPitch, targetYawn = self.cameraCoordsToEyeWorld(targetCameraCoords)
        speed = 20 # arbitrary speed value
        self.qMotorCmds.put(((0,self.getMovementCount()), [['motorH', -targetYawn, speed]]))
        # For now ignore the pitch. Not sure what is the correspondance between head motor
        # angle and pitch
        # Disengage IMU
        self.qMotorCmds.put(((0,self.getMovementCount()), [['IMU' , 0]]))

    def eyeTargetToAngles(self, eyeToWorld, target):
        """Compute the eye angles (pitch and yaw) using the eye transform matrix
            in world space to have the marionette look at target
            Should be computed for each position sent to the marionette
        """
        # Get the target coordinates in Eye space
        worldToEye = np.linalg.inv(eyeToWorld)
        targetEye = TransformPoint(target, worldToEye)

        ### Compute the eye rotation around Y axis (pitch)
        # Project target vector on plane orthogonal to Y:
        targetEyeY[0] = targetEye[0]
        targetEyeY[1] = 0
        targetEyeY[2] = targetEye[2]
        norm = np.linalg.norm(targetEyeY);
        targetEyeY[0] = targetEyeY[0] / norm
        targetEyeY[2] = targetEyeY[2] / norm
        # Get the angle between the X axis and that vector
        angleY = arccos(np.dot((1, 0, 0), targetEyeY))

        # Compute the eye rotation around Z axis (yaw)
        # Project target vector on plane orthogonal to Z:
        targetEyeZ[0] = targetEye[0]
        targetEyeZ[1] = targetEye[1]
        targetEyeZ[2] = 0
        norm = np.linalg.norm(targetEyeZ);
        targetEyeZ[0] = targetEyeZ[0] / norm
        targetEyeZ[2] = targetEyeZ[2] / norm
        # Get the angle between the X axis and that vector
        angleZ = arccos(np.dot((1, 0, 0), targetEyeZ))

        return (angleY, angleZ)

    def addPosition(self, name, angles, speeds):
        # Check angles length
        if not len(angles) == len(self.currentAngles):
            print 'Invalid angles: ', angles
            raise InvalidAnglesParameter
        if not len(speeds) == len(self.currentAngles):
            print 'Invalid speeds: ', speeds
            raise InvalidSpeedsParameter

        # Check for overwrite and print overwritten angles inc ase we want to recover
        if name in self.positions.keys():
            print 'WARNING: Overwrite "', name, '" position (old values: ', self.positions[name], ').'

        # Add a position to the Position.json file
        position = {}
        position['angles'] = angles
        position['speeds'] = speeds
        # print "position = ", position
        self.positions[name] = position
        with open("Positions.json", "w") as write_file:
            json.dump(self.positions, write_file, indent=4, sort_keys=True)

    def loadPositionsFromFile(self, filename):
        try:
            with open(filename, "r") as read_file:
                # print "Loading positions from ", filename, "..."
                filePositions = json.load(read_file)
                # print 'filePositions = ', filePositions.keys()
                n = len(Marionette().motorList)
                updatedPositions = {}
                for name in filePositions.keys():
                    # print "name = ", name
                    pos = filePositions[name]
                    while len(pos['angles']) < n:
                        pos['angles'].append(None)
                    while len(pos['speeds']) < n:
                        pos['speeds'].append(0)
                    # print "pos = ", pos
                    updatedPositions[name] = pos
                # print "updatedPositions = ", updatedPositions
                self.positions.update(updatedPositions)
        except:
            pass


    def updateHeadData(self):
        self.headDataUpdated = False
        self.qMotorCmds.put(((0,self.getMovementCount()), [['requestHeadData']]))
        # Wait until head data is updated (bail if too long)
        counter = 0
        while not self.headDataUpdated:
            pass
            # counter += 1
            # if counter > 10e6:
            #     self.headDataUpdated = True
            #     print "WARNING ----- Head data requested were not updated"


    def saveCalibration(self, name):
        self.updateHeadData()
        self.calibration[name] = [self.roll, self.pitch, self.yawn]

        if name is "up":
            self.pitchMax = self.pitch
        elif name is "down":
            self.pitchMin = self.pitch
        elif name is "left":
            self.yawnMax = self.yawn
        elif name is "right":
            self.yawnMin = self.yawn

        # Write new values in json file
        with open("IMUCameraCalibration.json", "w") as write_file:
            json.dump(self.calibration, write_file, indent=4, sort_keys=True)


if __name__ == '__main__':
    import time, sys
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.Qt import QMutex
    import random

    a = ActionModule(None)
    print "Current angles = ", a.currentAngles
    a.updateAnglesFromFeedback("s,10")
    a.updateAnglesFromFeedback("h,20")
    a.updateAnglesFromFeedback("m,0,-1")
    a.updateAnglesFromFeedback("m,1,1")
    a.updateAnglesFromFeedback("m,2,2")
    a.updateAnglesFromFeedback("m,3,3")
    a.updateAnglesFromFeedback("m,4,4")
    a.updateAnglesFromFeedback("m,5,5")
    #a.updateAnglesFromFeedback("m,6,6") # Right arm disabled
    a.updateAnglesFromFeedback("m,7,7")
    a.updateAnglesFromFeedback("m,8,8")
    a.updateAnglesFromFeedback("m,9,9")
    a.updateAnglesFromFeedback("e,30,40")

    print "updateAnglesFromFeedback tests done"

    class MotionGenerator(QtCore.QObject):

        newPos  = QtCore.pyqtSignal(int)

        def __init__(self, parent=None, delay=50):
            QtCore.QObject.__init__(self)
            self.parent = parent
            self.delay  = delay
            self.mutex  = QMutex()
            self.run    = True
            self.actionModule = ActionModule(None)

        def generateMotion(self):
            print "started"
            while self.run:
                actionKey = random.choice(self.actionModule.positions.keys())
                speed = random.choice([10, 20, 50, 80])
                speeds = []
                for a in self.actionModule.currentAngles:
                    speeds.append(speed)
                print "move to ", actionKey
                seq = self.actionModule.moveTo(actionKey)
                self.newPos.emit(len(seq))
                QtCore.QThread.msleep(self.delay)

    class MainWin(QtWidgets.QMainWindow):

        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)
            self.marionette = Marionette()

            self.thread1 = QtCore.QThread()
            self.motionGen = MotionGenerator(self, 1000)
            self.motionGen.moveToThread(self.thread1)
            self.motionGen.newPos.connect(self.updateVisual)
            self.thread1.started.connect(self.motionGen.generateMotion)
            self.thread1.start()

        def updateVisual(self, n):
            for i in range(n):
                if not self.motionGen.actionModule.qMotorCmds.empty():
                    cmds = self.motionGen.actionModule.qMotorCmds.get()
                    previousAngles = self.marionette.getAngles()
                    angles = []

                    for previousAngle, motor in zip(previousAngles, self.marionette.motorList):
                        angle = previousAngle
                        for cmd in cmds:
                            if cmd[0] == motor.name:
                                angle = int(cmd[1])
                        angles.append(angle)

                    self.marionette.setAngles(angles)


    app = QtWidgets.QApplication(sys.argv)
    main = MainWin()
    main.show()
    sys.exit(app.exec_())
