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


    def getCmdsToTarget(self, origin, speeds):
        """ Return the commands (angle/speed) to be sent to each motor that needs to move
            motorName: motor name
            angleValue: target angle of the motor
            speeds: motor rotation speeds

            Format of return value:
            [[motorName angleValue rotationSpeed] (optional)
             [motorName angleValue rotationSpeed] (optional)
             :
             :
             ]
        """
        # print "origin = ", origin
        # print "speeds = ", speeds
        # print "target = ", self.target
        if not len(self.target) == len(speeds):
            print "Invalid speeds number ", len(speeds)
            raise InvalidSpeedsNumber

        output = []
        for originAngle, targetAngle, speed, motor in zip(origin, self.target, speeds, self.marionette.motorList):
            if targetAngle is None or targetAngle == originAngle or speed == 0:
                # No motion requested: pass
                pass
            else:
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
    speeds = [ 5,   15, 0,     5, 5, 10,   5, 5,     5, 5,     5,   5]
    action = Action(target, 0.5)

    print "Commands to target:"
    for cmd in action.getCmdsToTarget(marionette.getAngles(), speeds):
        print ' '.join(map(str, cmd))

    # Define motion of only 4 motors (S, SR, AR, WR)
    # S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL
    print " "
    print "Right arm only"

    target = [21, -980, None, -2298, None, None, None, None, None, None, -1919, None, 90, None]

    action = Action(target, 0.5)

    print "Commands to target:"
    for cmd in action.getCmdsToTarget(marionette.getAngles(), speeds):
        print ' '.join(map(str, cmd))
