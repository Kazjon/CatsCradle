"""
Action (does a specific thing)
  - Accepts a number of parameters governing each movement (e.g. duration and amount)
  - Can move any combination of motors and eyes
  - e.g. EyeMove action w/parameters duration and angle
"""

import numpy as np
from Marionette import *

class Action(object):
    """"""
    def __init__(self, target, timeInterval):
        self.target = target
        self.timeInterval = timeInterval # seconds
        # TODO: check target angles are valid (assumed for now)

        # Marionette: Used for conversion
        self.marionette = Marionette()


    def getCmdsToTarget(self, origin, rotationSpeed):
        """ Return the commands (angle/speed) to be sent to each motor that needs to move
            motorName: motor name
            angleValue: target angle of the motor
            rotationSpeed: motor rotation speed

            Format of return value:
            [[motorName angleValue rotationSpeed] (optional)
             [motorName angleValue rotationSpeed] (optional)
             :
             :
             ]
        """
        # print "origin = ", origin
        # print "rotationSpeed = ", rotationSpeed
        # print "target = ", self.target
        output = []
        for originAngle, targetAngle, motor in zip(origin, self.target, self.marionette.motorList):
            if targetAngle is None or targetAngle == originAngle:
                # No motion requested: pass
                pass
            else:
                speed = rotationSpeed
                if motor.name == 'motorH':
                    # Adapt the speed from 0-80 to 400-800
                    speed = 400 + rotationSpeed / 80.0 * 400
                info = []
                info.append(motor.name)
                info.append(targetAngle)
                info.append(speed)
                output.append(info)

        return output

    def getLastTargetAngles(self):
        return self.lastTargetAngles


if __name__ == '__main__':

    from Marionette import *
    marionette = Marionette()

    # Define motion with all motors
    print "Full body motion"

    target = [21, -980, 0, -2298, 0, 73, 355, 0, -1573, 0, -1919, 821]
    action = Action(target, 0.5)

    print "Commands to target:"
    for cmd in action.getCmdsToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, cmd))

    # Define motion of only 4 motors (S, SR, AR, WR)
    # S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL
    print " "
    print "Right arm only"

    target = [21, -980, None, -2298, None, None, None, None, None, None, -1919, None]

    action = Action(target, 0.5)

    print "Commands to target:"
    for cmd in action.getCmdsToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, cmd))

    print "Commands to target too fast:"
    for cmd in action.getCmdsToTarget(marionette.getAngles(), 3):
        print ' '.join(map(str, cmd))
