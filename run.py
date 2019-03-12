import time

import cv2

from SensorModule import SensorModule
from EmotionModule import EmotionModule
from ResponseModule import ResponseModule
from ActionModule import ActionModule

import ArduinoCommunicator

import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os

import logging

# video
#VIDEO_FEED = os.path.expanduser('~/Desktop/ishaanMovies/people gesturing-converted.mp4')
#VIDEO_FEED = os.path.expanduser('~/Desktop/ishaanMovies/morePeople-converted.mp4')
# camera
VIDEO_FEED = 0

TEST_WIHOUT_RASP = False

class AppRun(QWidget):

    def __init__(self, realRun=None):
        super(AppRun, self).__init__()
        self.setWindowTitle('Cat\'s Cradle')
        self.move(0, 0)
        self.realRun = realRun

        self.loadingDialog = None

        closeBtn = QPushButton('Stop CatsCradle')
        closeBtn.clicked.connect(self.initShutdown)
        layout = QGridLayout(self)
        layout.addWidget(closeBtn, 1, 1)

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

        setupDialog.setInformativeText("Power on Raspberry Pi, \nwait 1 minute\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        if not TEST_WIHOUT_RASP:
            # Wait for 60
            delay = 60
            if "--testUI" in sys.argv:
                delay = 5
            progress = QProgressDialog("Starting Raspberry Pi...", None, 0, delay)
            progress.setWindowModality(Qt.WindowModal)

            for i in range(0, delay):
                progress.setValue(i)
                if (progress.wasCanceled()):
                    return False
                time.sleep(1)

            progress.setValue(delay);

            # Try port connection and warn user if failed
            self.ac = ArduinoCommunicator.ArduinoCommunicator("/dev/ttyUSB0")
            if self.ac.serial_port is None:
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

        setupDialog.setInformativeText("If necessary, plug main camera into battery\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 2

        setupDialog.setInformativeText("Power on motors and rear camera\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 3

        return True


    def initShutdown(self):
        if self.realRun:
            self.realRun.stop()


    def shutdown(self):
        # Raise message boxes to make sure the user properly shuts down the marionette
        shutdownDialog = QMessageBox()
        shutdownDialog.setText("Cat's Cradle Shutdown")
        shutdownDialog.setStandardButtons(QMessageBox.Ok)
        shutdownDialog.setDefaultButton(QMessageBox.Ok)

        if self.setupStep > 2:
            shutdownDialog.setInformativeText("Turn Off Motors\n")
            shutdownDialog.exec_()

        if self.setupStep > 0:
            shutdownDialog.setInformativeText("Turn Off Rasberry Pi\n")
            shutdownDialog.exec_()


class RunCatsCradle(object):
    def __init__(self, returnToZero=True, app=None):
        self.app = app
        self.returnToZero = returnToZero
        self.running = False

    def run(self):
        self.running = True

        logging.basicConfig(filename='interactions.log', level=logging.INFO)
        logging.info(str(time.time()) + ' started.')

        cameraMaxX = 1920
        cameraMaxY = 1080

        actionModule = ActionModule(cameraMaxX, cameraMaxY, dummy="--dummyAction" in sys.argv)

        print('Loaded Action Module...\n')

        response_module = ResponseModule(actionModule)

        print('Loaded Response Module...\n')

        emotion_module = EmotionModule(response_module, visualise=True)

        print('Loaded Emotion Module...\n')

        sensor_module = SensorModule(emotion_module)
        sensor_module.loadReactors()

        print('Loaded Sensor Module...\n')

        # loading the camera should happen after sensor module is initialized but before loading camera for the sensor module
        camera = cv2.VideoCapture(VIDEO_FEED)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, cameraMaxX)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, cameraMaxY)
        sensor_module.loadSensors(camera)

        while self.running:

            sensor_module.update()

            if self.app is not None:
                # Process the app events to catch a click on Shutdown button
                self.app.processEvents()
            else:
                # Hit 'q' on the keyboard to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                   self.running = False


        print("stopping...")
        sensor_module.cleanup()
        camera.release()
        cv2.destroyAllWindows()

        # Clear the current queue
        actionModule.clearQueue()

        if self.returnToZero:
            # Go to resting pose
            actionModule.goBackToZero()

        actionModule.stop()
        logging.info(str(time.time()) + ' ended.')

    def stop(self):
        self.running = False


if __name__ == "__main__":
    noSetup = False
    noShutdown = False
    returnToZero = True
    if "--noUI" in sys.argv:
        noSetup = True
        noShutdown = True
        returnToZero = False

    app = QApplication(sys.argv)

    run = RunCatsCradle(returnToZero, app)
    appWidget = AppRun(run)
    if "--dummyAction" in sys.argv or noSetup or appWidget.setup():
        appWidget.show()
        app.processEvents()
        run.run()

    if not noShutdown:
        appWidget.shutdown()
