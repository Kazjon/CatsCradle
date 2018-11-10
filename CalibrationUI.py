import sys
import threading
import time
import queue
import cv2

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from PyQt5.QtGui import QIcon, QPainter, QImage
from PyQt5.QtCore import QTimer, QPoint

from Calibration import *
from UIUtils import *

class App(QWidget):

    def __init__(self):
        super(App, self).__init__()
        self.title = 'Cat\'s Craddle - Calibration window'
        self.left = 10
        self.top = 10
        self.width = 680
        self.height = 480
        self.video_width = 680
        self.video_height = 280

        # Video frames
        self.videoWindow = ImageWidget()

        # Calibration object
        self.calibration = Calibration()
        ###################################
        # Temporary settings for debugging
        self.calibration.PRINT = True
        self.calibration.minCaptures = 2
        ###################################

        # Buttons
        self.captureBtn = QPushButton('Capture', self)
        self.calibrateBtn = QPushButton('Calibrate', self)
        self.saveBtn = QPushButton('Save to File', self)
        self.loadBtn = QPushButton('Load from File', self)
        self.closeBtn = QPushButton('Close', self)
        self.initUI()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateFrame)
        self.timer.start(1)


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createGridLayout()

        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.verticalGroupBox)
        self.setLayout(windowLayout)

        self.captureBtn.setToolTip('Capture image')
        self.captureBtn.clicked.connect(self.calibration.captureImage)
        self.captureBtn.setEnabled(True)

        self.calibrateBtn.setToolTip('Compute calibration')
        self.calibrateBtn.clicked.connect(self.calibration.computeCalibration)
        self.calibrateBtn.setEnabled(False)

        self.saveBtn.setToolTip('Save calibration to file')
        self.saveBtn.clicked.connect(lambda: self.calibration.saveCalibration('Calibration.npz'))
        self.saveBtn.setEnabled(False)

        self.loadBtn.setToolTip('Load calibration from file')
        self.loadBtn.clicked.connect(lambda: self.calibration.loadCalibration('Calibration.npz'))
        self.loadBtn.setEnabled(True)

        self.closeBtn.setToolTip('Close the Calibration window')
        self.closeBtn.clicked.connect(self.close)
        self.closeBtn.setEnabled(True)

        self.camera = Camera(0)

        self.show()

    def createGridLayout(self):
        self.verticalGroupBox = QGroupBox("Commands")
        layout = QGridLayout()
        n = 1
        for btn in [self.captureBtn, self.calibrateBtn, self.saveBtn, self.loadBtn, self.closeBtn]:
            layout.addWidget(btn, n, 1)
            n += 1
        layout.addWidget(self.videoWindow, 1, 2, n-1, 1)
        self.verticalGroupBox.setLayout(layout)

    def updateFrame(self):
        ret, img = self.camera.getFrame()
        if ret:
            img_height, img_width, img_colors = img.shape
            scale_w = float(self.video_width) / float(self.video_width)
            scale_h = float(self.video_height) / float(self.video_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = self.calibration.analyzeImage(img);
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QImage(img.data, width, height, bpl, QImage.Format_RGB888)
            self.videoWindow.setImage(image)
            self.updateButtons()

    def updateButtons(self):
        """Update button states depending on calibration"""
        self.calibrateBtn.setEnabled(self.calibration.enoughSamples())
        self.saveBtn.setEnabled(self.calibration.rms > -1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
