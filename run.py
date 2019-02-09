import time
from threading import Thread

import ArduinoCommunicator

from SensorModule import SensorModule
from EmotionModule import EmotionModule
from ResponseModule import ResponseModule
from ActionModule import ActionModule

from PersonSensor import PersonSensor
from Audience import Audience

import tensorflow as tf

import cv2

import sys

from multiprocessing import Process

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

_running = False

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
        closeBtn.clicked.connect(self.shutdown)
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


    def shutdown(self):
        _running = False

        # Raise message boxes to make sure the user properly shuts down the marionette
        shutdownDialog = QMessageBox()
        shutdownDialog.setText("Cat's Cradle Shutdown")
        shutdownDialog.setStandardButtons(QMessageBox.Ok)
        shutdownDialog.setDefaultButton(QMessageBox.Ok)

        if self.setupStep > 2:
            shutdownDialog.setInformativeText("Return all Motors to zero\n")
            shutdownDialog.exec_()

            shutdownDialog.setInformativeText("Power Off Motors\n")
            shutdownDialog.exec_()

        if self.setupStep > 1:
            shutdownDialog.setInformativeText("Power Off Rasberry Pi\n")
            shutdownDialog.exec_()

        exit()


    def loadingPersonDetector(self, value):
        if value is None:
            self.loadingDialog.cancel()
        else:
            # Raise message boxes to make sure the user knows something is loading
            if self.loadingDialog is None:
                self.loadingDialog = QProgressDialog("Loading Person Detector...", None, 0, 100)
                self.loadingDialog.setWindowModality(Qt.WindowModal)

            self.loadingDialog.show()
            self.loadingDialog.setValue(value % 100)


def run(app, appWidget):
    _running = True

    actionModule = ActionModule(dummy="--dummyAction" in sys.argv)
    config = tf.ConfigProto(allow_soft_placement=True)

    print('Loaded Action Module...\n')

    with tf.Session(config=config) as tf_sess:
        response_module = ResponseModule(actionModule)

        print('Loaded Response Module...\n')

        emotion_module = EmotionModule(response_module, visualise=True)

        print('Loaded Emotion Module...\n')


        perceptionMode = "full"
        if "--dummyPerception" in sys.argv:
            perceptionMode = "dummy"
        elif "--fastPerception" in sys.argv:
            perceptionMode = "fast"

        sensor_module = SensorModule({"cv_path": '.', "tf_sess": tf_sess, "perception_mode": perceptionMode}, emotion_module)
        sensor_module.loadSensors(cv2.VideoCapture(0), tf_sess)
        sensor_module.loadReactors()

        print('Loaded Sensor Module...\n')

        person_detector_thread = Thread(target=sensor_module.personSensor.detectUndetectedPersons)
        person_detector_thread.setDaemon(True)
        person_detector_thread.start()
#        person_detector_process = Process(target=sensor_module.personSensor.detectUndetectedPersons)
#        person_detector_process.start()


        appWidget.loadingPersonDetector(0)
        counter = 0
        while not sensor_module.personSensor.initialised:
            counter += 1
            appWidget.loadingPersonDetector(counter / 10)
            if "--testUI" in sys.argv and counter > 3000:
                break
            # Process the app events to avoid a freeze of the UI
            app.processEvents()
            continue
        appWidget.loadingPersonDetector(None)
        print('Loaded Person Detector...\n')


        while _running:

            sensor_module.update()

            # Hit 'q' on the keyboard to quit
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     _running = False

            # Process the app events to catch a click on Shutdown button
            app.processEvents()

        print("stopping...")
#                person_detector_process.terminate()
        sensor_module.cleanup()
        cv2.destroyAllWindows()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    appWidget = App()
    if "--dummyAction" in sys.argv or appWidget.setup():
        appWidget.show()
        app.processEvents()
        run(app, appWidget)

    appWidget.shutdown()

    sys.exit(app.exec_())
