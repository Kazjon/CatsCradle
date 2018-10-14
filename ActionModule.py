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

import ArduinoCommunicator
import time

from Action import *
from Marionette import *
from UIUtils import MarionetteWidget

class ActionModule(object):

    def __init__(self, config):
        """ port = usb port of the arduino controling the motors
            set to "" on a computer without arduino
        """
        # Read the positions from the Positions.json file
        with open("Positions.json", "r") as read_file:
            self.angles = json.load(read_file)

        self.timeInterval = 0.25 # (1/4 second)

        # Initialize the angles to the marionette's default (0 everywhere)
        self.currentAngles = Marionette().getAngles()

        # Flag True if successfully connected to the arduino
        self.connectedToArduino = False

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

        # Thread related variables
        self.qMotorSteps = Queue.Queue()
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
        # Good speed values for head and shoulder rotation (Jim)
        headSpeed = 10
        shoulderSpeed = 0
        if self.ac.serial_port is not None:
            # Watch out:
            # Not really thread safe but only written here and read later in Simulator
            self.connectedToArduino = True

        while(self.running):
            if not self.qMotorSteps.empty():
                steps = self.qMotorSteps.get()
                for step in steps:
                    # print "step = ", step
                    id = self.arduinoID[step[0]]
                    angle = int(step[1])
                    speed = int(step[2])
                    if id == -1:
                        # Obsolete motor AR
                        continue
                    if id == 'head':
                        self.ac.rotateHead(angle, speed)
                    elif id == 'shoulder':
                        self.ac.rotateShoulder(angle, speed)
                    else:
                        self.ac.rotateStringMotor(id, angle, speed)
        print "Arduino thread stopped"

    def moveToAngles(self, target, rotationSpeed):
        action = Action(target, self.timeInterval)
        output = action.getSpeedToTarget(self.currentAngles, rotationSpeed)
        self.currentAngles = target
        self.qMotorSteps.put(output)
        return self.currentAngles

    def moveTo(self, targetKey, rotationSpeed):
        if targetKey not in self.angles.keys():
            raise InvalidTargetKeyError

        print "move to ", targetKey, " at speed  ", rotationSpeed

        target = self.angles[targetKey]
        return self.moveToAngles(target, rotationSpeed)

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

    def addPosition(self, name, angles):
        # Check angles length
        if not len(angles) == len(self.currentAngles):
            print 'Invalid angles: ', angles
            raise InvalidAnglesParameter

        # Check for overwrite and print overwritten angles inc ase we want to recover
        if name in self.angles.keys():
            print 'WARNING: Overwrite "', name, '" angles (old values: ', self.angles[name], ').'

        # Add a position to the Position.json file
        self.angles[name] = angles
        with open("Positions.json", "w") as write_file:
            json.dump(self.angles, write_file, indent=4, sort_keys=True)


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
                actionKey = random.choice(self.actionModule.angles.keys())
                speed = random.choice([10, 20, 50, 80])
                print "move ", actionKey, " at speed ", speed
                seq = self.actionModule.moveTo(actionKey, speed)
                self.newPos.emit(len(seq))
                QtCore.QThread.msleep(self.delay)

    class MainWin(QtWidgets.QMainWindow):

        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)
            self.win2 = MarionetteWidget(Marionette())
            self.setCentralWidget(self.win2)

            self.thread1 = QtCore.QThread()
            self.motionGen = MotionGenerator(self, 1000)
            self.motionGen.moveToThread(self.thread1)
            self.motionGen.newPos.connect(self.updateVisual)
            self.thread1.started.connect(self.motionGen.generateMotion)
            self.thread1.start()

        def updateVisual(self, n):
            for i in range(n):
                if not self.motionGen.actionModule.qMotorSteps.empty():
                    steps = self.motionGen.actionModule.qMotorSteps.get()
                    previousAngles = self.win2.marionette.getAngles()
                    angles = []

                    for previousAngle, motor in zip(previousAngles, self.win2.marionette.motorList):
                        angle = previousAngle
                        for step in steps:
                            if step[0] == motor.name:
                                angle = int(step[1])
                        angles.append(angle)

                    self.win2.marionette.setAngles(angles)
                    self.win2.marionette.computeNodesPosition()
                    self.win2.updateGL()


    app = QtWidgets.QApplication(sys.argv)
    main = MainWin()
    main.show()
    sys.exit(app.exec_())
