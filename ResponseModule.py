"""
* ResponseModule (Handles marionette response choices) [Kaz]
  - Selects responses given the current emotional state and the world state (the output of the sensors).
"""

class DummyResponseModule(object):

    def __init__(self,config,action_module):
        self.action_module = action_module

    def setEmotion(self, emotion, arg=None):
        # Temporary implementation to get some response based on person detection
        # TODO: Implement response from marionette's emotion (Kaz + Steph)
        if emotion == 'emotion0':
            # Lower arms slowly: 5 sec
            self.action_module.moveTo('rest', 5, 1, 20)

        if emotion == 'emotion1':
            # Raise the arm on the side of the detected person slowly : 5 sec
            if not arg == None:
                person = arg
                screenWidth = 1280
                if person.posCamera[0] < screenWidth/2:
                    self.action_module.moveTo('leftHandFullRaise', 5, 1, 20)
                else:
                    self.action_module.moveTo('rightHandFullRaise', 5, 1, 20)

        if emotion == 'emotion2':
            # Raise both arms, fast: 2 sec
            self.action_module.moveTo('bothHandFullRaise', 2, 10, 30)
