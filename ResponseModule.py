"""
* ResponseModule (Handles marionette response choices) [Kaz]
  - Selects responses given the current emotional state and the world state (the output of the sensors).
"""
import csv
import numpy as np

class DummyResponseModule(object):

    def __init__(self,config,action_module):
        self.action_module = action_module

    def setEmotion(self, emotion, arg=None):
        # Temporary implementation to get some response based on person detection
        # TODO: Implement response from marionette's emotion (Kaz + Steph)
        if emotion == 'emotion0':
            # Lower arms
            self.action_module.moveTo('rest', 'slow')

        if emotion == 'emotion1':
            # Raise the arm on the side of the detected person
            if not arg == None:
                person = arg
                screenWidth = 1280
                if person.posCamera[0] < screenWidth/2:
                    self.action_module.moveTo('leftHandFullRaise', 'slow')
                else:
                    self.action_module.moveTo('rightHandFullRaise', 'slow')

        if emotion == 'emotion2':
            # Raise both arms
            self.action_module.moveTo('bothHandFullRaise', 'fast')

class ResponseModule(object):

    def __init__(self,config,action_module,gesture_list="responses.csv"):
        self.action_module = action_module
        gestures = []
        with open(gesture_list) as f:
            reader = csv.reader(f)
            for row in reader:
                g_pos = np.asarray([float(r) for r in row[:4]])
                if any(g_pos<0):
                    raise ValueError("Found a response definition with an emotional component below 0.")
                if any(g_pos>1):
                    raise ValueError("Found a response definition with an emotional component above 1.")
                if not sum(g_pos) == 1.:
                    raise ValueError("Found a response definition with an emotional component that didn't sum to 1.")
                gestures.append((g_pos,row[4:]))

    def update(self,emotional_state):
        pass
