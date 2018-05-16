from MatrixUtil import *
from Marionette import *

#
# Used reference spaces
# - World (at the marionette fixation O, x=front, y=left, z=up)
# - One for each motor:
#      S = Shoulder rotation
#      SR/SL = Shoulder Right and Left
#      H = Head rotation (????? question: is the head motor static on the shoulders rod?????)
#      HR/HL = Head Right and Left
#      FR/FL = Foot Right and Left
#      AR/ALL = Arm Right and Left
#      WR/WL = Wrist Right and Left
#

class ReferenceSpace:
    """Class to convert from one reference space to another"""

    def __init__(self, marionette):
        """motors is the list of Motors objects in the following order:
        S, SR, SL, AL, H, HR, HL, FR, FL, WR, WL"""
        self.marionette = marionette

    def motorToWorld(self, motor):
        transform = np.identity(4)
        srcMotor = motor
        for destMotor in self.marionette.pathToWorld[motor]:
            srcMotorToDestMotor = np.dot(srcMotor.getRotationMatrix(), self.marionette.initialAToB[srcMotor][destMotor])
            transform = np.dot(srcMotorToDestMotor, transform)
            srcMotor = destMotor
        srcMotorToWorld = np.dot(srcMotor.getRotationMatrix(), self.marionette.initialAToB[srcMotor]['World'])
        return np.dot(srcMotorToWorld, transform)

    def motorAToMotorB(self, motorA, motorB):
        return np.dot(np.linalg.inv(self.motorToWorld(motorB)), self.motorToWorld(motorA))


if __name__ == '__main__':
    # Tests
    np.set_printoptions(suppress=True, precision=2)

    marionette = Marionette()
    ref = ReferenceSpace(marionette)

    motor = marionette.motorSL
    print ref.motorToWorld(motor)
    print motor.getStringPoint()
