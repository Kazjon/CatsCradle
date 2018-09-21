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

        # duration of the move in s
        self.speed = {}
        self.speed['slow'] = 5
        self.speed['fast'] = 2
        self.speed['jump'] = 1

        # Initialize the angles to the marionette's default (0 everywhere)
        self.currentAngles = Marionette().getAngles()

        # Flag True if successfully connected to the arduino
        self.connectedToArduino = False

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
        self.ac_head = ArduinoCommunicator.ArduinoCommunicator("")

        # Good speed values for head and shoulder rotation (Jim)
        headSpeed = 10
        shoulderSpeed = 25

        if self.ac.serial_port is not None:
            # Watch out:
            # Not really thread safe but only written here and read later in Simulator
            self.connectedToArduino = True

        while(self.running):
            if not self.qMotorSteps.empty():
                step = self.qMotorSteps.get()
                #print "step = ", step
                duration = step[0]
                speed = step[1]
                # Translate the angles for the arduino commands
                # angles order : [S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL]
                self.ac.motor_cmd_dict['Right shoulder'] = int(speed[1])
                self.ac.motor_cmd_dict['Left shoulder'] = int(speed[2])
                # No motor on right arm
                #self.ac.motor_cmd_dict['Right arm'] = int(speed[3])
                self.ac.motor_cmd_dict['Left arm'] = int(speed[4])
                self.ac.motor_cmd_dict['Right head'] = int(speed[6])
                self.ac.motor_cmd_dict['Left head'] = int(speed[7])
                self.ac.motor_cmd_dict['Right foot'] = int(speed[8])
                self.ac.motor_cmd_dict['Left foot'] = int(speed[9])
                self.ac.motor_cmd_dict['Right hand'] = int(speed[10])
                self.ac.motor_cmd_dict['Left hand'] = int(speed[11])
                # For head and shoulder speed = function(angle)
                self.ac.rotateHead(int(speed[5]), headSpeed)
                self.ac.rotateShoulder(int(speed[0]), shoulderSpeed)
                self.ac.move()
                time.sleep(duration)
                self.ac.stopAllSteppers()
        print "Arduino thread stopped"

    def moveToAngles(self, target, duration):
        action = Action(target, self.timeInterval)
        sequence = action.getSpeedToTarget(self.currentAngles, duration)
        self.currentAngles = action.lastTargetAngles
        for a in sequence:
            #print "a = ", a
            self.qMotorSteps.put(a)
        return self.currentAngles

    def moveTo(self, targetKey, duration):
        if targetKey not in self.angles.keys():
            raise InvalidTargetKeyError

        print "move to ", targetKey, " during ", duration, " sec"

        target = self.angles[targetKey]
        return self.moveToAngles(target, duration)

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
                duration = random.choice([1, 2, 5])
                print "move ", actionKey, " during ", duration, " sec"
                seq = self.actionModule.moveTo(actionKey, duration)
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
                    step = self.motionGen.actionModule.qMotorSteps.get()
                    duration = step[0]
                    speeds = step[1]
                    angles = []
                    previousAngles = self.win2.marionette.getAngles()
                    for speed, previousAngle, motor in zip(speeds, previousAngles, self.win2.marionette.motorList):
                        if motor.isStatic:
                            angles.append(previousAngle + motor.angleFromMotorIncrement(speed))
                        else:
                            angles.append(speed)
                    self.win2.marionette.setAngles(angles)
                    self.win2.marionette.computeNodesPosition()
                    self.win2.updateGL()


    app = QtWidgets.QApplication(sys.argv)
    main = MainWin()
    main.show()
    sys.exit(app.exec_())
