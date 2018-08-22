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

import ArduinoCommunicator

from Action import *
from Marionette import *
from UIUtils import MarionetteWidget

class ActionModule(object):

    def __init__(self, config):
        """ port = usb port of the arduino controling the motors
            set to "" on a computer without arduino
        """
        # TODO: Get full list of motions from
        # https://docs.google.com/spreadsheets/d/1XPwe3iQbNzOgRDWYDuqAxW8JrQiBvvqikn3oN0fImSs/edit#gid=0
        self.angles = {}
        self.angles['rest'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.angles['rightHandFullRaise'] = [None, -122, None, -1035, None, None, None, None, None, None, -1920, None]
        self.angles['leftHandFullRaise'] = [None, None, -20, None, -841, None, None, None, None, None, None, -1717]
        self.angles['bothHandFullRaise'] = [None, -122, -80, -1035, -990, None, None, None, None, None, -1920, -1920]

        self.speed = {}
        self.speed['slow'] = 40
        self.speed['fast'] = 20
        self.speed['jump'] = 1

        # Initialize the angles to the marionette's default (0 everywhere)
        self.currentAngles = Marionette().getAngles()

        # Flag True if successfully connected to the arduino
        self.connectedToArduino = False

        # Thread related variables
        self.qMotorAngles = Queue.Queue()
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
        self.ac = ArduinoCommunicator.ArduinoCommunicator("/dev/cu.usbmodem1411")
        self.ac_head = ArduinoCommunicator.ArduinoCommunicator("")

        if self.ac.serial_port is not None:
            # Watch out:
            # Not really thread safe but only writen here and read later in Simulator
            self.connectedToArduino = True

        while(self.running):
            if not self.qMotorAngles.empty():
                angles = self.qMotorAngles.get()
                # Translate the angles for the arduino commands
                # angles order : [S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL]
                self.ac.motor_cmd_dict['Right shoulder'] = angles[1]
                self.ac.motor_cmd_dict['Left shoulder'] = angles[2]
                self.ac.motor_cmd_dict['Right arm'] = angles[3]
                self.ac.motor_cmd_dict['Left arm'] = angles[4]
                self.ac.motor_cmd_dict['Right head'] = angles[6]
                self.ac.motor_cmd_dict['Left head'] = angles[7]
                self.ac.motor_cmd_dict['Right foot'] = angles[8]
                self.ac.motor_cmd_dict['Left foot'] = angles[9]
                self.ac.motor_cmd_dict['Right hand'] = angles[10]
                self.ac.motor_cmd_dict['Left hand'] = angles[11]
                self.ac.move()
                speed = 1
                self.ac.rotateHead(angles[5], speed)
                self.ac.rotateShoulder(angles[0], speed)
        print "Arduino thread stopped"
        self.ac.stopAllSteppers()

    def moveToAngles(self, target, speed):
        action = Action(target)
        sequence = action.getAngleSequenceToTarget(self.currentAngles, speed)
        self.currentAngles = sequence[-1]
        for a in sequence:
            self.qMotorAngles.put(a)
        return sequence

    def moveTo(self, targetKey, speedKey):
        if targetKey not in self.angles.keys():
            raise InvalidTargetKeyError
        if speedKey not in self.speed.keys():
            raise InvalidSpeedKeyError

        print "move to ", targetKey, " ", speedKey

        target = self.angles[targetKey]
        speed = self.speed[speedKey]
        return self.moveToAngles(target, speed)

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
                speedKey = random.choice(self.actionModule.speed.keys())
                print "move ", actionKey, " ", speedKey
                seq = self.actionModule.moveTo(actionKey, speedKey)
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
                if not self.motionGen.actionModule.qMotorAngles.empty():
                    angles = self.motionGen.actionModule.qMotorAngles.get()
                    self.win2.marionette.setAngles(angles)
                    self.win2.marionette.computeNodesPosition()
                    self.win2.updateGL()


    app = QtWidgets.QApplication(sys.argv)
    main = MainWin()
    main.show()
    sys.exit(app.exec_())
