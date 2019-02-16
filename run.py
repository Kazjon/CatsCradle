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

_running = False

import os

# video
#VIDEO_FEED = os.path.expanduser('~/Desktop/ishaanMovies/morePeople-converted.mp4')
# camera
VIDEO_FEED = 0

TEST_WIHOUT_RASP = True

class App(QWidget):

    def __init__(self):
        super(App, self).__init__()
        self.setWindowTitle('Cat\'s Cradle')
        self.move(0, 0)

        self.loadingDialog = None

        label = QLabel()
        pixmap = QPixmap()
        pixmap.load('./icon_headshot')
        pixmap = pixmap.scaledToHeight(600)
        label.setPixmap(pixmap)
        closeBtn = QPushButton('Shutdown')
        closeBtn.clicked.connect(self.initShutdown)
        layout = QGridLayout(self)
        layout.addWidget(label, 1, 1)
        layout.addWidget(closeBtn, 2, 1)

        self.setupStep = 0

    def setup(self):
        # Raise message boxes to make sure the user properly sets the marionette
        # before running the AI
        setupDialog = QMessageBox()
        setupDialog.setText("Cat's Cradle Setup")
        setupDialog.setInformativeText("Make sure all strings are at their lowest point\n")
        setupDialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        setupDialog.setDefaultButton(QMessageBox.Ok)
        ret = setupDialog.exec_()
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 1

        setupDialog.setInformativeText("Power On Rasberry Pi\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        if not TEST_WIHOUT_RASP:
            # Wait for 45s
            delay = 45
            if "--testUI" in sys.argv:
                delay = 5
            progress = QProgressDialog("Starting Rasberry Pi...", None, 0, delay)
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
                errorDialog.setInformativeText("Port not found.\nMake sure the Rasberry Pi is connected to the right port\n")
                errorDialog.setStandardButtons(QMessageBox.Ok)
                errorDialog.setDefaultButton(QMessageBox.Ok)
                errorDialog.exec_()
                if not "--testUI" in sys.argv:
                    return False

        self.setupStep = 2

        setupDialog.setInformativeText("Power On Motors\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 3

        return True


    def initShutdown(self):
        global _running
        _running = False


    def shutdown(self):
        # Raise message boxes to make sure the user properly shuts down the marionette
        shutdownDialog = QMessageBox()
        shutdownDialog.setText("Cat's Cradle Shutdown")
        shutdownDialog.setStandardButtons(QMessageBox.Ok)
        shutdownDialog.setDefaultButton(QMessageBox.Ok)

        if self.setupStep > 2:
            shutdownDialog.setInformativeText("Power Off Motors\n")
            shutdownDialog.exec_()

        if self.setupStep > 1:
            shutdownDialog.setInformativeText("Power Off Rasberry Pi\n")
            shutdownDialog.exec_()


def run(app, appWidget):
    global _running
    _running = True

    actionModule = ActionModule(dummy="--dummyAction" in sys.argv)

    print('Loaded Action Module...\n')

    response_module = ResponseModule(actionModule)

    print('Loaded Response Module...\n')

    emotion_module = EmotionModule(response_module, visualise=False)

    print('Loaded Emotion Module...\n')

    sensor_module = SensorModule(emotion_module)
    sensor_module.loadReactors()

    print('Loaded Sensor Module...\n')

    # loading the camera should happen after sensor module is initialized but before loading camera for the sensor module
    camera = cv2.VideoCapture(VIDEO_FEED)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    sensor_module.loadSensors(camera)

    while _running:

        sensor_module.update()

        # Hit 'q' on the keyboard to quit
        #if cv2.waitKey(1) & 0xFF == ord('q'):
        #    _running = False

        # Process the app events to catch a click on Shutdown button
        app.processEvents()

    print("stopping...")
    sensor_module.cleanup()
    camera.release()
    cv2.destroyAllWindows()

    # Clear the current queue
    actionModule.clearQueue()
    # Define rest angles for the 12 motors (0)
    restAngles = [0] * 12
    # Add angles for the eyes (90)
    restAngles.extend([90, 90])
    # Define speed for each motor (25)
    speeds = [25] * 14
    actionModule.moveToAngles(restAngles, speeds)

    # Waiting for the move to complete
    while not actionModule.isMarionetteIdle():
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    appWidget = App()
    if "--dummyAction" in sys.argv or appWidget.setup():
        appWidget.show()
        app.processEvents()
        run(app, appWidget)

    appWidget.shutdown()

    exit()
