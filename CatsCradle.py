import time
import subprocess

import cv2

from ActionModule import ActionModule
from Marionette import *

from SimulatorUI import *

import ArduinoCommunicator

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class MainApp(QWidget):

    def __init__(self, app):
        super(MainApp, self).__init__()
        self.setWindowTitle('Cat\'s Cradle')
        self.move(0, 0)
        self.app = app

        self.appBtn = QPushButton('Start CatsCradle')
        self.appBtn.clicked.connect(self.startCatsCradle)
        self.simBtn = QPushButton('Start Simulator')
        self.simBtn.clicked.connect(self.simulator)
        self.closeBtn = QPushButton('Shutdown')
        self.closeBtn.clicked.connect(self.initShutdown)

        layout = QGridLayout(self)
        layout.addWidget(self.appBtn, 1, 1)
        layout.addWidget(self.simBtn, 1, 2)
        layout.addWidget(self.closeBtn, 1, 3)

        self.setupStep = 0

    def closeEvent(self, event):
        self.initShutdown()
        event.accept() # let the window close

    def setup(self):
        # Raise message boxes to make sure the user properly sets the marionette
        # before running the AI
        setupDialog = QMessageBox()
        setupDialog.setText("Cat's Cradle Setup")
        setupDialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        setupDialog.setDefaultButton(QMessageBox.Ok)

        setupDialog.setInformativeText("Please make sure the main camera is powered on.\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        setupDialog.setInformativeText("Power on Raspberry Pi. Click Ok and wait 1 minute.\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        # Try port connection and warn user if failed
        ac = ArduinoCommunicator.ArduinoCommunicator("/dev/ttyUSB0")
        if ac.serial_port is None:
            errorDialog = QMessageBox()
            errorDialog.setText("ERROR")
            errorDialog.setIcon(QMessageBox.Critical)
            errorDialog.setInformativeText("Port not found.\nMake sure the Raspberry Pi is connected to the right port\n")
            errorDialog.setStandardButtons(QMessageBox.Ok)
            errorDialog.setDefaultButton(QMessageBox.Ok)
            errorDialog.exec_()
            if not "--testUI" in sys.argv:
                return False

        self.setupStep = 1

        
        # Wait for 60
        delay = 60
        if "--testUI" in sys.argv:
            delay = 1
        progress = QProgressDialog("Starting Raspberry Pi...", None, 0, delay)
        progress.setWindowModality(Qt.WindowModal)

        for i in range(0, delay):
            progress.setValue(i)
            if (progress.wasCanceled()):
                return False
            time.sleep(1)

        progress.setValue(delay);


        self.setupStep = 2

        setupDialog.setInformativeText("Power on motors and rear camera. Then plug in the rear camera.\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 3

        return True


    def startCatsCradle(self):
        # Disable buttons
        self.simBtn.setEnabled(False)
        self.appBtn.setEnabled(False)
        self.closeBtn.setEnabled(False)

        # Force an immediate redraw of the buttons
        self.simBtn.repaint()
        self.appBtn.repaint()
        self.closeBtn.repaint()
        self.app.processEvents()

        subprocess.call("RunCatsCradle")

        self.resetMotors()

        # Enable buttons
        self.simBtn.setEnabled(True)
        self.appBtn.setEnabled(True)
        self.closeBtn.setEnabled(True)


    def simulator(self):
        # Disable buttons
        self.simBtn.setEnabled(False)
        self.appBtn.setEnabled(False)
        self.closeBtn.setEnabled(False)

        subprocess.call("RunSimulator")

        self.resetMotors()

        # Enable buttons
        self.simBtn.setEnabled(True)
        self.appBtn.setEnabled(True)
        self.closeBtn.setEnabled(True)

    def initShutdown(self):
        global _running
        _running = False

        # Disable buttons
        self.simBtn.setEnabled(False)
        self.appBtn.setEnabled(False)
        self.closeBtn.setEnabled(False)


    def resetMotors(self):
        # Return the marionette to resting position
        actionModule = ActionModule(10, 10, dummy=False)
        # Makes sure the current angles are not equal to the target (resting pause)
        minAngles = []
        marionette = Marionette()
        for m in marionette.motorList:
            minAngles.append(m.minAngle)
        actionModule.currentAngles = minAngles

        # Go back to resting position
        actionModule.isIdle = False
        actionModule.goBackToZero()

        # Waiting for the move to complete
        label = QLabel()
        label.setMinimumSize(400, 100)
        label.setText("Waiting for motors to get to resting position...")
        label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        label.show()

        i = 0
        while not actionModule.isMarionetteIdle():
            self.app.processEvents()
            if "--testUI" in sys.argv:
                i = i + 1
                if i > 5000:
                    actionModule.currentAngles = actionModule.currentTargetAngles

        actionModule.stop()

        label.hide()

    def shutdown(self):
        # Raise message boxes to make sure the user properly shuts down the marionette
        shutdownDialog = QMessageBox()
        shutdownDialog.setText("Cat's Cradle Shutdown")
        shutdownDialog.setStandardButtons(QMessageBox.Ok)
        shutdownDialog.setDefaultButton(QMessageBox.Ok)

        if self.setupStep > 2:
            shutdownDialog.setInformativeText("Power down motors and rear camera. Unplug rear camera USB.\n")
            shutdownDialog.exec_()

        if self.setupStep > 0:
            shutdownDialog.setInformativeText("Power down Rasberry Pi and main camera.\n")
            shutdownDialog.exec_()


if __name__ == "__main__":
    global _running
    _running = True

    app = QApplication(sys.argv)
    mainAppWidget = MainApp(app)
    if mainAppWidget.setup():
        mainAppWidget.show()
        while _running:
            app.processEvents()

    mainAppWidget.shutdown()
