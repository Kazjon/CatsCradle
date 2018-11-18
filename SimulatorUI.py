import sys
import functools
import decimal

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GLU import *

from ActionModule import ActionModule

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
        self.sliderSpeed = {}
        self.checkMotorSave = {}
        self.labelMotorName = {}
        self.labelMotorSpeed = {}
        self.resetMotorBtn = {}
        for motor in self.marionette.motorList:
            self.sliderMotor[motor] = QSlider(Qt.Horizontal)
            self.sliderSpeed[motor] = QSlider(Qt.Horizontal)
            self.labelMotorName[motor] = QLabel(motor.name)
            self.labelMotorAngle[motor] = QLabel(str(0))
            self.labelMotorSpeed[motor] = QLabel('')
            self.resetMotorBtn[motor] = QPushButton('Reset')
            self.checkMotorSave[motor] = QCheckBox()

        # commands widgets
        self.resetAnglesBtn = QPushButton('Reset angles')
        self.closeBtn = QPushButton('Close')
        self.printBtn = QPushButton('Save Position')

        # Goto controls
        self.positionsComboBox = QComboBox()
        self.gotoBtn = QPushButton('GoTo Target')

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createSpeedCmdLayout()
        self.createCheckSaveCmdLayout()
        self.createMotorCmdLayout()
        self.createMotorResetBtnLayout()
        self.createMotorNameLayout()
        self.createCommandsLayout()
        self.createGotoLayout()

        windowLayout = QGridLayout()
        # Line 1
        windowLayout.addWidget(self.nameGroupBox, 1, 1)
        windowLayout.addWidget(self.motorGroupBox, 1, 2)
        windowLayout.addWidget(self.resetGroupBox, 1, 3)
        windowLayout.addWidget(self.speedGroupBox, 1, 4)
        windowLayout.addWidget(self.checkSaveGroupBox, 1, 5)

        # Line 2
        windowLayout.addWidget(self.commandsGroupBox, 3, 1, 1, 2)
        windowLayout.addWidget(self.gotoGroupBox, 3, 3, 1, 1)

        self.setLayout(windowLayout)

        # Marionette settings (string length and motor rotation sliders)
        for motor in self.marionette.motorList:
            self.labelMotorAngle[motor].setMinimumSize(30, 0)
            self.labelMotorSpeed[motor].setMinimumSize(30, 0)

            # Motor rotation slider
            slider = self.sliderMotor[motor]
            slider.setEnabled(True)
            slider.setToolTip('Rotate ' + motor.name)
            # lambda does not work (all slider use the last motor)... why???
            # slider.valueChanged.connect(lambda: self.updateMotorPos(motor))
            slider.valueChanged.connect(functools.partial(self.updateMotorPos, motor))
            min = motor.minAngle
            max = motor.maxAngle
            defaultValue = motor.defaultAngle
            print "motor ", motor.name, " default angle = ", motor.defaultAngle
            if motor.isStatic:
                min = motor.stringLengthFromAngle(motor.minAngle)
                max = motor.stringLengthFromAngle(motor.maxAngle)
                defaultValue = motor.stringLengthFromAngle(motor.defaultAngle)
            slider.setMinimum(min)
            slider.setMaximum(max)
            slider.setValue(defaultValue)
            slider.setTickInterval(1)

            # Speed slider
            slider = self.sliderSpeed[motor]
            slider.setEnabled(1)
            slider.setToolTip('Set the speed of the ' + motor.name)
            slider.setMinimum(0)
            slider.setMaximum(80)
            # lambda does not work (all slider use the last motor)... why???
            # slider.valueChanged.connect(lambda: self.updateSpeed(motor))
            slider.valueChanged.connect(functools.partial(self.updateSpeed, motor))
            slider.setValue(10)
            slider.setTickInterval(1)

            # Reset button
            button = self.resetMotorBtn[motor]
            button.setToolTip('Reset ' + motor.name + ' rotation to 0 degree')
            button.clicked.connect(functools.partial(self.resetMotorAngle, [motor]))
            button.setEnabled(True)

            # Save checkbox
            checkBox = self.checkMotorSave[motor]
            checkBox.setChecked(1)
            checkBox.setToolTip('Enable/Disable saving of the ' + motor.name + ' angle in the new position')

        # Speed values for the head motor are 400-800
        motor = self.marionette.motor['H']
        slider = self.sliderSpeed[motor]
        slider.setMinimum(400)
        slider.setMaximum(800)
        slider.setValue(500)

        # Disable Rigth Arm slider since there is no motor on that joint
        motor = self.marionette.motor['AR']
        slider = self.sliderMotor[motor]
        slider.setEnabled(False)
        slider = self.sliderSpeed[motor]
        slider.setEnabled(False)
        checkBox = self.checkMotorSave[motor]
        checkBox.setChecked(0)
        checkBox.setEnabled(False)

        # Reset motor angles button
        self.resetAnglesBtn.setToolTip('Reset all motors rotation to 0 degree')
        self.resetAnglesBtn.clicked.connect(functools.partial(self.resetMotorAngle, self.marionette.motorList))
        self.resetAnglesBtn.setEnabled(True)

        # Close button
        self.closeBtn.setToolTip('Close the Simulator window')
        self.closeBtn.clicked.connect(self.close)
        self.closeBtn.setEnabled(True)
        # Print button
        self.printBtn.setToolTip('Save the current motor angles')
        self.printBtn.clicked.connect(self.savePosition)
        self.printBtn.setEnabled(True)

        # GoTo controls
        self.updateTargetComboBox()
        self.gotoBtn.setToolTip('Move the marionette to the selected pose at the selected speed')
        self.gotoBtn.clicked.connect(self.gotoTarget)
        self.gotoBtn.setEnabled(True)

        self.show()


    def createCommandsLayout(self):
        self.commandsGroupBox = QGroupBox("Commands")
        layout = QGridLayout()
        i = 1
        for btnList in [[self.resetAnglesBtn],
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
        for ctrlList in [[self.positionsComboBox],
                        [self.gotoBtn]]:
            j = 1
            for ctrl in ctrlList:
                layout.addWidget(ctrl, i, j)
                j += 1
            i += 1
        self.gotoGroupBox.setLayout(layout)


    def createSpeedCmdLayout(self):
        self.speedGroupBox = QGroupBox("Motor Speed")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.sliderSpeed[motor], n, 1)
            layout.addWidget(self.labelMotorSpeed[motor], n, 2)
            n += 1
        self.speedGroupBox.setMinimumSize(200, 0)
        self.speedGroupBox.setLayout(layout)


    def createCheckSaveCmdLayout(self):
        self.checkSaveGroupBox = QGroupBox("Saved motor")
        layout = QGridLayout()
        n = 1
        for motor in self.marionette.motorList:
            layout.addWidget(self.checkMotorSave[motor], n, 1)
            n += 1
        self.checkSaveGroupBox.setLayout(layout)


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


    def updateMotorPos(self, motor):
        # Update motor label
        self.labelMotorAngle[motor].setText(str(self.sliderMotor[motor].value()))


    def updateSpeed(self, motor):
        speed = self.sliderSpeed[motor].value()
        self.labelMotorSpeed[motor].setText(str(speed))


    def resetMotorAngle(self, motorList):
        previousAngles = {}
        for motor in motorList:
            value = motor.defaultAngle
            if motor.isStatic:
                value = motor.stringLengthFromAngle(motor.defaultAngle)
            self.sliderMotor[motor].setValue(value)
            self.sliderMotor[motor].repaint()


    def savePosition(self):
        # Get current angles
        angles = []
        speeds = []
        for motor in self.marionette.motorList:
            if self.checkMotorSave[motor].isChecked():
                angles.append(motor.angle)
                speeds.append(self.sliderSpeed[motor].value())
            else:
                angles.append(None)
                speeds.append(0)
        # create dialog to enter name
        text, ok = QInputDialog.getText(self, 'Save current position', 'Name:')
        if ok:
            self.actionModule.addPosition(text, angles, speeds)
        # Update target dropdown
        self.updateTargetComboBox()


    def updateTargetComboBox(self):
        self.positionsComboBox.clear()
        self.positionsComboBox.addItem("Current slider angles")
        for key in sorted(self.actionModule.positions.keys()):
            self.positionsComboBox.addItem(key)


    def sliderAngles(self):
        # Return current angles
        angles = []
        for motor in self.marionette.motorList:
            value = self.sliderMotor[motor].value()
            angle = value
            if motor.isStatic:
                angle = motor.angleFromStringLength(value)
            angles.append(angle)
        return angles


    def sliderSpeeds(self):
        # Return current speeds
        speeds = []
        for motor in self.marionette.motorList:
            speeds.append(self.sliderSpeed[motor].value())
        return speeds


    def gotoTarget(self):
        # Go to selected target
        self.actionModule.currentAngles = self.marionette.getAngles()
        target = self.positionsComboBox.currentText()

        # print "target = ", target
        if target == "Current slider angles":
            # print "angles = ", self.sliderAngles()
            angles = self.actionModule.moveToAngles(self.sliderAngles(), self.sliderSpeeds())
        else:
            angles = self.actionModule.moveTo(target)
        self.marionette.setAngles(angles)

        self.updateSliders()


    def updateSliders(self):
        # Update the sliders angle
        for motor in self.marionette.motorList:
            value = motor.angle
            if motor.isStatic:
                value = motor.stringLengthFromAngle(motor.angle)
            self.sliderMotor[motor].setValue(value)
            self.sliderMotor[motor].repaint()
            # value with precision 1
            value = decimal.Decimal(value).quantize(decimal.Decimal('1'))
            self.labelMotorAngle[motor].setText(str(value))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
