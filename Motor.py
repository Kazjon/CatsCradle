from MatrixUtil import *

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

    def angleFromStringLength(self, length):
        """Returns the rotation angle in degrees needed to get a string of 'length' length"""
        if self.isStatic:
            l = length - self.initialLength
            theta = self.signZ * l / self.radius
            return np.degrees(tetha)
        else:
            return None

    def stringLengthFromAngle(self, angle):
        """Returns string length for a rotation of 'angle' degrees"""
        if self.isStatic:
            theta = np.radians(angle)
            l = self.signZ * theta * self.radius
            return self.initialLength + l
        else:
            return None

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
            return None


if __name__ == '__main__':
    # Tests
    m = Motor("motor", 10)

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
