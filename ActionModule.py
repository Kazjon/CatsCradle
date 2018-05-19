"""
* ActionModule (does things) [Alex/Marco/Mauro]
  - Maintains a list of Actions that can be performed
  - Handles conflicting concurrent gestures (note: we need to talk about how to resolve this)
  - Handles gestures that would take the system out of range (such as chaining gestures in one direction, providing illegal parameters, etc)
  - Handles eye stabilisation
  - Handles zero-finding during startup (in case of unexpected shutdown)
"""

from Action import *
from Marionette import *

class ActionModule(object):

    def __init__(self, config, currentAngles):
        # TODO: Get full list of motions from
        # https://docs.google.com/spreadsheets/d/1XPwe3iQbNzOgRDWYDuqAxW8JrQiBvvqikn3oN0fImSs/edit#gid=0
        self.angles = {}
        self.angles['rightHandFullRaise'] = [None, -980, None, -2298, None, None, None, None, None, None, -1919, None]
        self.angles['leftHandFullRaise'] = [None, None, -980, None, -2298, None, None, None, None, None, None, -1919]

        self.speed = {}
        self.speed['slow'] = 40
        self.speed['fast'] = 20

        self.currentAngles = currentAngles

    def moveTo(self, targetKey, speedKey):
        if targetKey not in self.angles.keys():
            raise InvalidTargetKeyError
        if speedKey not in self.speed.keys():
            raise InvalidSpeedKeyError
            
        target = self.angles[targetKey]
        speed = self.speed[speedKey]
        action = Action(target)
        sequence =  action.getAngleSequenceToTarget(self.currentAngles, speed)
        self.currentAngles = sequence[-1]
        return sequence


if __name__ == '__main__':

    marionette = Marionette()
    actionModule = ActionModule(None, marionette.getAngles())

    sequence = actionModule.moveTo('rightHandFullRaise', 'slow')
    sequence = sequence + actionModule.moveTo('leftHandFullRaise', 'fast')

    for angles in sequence:
        print ' '.join(map(str, angles))
