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

from Action import *
from Marionette import *
from UIUtils import MarionetteWidget

class ActionModule(object):

    def __init__(self, config):
        # TODO: Get full list of motions from
        # https://docs.google.com/spreadsheets/d/1XPwe3iQbNzOgRDWYDuqAxW8JrQiBvvqikn3oN0fImSs/edit#gid=0
        self.angles = {}
        self.angles['rest'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.angles['rightHandFullRaise'] = [None, -980, None, -2298, None, None, None, None, None, None, -1919, None]
        self.angles['leftHandFullRaise'] = [None, None, -980, None, -2298, None, None, None, None, None, None, -1919]
        self.angles['bothHandFullRaise'] = [None, -980, -980, -2298, -2298, None, None, None, None, None, -1919, -1919]

        self.speed = {}
        self.speed['slow'] = 40
        self.speed['fast'] = 20
        self.speed['jump'] = 1

        # Initialize the angles to the marionette's default (0 everywhere)
        self.currentAngles = Marionette().getAngles()

        # Thread related variables
        self.q = Queue.Queue()

    def moveTo(self, targetKey, speedKey):
        if targetKey not in self.angles.keys():
            raise InvalidTargetKeyError
        if speedKey not in self.speed.keys():
            raise InvalidSpeedKeyError

        print "move to ", targetKey, " ", speedKey

        target = self.angles[targetKey]
        speed = self.speed[speedKey]
        action = Action(target)
        sequence = action.getAngleSequenceToTarget(self.currentAngles, speed)
        self.currentAngles = sequence[-1]
        for a in sequence:
            self.q.put(a)
        return sequence


if __name__ == '__main__':
    import time, sys
    from PyQt5 import QtGui, QtCore, QtWidgets
    from PyQt5.Qt import QMutex
    import random

    class MotionGenerator(QtCore.QObject):

        newPos  = QtCore.pyqtSignal(int)

        def __init__(self, parent=None, delay=5):
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
                if not self.motionGen.actionModule.q.empty():
                    angles = self.motionGen.actionModule.q.get()
                    self.win2.marionette.setAngles(angles)
                    self.win2.marionette.computeNodesPosition()
                    self.win2.updateGL()


    app = QtWidgets.QApplication(sys.argv)
    main = MainWin()
    main.show()
    sys.exit(app.exec_())
