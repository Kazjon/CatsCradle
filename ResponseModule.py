"""
* ResponseModule (Handles marionette response choices) [Kaz]
  - Selects responses given the current emotional state and the world state (the output of the sensors).
"""
import csv
import numpy as np
from collections import deque
import inspect

from Responder import Responder
import EmotionalResponders

class DummyResponseModule(object):

    def __init__(self,action_module):
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

class ResponseModule(object):

    def __init__(self,action_module,gesture_queue_length=5):
        self.action_module = action_module
        self.gesture_queue = deque()
        self.responders = []
        self.loadResponders(action_module)

        '''Disabled gesture list stuff -- may or may not end up using this
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
        '''

    def loadResponders(self, action_module):
        baseResponders = ["Responder"]
        # Load Emotional Responders (respodners that trigger based on the state of the audience and  for other reactors to work with)
        for r in dir(EmotionalResponders):
            if r not in baseResponders and inspect.isclass(getattr(EmotionalResponders,r)):
                self.responders.append(getattr(EmotionalResponders, r)(action_module))

    def update(self,emotional_state, audience):
        idle = self.action_module.is_idle()
        #Determine whether anything needs to be added to the queue
        for responder in self.responders:
            responder.respond(emotional_state, audience, idle)

        if idle and len(self.gesture_queue):
            self.action_module.execute(self.gesture_queue.pop())
