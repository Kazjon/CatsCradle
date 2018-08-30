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

        self.lastTargetAngles = self.marionette.getAngles()

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

        self.lastTargetAngles = angleList[-1]

        return angleList

    def getStepsToTarget(self, origin, duration):
        """ Decompose the motion into self.interval seconds steps and
            return the sequence of increments and duration to be sent to the motors
            origin: list of motor angles in the same order as motorList
            duration: time to get to the target (seconds).

            Format of return value:
            [[duration [incr1 incr2 incr3...]
             [duration [incr1 incr2 incr3...]
             :
             [duration [incr1 incr2 incr3...]]
        """
        if duration == 0:
            return []

        if duration < 0:
            print "duration = ", duration
            raise InvalidDurationError

        if len(self.target) != len(origin):
            raise InvalidSizeError

        numSteps = int(duration / self.timeInterval)
        finalStepDuration = duration - numSteps * self.timeInterval
        #print "numSteps = ", numSteps
        #print "finalStepDuration = ", finalStepDuration

        # Get the duration and stepper increment for each motor for one cycle
        stepIncr = []
        remainingIncr = []
        finalIncr = []
        for originAngle, targetAngle, motor in zip(origin, self.target, self.marionette.motorList):
            if targetAngle == None:
                targetAngle = originAngle

            if not motor.isStatic:
                incr = targetAngle
                remaining = 0
            else:
                totalAngle = targetAngle - originAngle
                totalIncr = motor.motorIncrementFromAngle(totalAngle)
                incr = round(totalIncr / numSteps)
                remaining = totalIncr - incr * numSteps
                #print "totalAngle = ", totalAngle
                #print "totalIncr = ", totalIncr
                #print "incr = ", incr
                #print "remaining = ", remaining
            stepIncr.append(incr)
            remainingIncr.append(remaining)
            finalIncr.append(incr + remaining)

        # Generate the steps
        stepList = []
        n = 0
        step = []
        step.append(self.timeInterval)
        step.append(stepIncr)
        while n < numSteps:
            if n == numSteps - 1:
                if finalStepDuration == 0:
                    # There is no extra step, add the final incr to the last step
                    step = []
                    step.append(self.timeInterval)
                    step.append(finalIncr)
            stepList.append(step)
            n = n + 1

        # The last position should match the target pos and last finalStepDuration
        # except for the rotation motors (non static)
        if not finalStepDuration == 0:
            finalStep = []
            finalStep.append(finalStepDuration)
            finalStep.append(remainingIncr)
            stepList.append(finalStep)

        return stepList


    def getSpeedToTarget(self, origin, duration):
        """ Decompose the motion into self.interval (0.5) seconds steps and
            return the sequence of speeds and duration to be sent to the motors
            origin: list of motor angles in the same order as motorList
            duration: time to get to the target (seconds).

            Format of return value:
            [[duration [speed1 speed2 speed3...]
             [duration [speed1 speed2 speed3...]
             :
             [duration [speed1 speed2 speed3...]]
        """
        # print "origin = ", origin
        # print "duration = ", duration
        # print "target = ", self.target
        totalIncr = []
        stepList = self.getStepsToTarget(origin, duration)
        # print "num of steps = ", len(stepList)
        speedList = []
        remainings = []
        for originAngle, targetAngle, motor in zip(origin, self.target, self.marionette.motorList):
            remainings.append(0)
            if motor.isStatic:
                totalIncr.append(0)
            elif targetAngle is not None:
                totalIncr.append(targetAngle)
            else:
                totalIncr.append(originAngle)

        for step in stepList:
            duration = step[0]
            increments = np.add(step[1], remainings)
            speeds = []
            remainings = []
            currentIncr = []
            for incr, motor in zip(increments, self.marionette.motorList):
                if motor.isStatic:
                    speed = round(incr / duration)
                    speeds.append(speed)
                    remainings.append(incr - duration * speed)
                    currentIncr.append(duration * speed)
                else:
                    speeds.append(incr)
                    remainings.append(0)
                    currentIncr.append(0)

            totalIncr = np.add(totalIncr, currentIncr)

            newStep = []
            newStep.append(duration)
            newStep.append(speeds)
            speedList.append(newStep)

        self.lastTargetAngles = []
        for originAngle, incr, motor in zip(origin, totalIncr, self.marionette.motorList):
            if motor.isStatic:
                self.lastTargetAngles.append(originAngle + motor.angleFromMotorIncrement(incr))
            else:
                self.lastTargetAngles.append(incr)

        return speedList

    def getLastTargetAngles(self):
        return self.lastTargetAngles


if __name__ == '__main__':

    from Marionette import *
    marionette = Marionette()

    # Define motion with all motors
    print "Full body motion"

    target = [21, -980, 0, -2298, 0, 73, 355, 0, -1573, 0, -1919, 821]
    action = Action(target, 0.5)

    for angles in action.getAngleSequenceToTarget(marionette.getAngles(), 20):
        print ' '.join(map(str, angles))

    print "Steps to target:"
    for step in action.getStepsToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, step))

    print "Speed to target:"
    for step in action.getSpeedToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, step))

    # Define motion of only 4 motors (S, SR, AR, WR)
    # S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL
    print " "
    print "Right arm only"

    target = [21, -980, None, -2298, None, None, None, None, None, None, -1919, None]

    action = Action(target, 0.5)
    for angles in action.getAngleSequenceToTarget(marionette.getAngles(), 20):
        print ' '.join(map(str, angles))

    print "Steps to target:"
    for step in action.getStepsToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, step))

    print "Speed to target:"
    for step in action.getSpeedToTarget(marionette.getAngles(), 5):
        print ' '.join(map(str, step))
