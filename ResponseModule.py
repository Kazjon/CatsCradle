"""
* ResponseModule (Handles marionette response choices) [Kaz]
  - Selects responses given the current emotional state and the world state (the output of the sensors).
"""
import sys
import csv
import numpy as np
from collections import deque
import inspect

from Responder import Responder
import EmotionalResponders
import time
import logging

DISABLE_GESTURES = False
ATTENTION_CHANGE_MINIMUM = 8.0 #minimum time before attention will be checked again
TRACKING_INTERVAL = 0.05 #How frequently to send new locations of the current focus of attention so that eyes+head track them.

BACK_MOVEMENT_RESPONSE_INTERVAL = 5 # seconds that takes for lookaway gesture to complete
BACK_MOVEMENT_RESPONSE_FACTOR = 200.0 # proba of response for back camera = the movement amount / factor (this variable)
BACK_MOVEMENT_RESPONSE_MIN = 10 # the minimum amount of motion in the back camera that triggers response

class ResponseModule(object):

    def __init__(self,action_module,gesture_queue_length=5):
        self.action_module = action_module
        self.gesture_queue = deque()
        self.responders = []
        self.loadResponders(action_module)
        self.last_updated = 0
        self.last_attention_change = 0
        self.focus = None
        self.returnToFocusAt = 0
        self.last_tracked = 0
        self.currentEyeTarget = (-1,-1)
        self.last_focus_id = -1
        self.back_movement_response_timeout = 0

    def loadResponders(self, action_module):
        baseResponders = ["Responder"]
        # Load Emotional Responders (respodners that trigger based on the state of the audience and  for other reactors to work with)
        for r in dir(EmotionalResponders):
            if r not in baseResponders and inspect.isclass(getattr(EmotionalResponders,r)):
                self.responders.append(getattr(EmotionalResponders, r)(action_module, self))

    def update(self,emotion_module, audience):
        idle = self.action_module.isMarionetteIdle()
        emotional_state = emotion_module.emotion_as_dict()

        #Update the focus of attention, pushing any needed changes to the left of the queue
        self.updateAttentionAndTrack(audience, emotional_state)

        if not self.focus is None and self.focus.id != self.last_focus_id:
            #print("current focus: " + str(self.focus))
            logging.info(str(time.time()) + ' FOCUS:' + str(self.focus))
            self.last_focus_id = self.focus.id

        #Determine whether anything needs to be added to the queue
        #Note: Some responders may use the glanceAt and lookAt functions below to push things to the left of the queue
        
        Responder.all_rules = set()
        
        if not DISABLE_GESTURES:
            for responder in self.responders:
                response = responder.respond(emotion_module, audience, idle)
                if response is not None:
                    self.gesture_queue.append(response)
    
            if len(self.gesture_queue):
                # [:] is for copying the list since we clear the queue afterwards
                gesture = self.gesture_queue.pop()[:]
                if gesture[0] == '046a_Reset':
                    print("Going back to zero.")
                    logging.info(str(time.time()) + ' BACK_TO_ZERO:.')
                self.action_module.executeGesture(gesture, useThread=True)
            # discard the queue since the contents might not be relavant in the next update cycle
            self.gesture_queue.clear()
        
        self.last_updated = time.time()
        
        if len(Responder.all_rules) > 0:
            logging.info(str(time.time()) + ' RULES:' + str(','.join(Responder.all_rules)))
	#     print(','.join(Responder.all_rules))
        #    sys.stdout.write(','.join(Responder.all_rules) + ' '*50 + '\r')
        #    sys.stdout.flush()

    def updateAttentionAndTrack(self, audience, emotional_state):
        t = time.time()
        
        # return early if we are in the middle of executing lookaway
        if t < self.back_movement_response_timeout:
            return
        
        # checking for back camera movement
        max_back_movement = max(audience.back_movement_left, audience.back_movement_right)
        if (max_back_movement > BACK_MOVEMENT_RESPONSE_MIN) and np.random.random() < (max_back_movement / BACK_MOVEMENT_RESPONSE_FACTOR):
            self.lookAway(audience)
            self.back_movement_response_timeout = t + BACK_MOVEMENT_RESPONSE_INTERVAL
            print("back camera movement -> looking away.")
            logging.info(str(t) + ' LOOKAWAY:.')
            return
        
        if (t > self.returnToFocusAt) and (t - self.last_attention_change > ATTENTION_CHANGE_MINIMUM):
            if len(audience.persons):
                sorted_emotions = sorted(emotional_state.items(), key=lambda x: x[1], reverse=True)
                highest_emotion = sorted_emotions[0]
                second_emotion = sorted_emotions[1]
                
                #Probabilistically select a focus of attention between the current and highest attention person
                interests = [p.interestingness for p in audience.persons]
                ids = [p.id for p in audience.persons]
                most_interesting = np.argmax(interests)
                if self.focus is None or self.focus.id not in ids:
                    self.setFocus(audience.persons[most_interesting])
                    self.last_attention_change = t
                    return
                elif ids[most_interesting] is not self.focus.id:
                    interest_proportion = interests[most_interesting] / self.focus.interestingness
                    p = 0.5 * interest_proportion
                    if np.random.random() < p:
                        self.setFocus(audience.persons[most_interesting])
                        self.last_attention_change = t
                        return
                    else:
                        #Don't check again for at least ATTENTION_CHANGE_MINIMUM even if we didn't change
                        self.last_attention_change = t
            else:
                #There's no one around, so ditch the focus.
                self.focus = None
        elif (self.focus is not None) and (t - self.last_tracked > TRACKING_INTERVAL):
            if t > self.returnToFocusAt:
                self.lookAt(self.focus)
                self.last_tracked = t


    #These attention-directing functions are putting eyes/head movements directly into the action module's priority queue

    #Looks at a person with just eyes. If duration > 0, will return to the focal person after duration seconds.
    def glanceAt(self,person, duration=0):
        target = tuple(person.faceMidpoint())
        if self.differentToCurrentTarget(target):
            logging.info(str(time.time()) + ' TRACKING_E:' + str(target))
            self.currentEyeTarget = target
            self.action_module.moveEyes(target)
            if duration > 0:
                self.returnToFocusAt = time.time() + duration

    #Looks at a person with both eyes and head.  If duration > 0, will return to the focal person after duration seconds.
    def lookAt(self,person,duration=0):
        target = tuple(person.faceMidpoint())
        if self.differentToCurrentTarget(target):
            logging.info(str(time.time()) + ' TRACKING_I:' + str(target))
            self.currentEyeTarget = target
            self.action_module.moveEyesAndHead(target)
            if duration > 0:
                self.returnToFocusAt = time.time() + duration

    def setFocus(self,person):
        self.lookAt(person)
        logging.info(str(time.time()) + ' CHANGE_FOCUS:' + str(person))
        self.focus = person

    def lookAway(self, audience):
        # note that sides of the camera is reversed.
        if audience.back_movement_left < audience.back_movement_right:
            gesture = '041c_HeadRotLHalfMed'
        else:
            gesture = '040c_HeadRotRHalfMed'
        self.action_module.executeLookAway(gesture)

    def differentToCurrentTarget(self,target):
        return not [round(p) for p in target] == [round(p) for p in self.currentEyeTarget]
