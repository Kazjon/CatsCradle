from MatrixUtil import *
from math import pi

class Motor:
    """Class to handle the rotation motor
    Motor reference space:
    Static motor (with string, do not rotate with motor)
        origin = string fixed point (hole in rod (HR, HL, SR, SL), or contact with motor(AL, HD, FR, FL))
        x axis = axis perpendicular to the string pointing toward the string
        y axis = down
        z axis = axis of positive rotation
    Non static motor (no string, rotates with the motor)
        origin = center of motor rotation
        x axis = perpendicular to rod axis, pointing front
        y axis = rod axis, pointing left
        z axis = axis of positive rotation"""

    def __init__(self, name, radius, stringLength = 0):
        self.name = name
        self.radius = radius
        self.initialLength = stringLength # String length when angle = 0
        self.isStatic = (self.initialLength > 0)
        self.signZ = 1 # positive (allow flexibility if z axis is reverse rotation axis)
        self.angle = 0 # current angle (degrees)
        self.circumference = 2 * pi * self.radius
        if self.isStatic:
            # min angle possible (l >= 0)
            self.minAngle = self.angleFromStringLength(0)
            self.maxAngle = 3000 # TODO: Limit = max length of string
        else:
            self.minAngle = -180
            self.maxAngle = 180


    def angleFromStringLength(self, length):
        """Returns the rotation angle in degrees needed to get a string of 'length' length"""
        if self.isStatic:
            # Compute number of full rotations:
            l = length - self.initialLength
            n = int(l / self.circumference)
            # Remaining length
            l = l - n * self.circumference
            theta = self.signZ * l / self.radius
            theta = theta  + n * 2 * pi
            return np.degrees(theta)
        else:
            raise InvalidCallForStaticMotor

    def stringLengthFromAngle(self, angle):
        """Returns string length for a rotation of 'angle' degrees"""
        if self.isStatic:
            # Compute number of full rotations:
            theta = np.radians(angle)
            n = int(theta / 2 / pi)
            # Remaining angle
            theta = theta - n * 2 * pi
            l = self.signZ * theta * self.radius
            l = self.initialLength + l + n * self.circumference
            if l < 0 :
                print "Motor::stringLengthFromAngle(", angle ,"): ", self.name, "error: invalid angle -> length ", l, " < 0"
                raise InvalidAngleError
            return l
        else:
            raise InvalidCallForStaticMotor

    def getRotationMatrix(self):
        """Returns the transform of the current rotation"""
        if self.isStatic:
            return np.identity(4)
        else:
            return RotateZ(np.identity(4), self.signZ * self.angle)

    def getStringPoint(self):
        """Returns current coordinates of the string attachment point in motor reference space
            This assumes the string goes straight down.
            Use only as a starting point for marionette's optimisation algo (truss)
        """
        if self.isStatic:
            length = self.stringLengthFromAngle(self.angle)
            return [0, length, 0]
        else:
            raise InvalidCallForStaticMotor


if __name__ == '__main__':
    # Tests
    m = Motor("motor", 10, 100)

    print m.angle
    print m.getRotationMatrix()
    print m.getStringPoint()
    m.angle += 45
    print m.angle
    print m.getRotationMatrix()
    print m.getStringPoint()
    m.angle += 45
    print m.angle
    print m.getRotationMatrix()
    print m.getStringPoint()
    m.angle += 45
    print m.angle
    print m.getRotationMatrix()
    print m.getStringPoint()

    angle = 50
    length = m.stringLengthFromAngle(angle)
    a = m.angleFromStringLength(length)
    print "stringLengthFromAngle(", angle, ") = ", length
    print "angleFromStringLength(", length, ") = ", a
