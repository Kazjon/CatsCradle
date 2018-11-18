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

import ArduinoCommunicator
import time

from Action import *
from Marionette import *

class ActionModule(object):

    def __init__(self, config):
        """ port = usb port of the arduino controling the motors
            set to "" on a computer without arduino
        """
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

        # Arduino motor id
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

        # Thread related variables
        self.qMotorCmds = Queue.Queue()
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
            self.arduino_thread = threading.Thread(name='Arduino', target=self.threadFunc)
            self.arduino_thread.setDaemon(True)
            self.arduino_thread.start()


    def threadFunc(self):
        self.ac = ArduinoCommunicator.ArduinoCommunicator("/dev/ttyACM0")
        self.ac_head = ArduinoCommunicator.ArduinoCommunicator("/dev/ttyACM1")

        while(self.running):
            if not self.qMotorCmds.empty():
                cmds = self.qMotorCmds.get()
                eyeMotion = False
                eyeAngleX = 90 # The eye angles needs an int. If it should be None,
                eyeAngleY = 90 # speed will be 0 and no motion will be triggered
                eyeSpeedX = 0
                eyeSpeedY = 0
                for cmd in cmds:
                    # print "step = ", step
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
                    self.ac_head.rotateEyes(eyeAngleX, eyeAngleY, eyeSpeedX, eyeSpeedY)

        print "Arduino thread stopped"


    def moveToAngles(self, target, speeds):
        action = Action(target, self.timeInterval)
        output = action.getCmdsToTarget(self.currentAngles, speeds)
        newAngles = []
        for oldAngle, newAngle in zip(self.currentAngles, target):
            if newAngle is None:
                newAngles.append(oldAngle)
            else:
                newAngles.append(newAngle)
        # print "self.currentAngles = ", self.currentAngles
        # print "target = ", target
        # print "newAngles = ", newAngles
        self.currentAngles = newAngles
        self.qMotorCmds.put(output)
        return self.currentAngles


    def moveTo(self, targetKey):
        if targetKey not in self.positions.keys():
            raise InvalidTargetKeyError

        position = self.positions[targetKey]
        return self.moveToAngles(position['angles'], position['speeds'])


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


if __name__ == '__main__':
    import time, sys
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.Qt import QMutex
    import random

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
