import time
from threading import Thread

TESTING_UI = False
#TESTING_UI = True

import ArduinoCommunicator

if not TESTING_UI:
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

class App(QWidget):

    def __init__(self):
        super(App, self).__init__()
        self.title = 'Cat\'s Cradle'
        self.left = 10
        self.top = 10
        self.width = 1200
        self.height = 680

        label = QLabel()
        pixmap = QPixmap()
        pixmap.load('./icon_headshot')
        pixmap = pixmap.scaledToHeight(600)
        label.setPixmap(pixmap)
        closeBtn = QPushButton('Shutdown')
        closeBtn.clicked.connect(self.shutdown)
        closeBtn.setEnabled(True)
        layout = QGridLayout(self)
        layout.addWidget(label, 1, 1)
        layout.addWidget(closeBtn, 2, 1)

        closeBtn.setEnabled(False)

        self.running = False
        self.app_thread = None

        self.setupStep = 0

        if "--dummyAction" in sys.argv or self.setup():
            closeBtn.setEnabled(True)
            self.showNormal()

            self.running = True
            self.app_thread = Thread(name='CatsCradle', target=self.run, args=())
            self.app_thread.setDaemon(True)
            self.app_thread.start()
        else:
            self.shutdown()


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
        if TESTING_UI:
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
            return False

        self.setupStep = 2

        setupDialog.setInformativeText("Power On Motors\n");
        ret = setupDialog.exec_();
        if ret == QMessageBox.Close:
            return False

        self.setupStep = 3

        return True


    def shutdown(self):
        self.running = False
        if self.app_thread:
            self.app_thread.join()

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

    def run(self):
        if TESTING_UI:
            while self.running:
                print "running"
            return

        actionModule = ActionModule(dummy="--dummyAction" in sys.argv)
        print('Loaded Action Module...\n')

        config = tf.ConfigProto(allow_soft_placement=True)
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

            while not sensor_module.personSensor.initialised:
                continue
            print('Loaded Person Detector...\n')

            while self.running:

                sensor_module.update()

                # Hit 'q' on the keyboard to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False

            print("stopping...")
#                person_detector_process.terminate()
            sensor_module.cleanup()
            cv2.destroyAllWindows()

        self.shutdown()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
