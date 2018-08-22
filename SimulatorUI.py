import sys
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GLU import *

from ActionModule import ActionModule

from UIUtils import MarionetteWidget
from Marionette import *

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
        self.lastSentAngles = self.marionette.getAngles();

        # ActionModule
        self.actionModule = ActionModule(None)
        # Flag defining how the simulator is used:
        # If True, use the controls to update the virtual visualization
        # If False, use the controls to move the real marionette
        self.simulate = not self.actionModule.connectedToArduino
        #### To test arduino command without the connection uncomment:
        #self.simulate = False

        # GL window
        self.visualWindow = None
        if self.simulate:
            self.visualWindow = MarionetteWidget(self.marionette, self)

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
        self.resetMotorBtn = {}
        for motor in self.marionette.motorList:
            self.sliderMotor[motor] = QSlider(Qt.Horizontal)
            self.sliderString[motor] = QSlider(Qt.Horizontal)
            self.labelMotorName[motor] = QLabel(motor.name)
            self.labelMotorAngle[motor] = QLabel(str(0))
            self.labelMotorStringLength[motor] = QLabel('')
            self.resetMotorBtn[motor] = QPushButton('Reset')

        # Eye control widgets
        self.sliderYaw = QSlider(Qt.Horizontal)
        self.labelYaw = QLabel("Yaw")
        self.sliderPitch = QSlider(Qt.Horizontal)
        self.labelPitch = QLabel("Pitch")

        # commands widgets
        self.resetAnglesBtn = QPushButton('Reset angles')
        self.resetStringsBtn = QPushButton('Reset strings')
        self.playBtn = QPushButton('Play')
        self.recordBtn = QPushButton('Record')
        self.closeBtn = QPushButton('Close')
        self.printBtn = QPushButton('Print Angles')

        # Goto controls
        self.anglesComboBox = QComboBox()
        self.speedComboBox = QComboBox()
        self.gotoBtn = QPushButton('GoTo Target')

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createViewCmdLayout()
        self.createStringCmdLayout()
        self.createMotorCmdLayout()
        self.createMotorResetBtnLayout()
        self.createMotorNameLayout()
        self.createEyeCmdLayout()
        self.createCommandsLayout()
        self.createGotoLayout()

        windowLayout = QGridLayout()
        # Line 1
        windowLayout.addWidget(self.nameGroupBox, 1, 1)
        windowLayout.addWidget(self.motorGroupBox, 1, 2)
        windowLayout.addWidget(self.resetGroupBox, 1, 3)
        windowLayout.addWidget(self.stringGroupBox, 1, 4)

        # Line 2
        windowLayout.addWidget(self.eyeGroupBox, 2, 1, 1, 3)
        windowLayout.addWidget(self.commandsGroupBox, 3, 1, 1, 2)
        windowLayout.addWidget(self.gotoGroupBox, 3, 3, 1, 1)

        if self.simulate:
            windowLayout.addWidget(self.visualWindow, 1, 5, 2, 1)
            windowLayout.addWidget(self.viewGroupBox, 3, 5)

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
            slider.setMinimum(motor.minAngle)
            slider.setMaximum(motor.maxAngle)
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

            # Reset button
            button = self.resetMotorBtn[motor]
            button.setToolTip('Reset ' + motor.name + ' rotation to 0 degree')
            button.clicked.connect(functools.partial(self.resetMotorAngle, [motor]))
            button.setEnabled(True)

        # Eye control settings
        for slider in [self.sliderPitch, self.sliderYaw]:
            slider.setEnabled(True)
            slider.setToolTip('Rotate eyes')
            slider.valueChanged.connect(self.moveEyes)
            slider.setMinimum(-20)
            slider.setMaximum(20)
            slider.setValue(0)
            slider.setTickInterval(1)

        # Reset string length button
        self.resetStringsBtn.setToolTip('Reset the strings initial length to their original values')
        self.resetStringsBtn.clicked.connect(self.resetStringLength)
        self.resetStringsBtn.setEnabled(True)
        # Reset motor angles button
        self.resetAnglesBtn.setToolTip('Reset all motors rotation to 0 degree')
        self.resetAnglesBtn.clicked.connect(functools.partial(self.resetMotorAngle, self.marionette.motorList))
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
        # Print button
        self.printBtn.setToolTip('Print the current motor angles')
        self.printBtn.clicked.connect(self.printAngles)
        self.printBtn.setEnabled(True)

        # GoTo controls
        for key in self.actionModule.angles.keys():
            self.anglesComboBox.addItem(key)
        for key in self.actionModule.speed.keys():
            self.speedComboBox.addItem(key)
        self.gotoBtn.setToolTip('Move the marionette to the selected pose at the selected speed')
        self.gotoBtn.clicked.connect(self.gotoTarget)
        self.gotoBtn.setEnabled(True)

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


    def createEyeCmdLayout(self):
        self.eyeGroupBox = QGroupBox("Eyes commands")
        layout = QGridLayout()
        i = 1
        for btnList in [[self.labelPitch, self.sliderPitch],
                        [self.labelYaw, self.sliderYaw]]:
            j = 1
            for btn in btnList:
                layout.addWidget(btn, i, j)
                j += 1
            i += 1
        self.eyeGroupBox.setLayout(layout)


    def createCommandsLayout(self):
        self.commandsGroupBox = QGroupBox("Commands")
        layout = QGridLayout()
        i = 1
        for btnList in [[self.resetAnglesBtn, self.resetStringsBtn],
                        [self.playBtn, self.recordBtn],
                        [self.closeBtn, self.printBtn]]:
            j = 1
            for btn in btnList:
                layout.addWidget(btn, i, j)
                j += 1
            i += 1
        self.commandsGroupBox.setLayout(layout)


    def createGotoLayout(self):
        self.gotoGroupBox = QGroupBox("GoTo")
        layout = QGridLayout()
        i = 1
        for ctrlList in [[self.anglesComboBox],
                        [self.speedComboBox],
                        [self.gotoBtn]]:
            j = 1
            for ctrl in ctrlList:
                layout.addWidget(ctrl, i, j)
                j += 1
            i += 1
        self.gotoGroupBox.setLayout(layout)


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


    def createMotorResetBtnLayout(self):
        self.resetGroupBox = QGroupBox("Motor reset")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.resetMotorBtn[motor], n, 1)
            n += 1
        self.resetGroupBox.setLayout(layout)


    def closeEvent(self, event):
        self.actionModule.stop()
        event.accept() # let the window close


    def rotateView(self):
        if self.visualWindow is not None:
            self.visualWindow.angleZ = self.rotationSlider.value()
            self.visualWindow.updateGL()


    def translateView(self):
        if self.visualWindow is not None:
            self.visualWindow.offsetZ = self.translationSlider.value()
            self.visualWindow.updateGL()


    def zoomView(self):
        if self.visualWindow is not None:
            self.visualWindow.zoom = self.zoomSlider.value() / 100.0
            self.visualWindow.updateGL()


    def moveEyes(self):
        for key in ['ER', 'EL']:
            self.marionette.eye[key].angleY = self.sliderPitch.value()
            self.marionette.eye[key].angleZ = self.sliderYaw.value()
        if self.simulate:
            self.visualWindow.updateGL()


    def updateMotorPos(self, motor):
        previousAngle = motor.angle
        # Update motor angle
        motor.angle = self.sliderMotor[motor].value()
        if self.simulate:
            if self.marionette.computeNodesPosition():
                self.visualWindow.updateGL()
        else:
            self.actionModule.moveToAngles(self.marionette.getAngles(), 10)

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
        if self.simulate:
            if not self.marionette.computeNodesPosition():
                motor.initialLength = previousLength
                self.sliderString[motor].setValue(previousLength)
            else:
                # Redraw
                self.visualWindow.updateGL()
        self.labelMotorStringLength[motor].setText(str(motor.initialLength))


    def resetMotorAngle(self, motorList):
        previousAngles = {}
        for motor in motorList:
            previousAngles[motor] = motor.angle
            motor.angle = 0
        if self.simulate:
            if not self.marionette.computeNodesPosition():
                # Restore previous angles
                for motor in motorList:
                    motor.angle = previousAngles[motor]
                    self.sliderMotor[motor].setValue(motor.angle)
            else:
                self.visualWindow.updateGL()
        self.updateSlider()

    def resetStringLength(self):
        m = self.marionette
        for key in m.motor.keys():
            motor = m.motor[key]
            motor.initialLength = m.length[key]
            self.sliderString[motor].setValue(motor.initialLength)
            self.sliderString[motor].repaint()

        # Initial string length should be a valid positions
        # no need to check ... unless motors are not at initial angle...
        if self.simulate:
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
                self.marionette.setAngles(angles)
                if self.simulate:
                    self.marionette.computeNodesPosition()
                    self.visualWindow.updateGL()
                else:
                    self.actionModule.moveToAngles(angles, 10)
            f.close()
            self.updateSlider()

    def printAngles(self):
        # Print current angles
        angles = []
        for motor in self.marionette.motorList:
            angles.append(motor.angle)
        print angles

    def gotoTarget(self):
        # Go to selected target
        self.actionModule.currentAngles = self.marionette.getAngles()
        target = self.anglesComboBox.currentText()
        speed = self.speedComboBox.currentText()
        for angles in self.actionModule.moveTo(target, speed):
            self.marionette.setAngles(angles)

        if self.simulate:
            self.marionette.computeNodesPosition()
            self.visualWindow.updateGL()

        self.updateSlider()

    def updateSlider(self):
        # Update the sliders angle
        for motor in self.marionette.motorList:
            self.sliderMotor[motor].setValue(motor.angle)
            self.sliderMotor[motor].repaint()
            self.labelMotorAngle[motor].setText(str(motor.angle))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
