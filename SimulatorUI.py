import sys
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GLU import *

from MarionetteOpenGL import *

class App(QWidget):

    def __init__(self):
        super(App, self).__init__()
        self.title = 'Cat\'s Craddle - Simulator window'
        self.left = 10
        self.top = 10
        self.width = 1200
        self.height = 680
        self.recordFile = None

        # Marionette object
        self.marionette = Marionette()

        # GL window
        self.visualWindow = glWidget(self, self.marionette)

        # View control widgets
        self.zoomLabel = QLabel('Zoom')
        self.zoomSlider = QSlider(Qt.Horizontal)
        self.rotationLabel = QLabel('Z Rotation')
        self.rotationSlider = QSlider(Qt.Horizontal)
        self.translationLabel = QLabel('Z Translation')
        self.translationSlider = QSlider(Qt.Horizontal)

        # Marionette control widgets
        self.sliderMotor = {}
        self.labelMotorAngle = {}
        self.sliderString = {}
        self.labelMotorName = {}
        self.labelMotorStringLength = {}
        for motor in self.marionette.motorList:
            self.sliderMotor[motor] = QSlider(Qt.Horizontal)
            self.sliderString[motor] = QSlider(Qt.Horizontal)
            self.labelMotorName[motor] = QLabel(motor.name)
            self.labelMotorAngle[motor] = QLabel(str(0))
            self.labelMotorStringLength[motor] = QLabel('')

        # commands widgets
        self.resetAnglesBtn = QPushButton('Reset angles')
        self.resetStringsBtn = QPushButton('Reset strings')
        self.playBtn = QPushButton('Play')
        self.recordBtn = QPushButton('Record')
        self.closeBtn = QPushButton('Close', self)

        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createViewCmdLayout()
        self.createStringCmdLayout()
        self.createMotorCmdLayout()
        self.createMotorNameLayout()
        self.createCommandsLayout()

        windowLayout = QGridLayout()
        # column 1
        windowLayout.addWidget(self.nameGroupBox, 1, 1)
        windowLayout.addWidget(self.motorGroupBox, 1, 2)
        windowLayout.addWidget(self.stringGroupBox, 1, 3)

        windowLayout.addWidget(self.commandsGroupBox, 2, 1, 1, 3)
        # column 2
        windowLayout.addWidget(self.visualWindow, 1, 5)
        windowLayout.addWidget(self.viewGroupBox, 2, 5)
        self.setLayout(windowLayout)

        # View rotation slider around Z axis
        self.rotationSlider.setToolTip('Rotate the view around the vertical axis')
        self.rotationSlider.valueChanged.connect(self.rotateView)
        self.rotationSlider.setMinimum(-180)
        self.rotationSlider.setMaximum(180)
        self.rotationSlider.setValue(0)
        self.rotationSlider.setTickInterval(10)
        self.rotationSlider.setEnabled(True)

        # View translation slider along Z axis
        self.translationSlider.setToolTip('Rotate the view around the vertical axis')
        self.translationSlider.valueChanged.connect(self.translateView)
        self.translationSlider.setMinimum(-2000)
        self.translationSlider.setMaximum(2000)
        self.translationSlider.setValue(0)
        self.translationSlider.setTickInterval(1)
        self.translationSlider.setEnabled(True)

        # Zoom slider
        self.zoomSlider.setToolTip('Zoom the view')
        self.zoomSlider.valueChanged.connect(self.zoomView)
        self.zoomSlider.setMinimum(50)
        self.zoomSlider.setMaximum(300)
        self.zoomSlider.setValue(100)
        self.zoomSlider.setTickInterval(1)
        self.zoomSlider.setEnabled(True)

        # Marionette settings (string length and motor rotation sliders)
        for motor in self.marionette.motorList:
            self.labelMotorAngle[motor].setMinimumSize(30, 0)
            self.labelMotorStringLength[motor].setText(str(motor.initialLength))

            # Motor rotation slider
            slider = self.sliderMotor[motor]
            slider.setEnabled(True)
            slider.setToolTip('Rotate ' + motor.name)
            # lambda does not work (all slider use the last motor)... why???
            # slider.valueChanged.connect(lambda: self.updateStringLength(motor))
            slider.valueChanged.connect(functools.partial(self.updateMotorPos, motor))
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(0)
            slider.setTickInterval(1)

            # String length slider (+/- 100mm around initial length)
            slider = self.sliderString[motor]
            slider.setEnabled(motor.isStatic)
            if motor.isStatic:
                slider.setToolTip('Set the length of the string of ' + motor.name)
                slider.setMinimum(motor.initialLength - 100)
                slider.setMaximum(motor.initialLength + 100)
                slider.setValue(motor.initialLength)
                # lambda does not work (all slider use the last motor)... why???
                # slider.valueChanged.connect(lambda: self.updateStringLength(motor))
                slider.valueChanged.connect(functools.partial(self.updateStringLength, motor))
                slider.setTickInterval(1)

        # Reset string length button
        self.resetStringsBtn.setToolTip('Reset the strings initial length to their original values')
        self.resetStringsBtn.clicked.connect(self.resetStringLength)
        self.resetStringsBtn.setEnabled(True)
        # Reset motor angles button
        self.resetAnglesBtn.setToolTip('Reset all motors rotation to 0 degree')
        self.resetAnglesBtn.clicked.connect(self.resetMotorAngle)
        self.resetAnglesBtn.setEnabled(True)

        # Record poses button
        self.recordBtn.setToolTip('Start recording the motor angles')
        self.recordBtn.clicked.connect(self.record)
        self.recordBtn.setEnabled(True)
        # Play motion button
        self.playBtn.setToolTip('Play the motion stored in a file')
        self.playBtn.clicked.connect(self.play)
        self.playBtn.setEnabled(True)

        # Close button
        self.closeBtn.setToolTip('Close the Simulator window')
        self.closeBtn.clicked.connect(self.close)
        self.closeBtn.setEnabled(True)

        self.show()


    def createViewCmdLayout(self):
        self.viewGroupBox = QGroupBox("View commands")
        layout = QGridLayout()
        i = 1
        for btnList in [[self.zoomLabel, self.zoomSlider],
                        [self.rotationLabel, self.rotationSlider],
                        [self.translationLabel, self.translationSlider]]:
            j = 1
            for btn in btnList:
                layout.addWidget(btn, i, j)
                j += 1
            i += 1
        self.viewGroupBox.setLayout(layout)


    def createCommandsLayout(self):
        self.commandsGroupBox = QGroupBox("Commands")
        layout = QGridLayout()
        i = 1
        for btnList in [[self.resetAnglesBtn, self.resetStringsBtn],
                        [self.playBtn, self.recordBtn],
                        [self.closeBtn]]:
            j = 1
            for btn in btnList:
                layout.addWidget(btn, i, j)
                j += 1
            i += 1
        self.commandsGroupBox.setLayout(layout)


    def createStringCmdLayout(self):
        self.stringGroupBox = QGroupBox("String length at 0 degree (mm)")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.sliderString[motor], n, 1)
            layout.addWidget(self.labelMotorStringLength[motor], n, 2)
            n += 1
        self.stringGroupBox.setMinimumSize(200, 0)
        self.stringGroupBox.setLayout(layout)


    def createMotorCmdLayout(self):
        self.motorGroupBox = QGroupBox("Motor rotations (degrees)")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.sliderMotor[motor], n, 1)
            layout.addWidget(self.labelMotorAngle[motor], n, 2)
            n += 1
        self.motorGroupBox.setMinimumSize(230, 0)
        self.motorGroupBox.setLayout(layout)


    def createMotorNameLayout(self):
        self.nameGroupBox = QGroupBox("Motor names")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.labelMotorName[motor], n, 1)
            n += 1
        self.nameGroupBox.setLayout(layout)


    def rotateView(self):
        self.visualWindow.angleZ = self.rotationSlider.value()
        self.visualWindow.updateGL()


    def translateView(self):
        self.visualWindow.offsetZ = self.translationSlider.value()
        self.visualWindow.updateGL()


    def zoomView(self):
        self.visualWindow.zoom = self.zoomSlider.value() / 100.0
        self.visualWindow.updateGL()


    def updateMotorPos(self, motor):
        previousAngle = motor.angle
        # Update motor angle
        motor.angle = self.sliderMotor[motor].value()
        if not self.marionette.computeNodesPosition():
            # Restore previous angle
            motor.angle = previousAngle
            self.sliderMotor[motor].setValue(previousAngle)
        else:
            # Redraw
            self.visualWindow.updateGL()
            if self.recordFile:
                angles = ''
                for motor in self.marionette.motorList:
                    angles += ' ' + str(motor.angle)
                self.recordFile.write(angles + '\n')
        self.labelMotorAngle[motor].setText(str(motor.angle))


    def updateStringLength(self, motor):
        previousLength = motor.initialLength
        # Update motor string length
        motor.initialLength = self.sliderString[motor].value()
        if not self.marionette.computeNodesPosition():
            motor.initialLength = previousLength
            self.sliderString[motor].setValue(previousLength)
        else:
            # Redraw
            self.visualWindow.updateGL()
        self.labelMotorStringLength[motor].setText(str(motor.initialLength))


    def resetMotorAngle(self):
        for motor in self.marionette.motorList:
            motor.angle = 0
            self.sliderMotor[motor].setValue(motor.angle)
            self.sliderMotor[motor].repaint()
            self.labelMotorAngle[motor].setText(str(motor.angle))

        # Initial motor pos should be a valid position
        # no need to check ... unless strings are not at initial length...
        self.marionette.computeNodesPosition()
        self.visualWindow.updateGL()

    def resetStringLength(self):
        m = self.marionette
        for key in m.motor.keys():
            motor = m.motor[key]
            motor.initialLength = m.length[key]
            self.sliderString[motor].setValue(motor.initialLength)
            self.sliderString[motor].repaint()

        # Initial string length should be a valid positions
        # no need to check ... unless motors are not at inital angle...
        self.marionette.computeNodesPosition()
        self.visualWindow.updateGL()

    def record(self):
        if self.recordFile == None:
            # Open the file
            filename, _ = QFileDialog.getOpenFileName(self,'QFileDialog.getOpenFileName()', '','Text Files (*.txt)')
            if filename:
                self.recordFile = open(filename, 'w')
                self.recordBtn.setToolTip('Stop recording the motor angles')
                self.recordBtn.setText('Stop Recording')
        else:
            self.recordBtn.setToolTip('Start recording the motor angles')
            self.recordBtn.setText('Record')
            # Stop recording
            self.recordFile.close()
            self.recordFile = None

        self.recordBtn.repaint()

    def play(self):
        # Open and replay the file
        filename, _ = QFileDialog.getOpenFileName(self,'QFileDialog.getOpenFileName()', '','Text Files (*.txt)')
        if filename:
            f = open(filename, 'r')
            ###### TODO: add check on the file's content (it might not be a recorded file)
            for line in f:
                angles = line.split()
                i = 0
                for motor in self.marionette.motorList:
                    motor.angle = int(angles[i])
                    i += 1
                self.marionette.computeNodesPosition()
                self.visualWindow.updateGL()
            f.close()
            for motor in self.marionette.motorList:
                self.labelMotorAngle[motor].setText(str(motor.angle))
                self.sliderMotor[motor].setValue(motor.angle)

class glWidget(QGLWidget):
    def __init__(self, parent, marionette):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)
        self.marionetteView = None
        self.marionette = marionette
        self.angleZ = 0
        self.zoom = 1
        self.offsetZ = 0

    def paintGL(self):
        glPushMatrix()
        glRotatef(self.angleZ, 0, 0, 1)
        glScale(self.zoom, self.zoom, self.zoom)
        glTranslatef(0, 0, self.offsetZ)
        self.marionetteView.draw(self.marionette)
        glPopMatrix()

    def initializeGL(self):
        self.marionetteView = MarionetteOpenGL()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
