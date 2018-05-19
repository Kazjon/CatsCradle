"""
Action (does a specific thing)
  - Accepts a number of parameters governing each movement (e.g. duration and amount)
  - Can move any combination of motors and eyes
  - e.g. EyeMove action w/parameters duration and angle
"""

import numpy as np

class Action(object):
    """"""
    def __init__(self, target):
        self.target = target
        # TODO: check target angles are valid (assumed for now)


    def getAngleSequenceToTarget(self, origin, numSteps):
        """Get the angles for the motors from the origin to target in
            numSteps regular steps
            origin: list of motor angles in the same order as motorList
        """
        if numSteps < 1:
            raise InvalidNumStepsError

        if len(self.target) != len(origin):
            raise InvalidSizeError

        # Get the currentAngles and motion increment for each motor for one cycle
        increment = []
        currentAngles = []
        for originAngle, targetAngle in zip(origin, self.target):
            currentAngles.append(originAngle)
            if targetAngle == None:
                incr = 0
            else:
                incr = (targetAngle - originAngle) / numSteps
            increment.append(incr)

        # Play the motion
        angleList = []
        n = 0
        while n < numSteps:
            currentAngles = np.add(currentAngles, increment)
            angleList.append(currentAngles)
            n = n + 1

        # The last position should match the target pos
        i = 0
        for targetAngle in self.target:
            if targetAngle != None:
                currentAngles[i] = targetAngle
            i = i + 1

        return angleList


if __name__ == '__main__':

    from Marionette import *
    marionette = Marionette()

    # Define motion with all motors
    print "Full body motion"

    target = [21, -980, 0, -2298, 0, 73, 355, 0, -1573, 0, -1919, 821]
    action = Action(target)

    for angles in action.getAngleSequenceToTarget(marionette.getAngles(), 20):
        print ' '.join(map(str, angles))

    # Define motion of only 4 motors (S, SR, AR, WR)
    # S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL
    print " "
    print "Right arm only"

    target = [21, -980, None, -2298, None, None, None, None, None, None, -1919, None]

    action = Action(target)
    for angles in action.getAngleSequenceToTarget(marionette.getAngles(), 20):
        print ' '.join(map(str, angles))
