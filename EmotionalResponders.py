from Responder import Responder
from random import random
import numpy as np
from EmotionModule import EMOTION_LABELS, EMOTION_DELTAS, try_add, normalise_emotion_vector

import time
import logging

import cv2

from scipy.spatial import distance

BASE_RESPONSE_CHANCE = 0.45 #Probability of conducting an idle gesture every response_interval
IDLE_CHANCE = 0.01 # probability of executing idle movements. 0.01 -> every 30 seconds
EXPRESSION_INTERVAL = 1. #Min seconds between checks for an expression.

HIGH_INTEREST_THRESH = 10 #An arbitrary line dividing "low" and "high" interest people
TOO_CLOSE_FRACTION = 45. #Fraction of the screen diagonal that the face diagonal must exceed for that person to be "too close"

MAX_STILLNESS_MOVEMENT = 5 #Max number of pixels you can have moved (every frame!) in order to be considered "too still"
MIN_FAST_MOVEMENT_FRACTION = 15.#Fraction of the screen diagonal that you must have covered quickly in order to be considered "too fast"

from Person import FACE_HISTORY_LENGTH, TAG_MEMORY_SPAN

class ExpressionResponder(Responder):
    def __init__(self, action_module, response_module, p=BASE_RESPONSE_CHANCE):
        Responder.__init__(self,action_module, response_module, p)
        self.last_checked = 0
        self.emotional_gestures = {e:[[],[]] for e in EMOTION_LABELS}
        self.emotional_gestures["neutral"] = [[],[]]
        for e,gestures_and_weights in self.emotional_gestures.iteritems():
            for name,weight_and_sequence in action_module.gestureNameToSeq.iteritems():
                if name.startswith(e):
                    weight = weight_and_sequence[0]
                    sequence = weight_and_sequence[1]
                    gestures_and_weights[0].append(weight)
                    gestures_and_weights[1].append(sequence)
            #Now we know how many gestures are in each category, divide the weight for each by the number to get a probability.
            gestures_and_weights[0] = [w/sum(gestures_and_weights[0]) for w in gestures_and_weights[0]]


    def respond(self, emotion_module, audience, idle):
        t = time.time()
        if t - self.last_checked > EXPRESSION_INTERVAL:
            if idle:
                # check to see if we should be neutral (when nobody is in the room and we got no focus of attention)
                if (self.response_module.focus is None) and (len(audience.persons) == 0):
                    if random() < IDLE_CHANCE:
                        print("idle movement")
                        logging.info(str(time.time()) + ' EMOTION:NEUTRAL')
                        g = np.random.choice(self.emotional_gestures["neutral"][1], p=self.emotional_gestures["neutral"][0])
                        logging.info(str(time.time()) + ' GESTURE:' + str(g))
                        return g
                    return

                # we have someone to respond to if we get the chance!
                if random() < self.p:
                    emotion_names = []
                    emotion_quantities = []
                    logging.info(str(time.time()) + ' INTENSITIES:' + str(emotion_module.emotion_as_dict()))
                    for emotion_name, emotion_quantity in emotion_module.emotion_as_dict().iteritems():
                        if len(self.emotional_gestures[emotion_name]):
                            emotion_quantity -= 0.25
                            emotion_quantity = max(0, emotion_quantity)
                            emotion_quantity *= 1.33
                        emotion_names.append(emotion_name)
                        emotion_quantities.append(emotion_quantity)
                    #logging.info(str(time.time()) + ' RAW_QUANTITIES:' + str(dict(zip(emotion_names, emotion_quantities))))
                    # here we select one emotion given the emotion_quantities as their probability of being selected
                    #emotion_quantities = emotion_quantities / np.linalg.norm(np.array(emotion_quantities))
                    #logging.info(str(time.time()) + ' PROBAS:' + str(dict(zip(emotion_names, emotion_quantities))))
                    selected_emotion = np.random.choice(emotion_names, p=emotion_module.emotion_as_dict().values())
                    #print "Expressing", str(emotion_name).upper()
                    logging.info(str(time.time()) + ' EMOTION:' + str(selected_emotion))
                    g = np.random.choice(self.emotional_gestures[selected_emotion][1], p=self.emotional_gestures[selected_emotion][0])
                    logging.info(str(time.time()) + ' GESTURE:' + str(g))
                    return g
                
                # the program hits this if there was no chance of executing any gesture (random < base_response_chance)
                self.last_checked = t


#Responds to new people.  She's afraid of fast entry, but longs for children.
class EntryResponder(Responder):

    def __init__(self, action_module, response_module,p=0.5):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotion_module, audience, idle):
        self.emotional_effect = {}
        self.persons_to_look_list = []
        
        self.execute_rules(
            audience,
            # rules list 1.1 - 1.3
            [
                ("sad/shame entry F+2", [([None, 'adult', 'F', 'new'], 2)], "shame", "small", "", 0, "small"),
                ("sad/shame entry F", [([None, 'adult', 'F', 'new'], 0)], "shame", "medium", "glance", 2, "large"),
                ("sad/shame entry S", [([None, 'senior', None, 'new'], 0)], "shame", "small", "glance", 2, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 1.4 - 1.6
            [
                ("longing entry C+A", [([None, 'child', None, 'new'], 0),
                              ([None, 'adult', None, 'new'], 0)], "longing", "large", "", 0, "large"),
                ("longing entry C", [([None, 'child', None, 'new'], 0)], "longing", "large", "glance", 2, "large"),
                ("longing entry F+M", [([None, 'adult', 'F', 'new'], 0),
                              ([None, 'adult', 'M', 'new'], 0)], "longing", "medium", "", 0, "small")
            ]
        )
        
        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()

        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}


#Responds to people who walk towards her. Variety of effects.
class ApproachResponder(Responder):
    def __init__(self, action_module, response_module, p=0.5, slow_size_ratio_range = [1.2, 1.25],
                 approach_size_ratio = 1.25, threat_size_ratio = 1.52):
        Responder.__init__(self,action_module, response_module, p)
        self.approach_size_ratio = approach_size_ratio
        self.threat_size_ratio = threat_size_ratio
        self.slow_size_ratio_range = slow_size_ratio_range

    def respond(self, emotion_module, audience, idle):
        
        # adding tags based on proximity and speed of audience
        for person in audience.persons:
            if person.faceSizeHistory is None or len(person.faceSizeHistory) == 0 or person.faceSizeHistory[0] is None:
                continue

	    max_size_diff = max(person.faceSizeHistory) / min(person.faceSizeHistory)
	    # If any of them are approaching fast, add "threat" tag
            if person.faceSizeHistory[0] / min(person.faceSizeHistory) > self.threat_size_ratio:
                #print("Threat\n")
                person.update_label('Threat', 25)
            # Check to see if there are any people who are walking towards her, add the "approached" tag to them
            elif person.faceSizeHistory[0] / min(person.faceSizeHistory) > self.approach_size_ratio:
                #print("Approach\n")
                person.update_label('Approach', 5)
            # If any of them are approaching slow, add "creeping" tag
            elif max_size_diff > self.slow_size_ratio_range[0] and max_size_diff < self.slow_size_ratio_range[1]:
                #print("Creeping\n")
                person.update_label('Creeping', 5)
            
        # respond based on tags
        
        self.emotional_effect = {}
        self.persons_to_look_list = []
        
        self.execute_rules(
            audience,
            # rules list 2.1 - 2.3
            [
                ("fear approach M", [(['Approach', 'adult', 'M', 'current'], 0)], "fear", "extreme", "glance", 2, "medium"),
                ("fear fast approach F", [(['Threat', 'adult', 'F', 'current'], 0)], "fear", "large", "glance", 1, "medium"),
                ("fear fast approach S", [(['Threat', 'senior', None, 'current'], 0)], "fear", "large", "glance", 1, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.4 - 2.7
            [
                ("sad/shame approach F", [(['Approach', 'adult', 'F', 'current'], 0)], "shame", "large", "glance", 1, "large"),
                ("sad/shame slow approach F+2", [(['Creeping', 'adult', 'F', 'current'], 2)], "shame", "large", "", 0, "small"),
                ("sad/shame slow approach S", [(['Creeping', 'senior', None, 'current'], 0)], "shame", "small", "glance", 1, "medium"),
                ("sad/shame slow approach +5", [(['Creeping', None, None, 'current'], 5)], "shame", "large", "", 0, "small")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.8 - 2.10
            [
                ("surprise fast approach M", [(['Threat', 'adult', 'M', 'current'], 0)], "surprise", "instant", "glance", 0.5, "tiny"),
                ("surprise fast approach C", [(['Threat', 'child', None, 'current'], 0)], "surprise", "instant", "glance", 0.5, "tiny"),
                ("surprise fast approach F", [(['Threat', 'adult', 'F', 'current'], 0)], "surprise", "extreme", "glance", 0.5, "tiny")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.11 - 2.16
            [
                ("longing slow approach F+M", [(['Creeping', 'adult', 'F', 'current'], 0),
                               (['Creeping', 'adult', 'M', 'current'], 0)], "longing", "medium", "", 0, "medium"),
                ("longing approach C+A", [(['Approach', 'adult', None, 'current'], 0),
                               (['Approach', 'child', None, 'current'], 0)], "longing", "large", "", 0, "large"),
                ("longing slow approach C", [(['Creeping', 'child', None, 'current'], 0)], "longing", "large", "glance", 2, "large"),
                ("longing slow approach S", [(['Creeping', 'senior', None, 'current'], 0)], "longing", "medium", "", 0, "medium"),
                ("longing approach F", [(['Approach', 'adult', 'F', 'current'], 0)], "longing", "medium", "", 0, "large"),
                ("longing slow approach F+2", [(['Creeping', 'adult', 'F', 'current'], 2)], "longing", "medium", "", 0, "small")
            ]
        )

        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()
        
        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}


#Responds to people walking away from her based on how interesting they were.
class DepartResponder(Responder):

    def __init__(self, action_module, response_module, p=0.5):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotion_module, audience, idle):
        
        for person in audience.previousPersons:
            if person not in audience.persons:
                if ('Approach' in person.labels) and (time.time() - person.labels['Approach'] < TAG_MEMORY_SPAN):
                    if person.interestingness < HIGH_INTEREST_THRESH:
                        person.interestingness += 5
                    else:
                        person.interestingness += 10

        # respond
        
        self.emotional_effect = {}
        self.persons_to_look_list = []
        
        self.execute_rules(
            audience,
            # rules list 3.1 - 3.3
            [
                ("sad/shame depart C", [([None, 'child', None, 'lost'], 0)], "shame", "large", "", 0, "large"),
                ("sad/shame depart F+M", [([None, 'adult', 'F', 'lost'], 0),
                              ([None, 'adult', 'M', 'lost'], 0)], "shame", "medium", "", 0, "small"),
                ("sad/shame depart S", [([None, 'senior', None, 'lost'], 0)], "shame", "small", "", 0, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 3.4 - 3.7
            [
                ("longing depart F+2", [([None, 'adult', 'F', 'lost'], 2)], "longing", "small", "", 0, "small"),
                ("longing depart S", [([None, 'senior', None, 'lost'], 0)], "longing", "small", "", 0, "medium"),
                ("longing depart C+A", [([None, 'adult', None, 'lost'], 0),
                              ([None, 'child', None, 'lost'], 0)], "longing", "medium", "", 0, "large"),
                ("longing depart F", [([None, 'adult', 'F', 'lost'], 0)], "longing", "medium", "", 0, "large")
            ]
        )

        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()
        
        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}


#Responds to people who are standing right up in her face.
class TooCloseResponder(Responder):

    def __init__(self, action_module, response_module, p=0.1):
        Responder.__init__(self,action_module, response_module, p)


    def respond(self, emotion_module, audience, idle):
        
        width = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        screen_diag = distance.euclidean([0,0],[width,height])
        too_close_size = screen_diag/TOO_CLOSE_FRACTION
        #Check to see if anyone is standing too close
        for person in audience.persons:
            if person.faceSize() > too_close_size:
                #print("Too Close\n")
                person.update_label('Close', 5)
    
        # respond
        
        self.emotional_effect = {}
        self.persons_to_look_list = []
        
        self.execute_rules(
            audience,
            # rules list 4.2 - 4.4
            [
                ("surprise close F", [(['Close', 'adult', 'F', 'current'], 0)], "surprise", "extreme", "", 0, "medium"),
                ("surprise close S", [(['Close', 'senior', None, 'current'], 0)], "surprise", "extreme", "", 0, "medium"),
                ("surprise close C", [(['Close', 'child', None, 'current'], 0)], "surprise", "extreme", "glance", 0.5, "medium")
            ]
        )
        
        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()
        
        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}

            
class MovementResponder(Responder):
    
    def __init__(self, action_module, response_module, p=0.5):
        Responder.__init__(self,action_module, response_module, p)
        
    def respond(self, emotion_module, audience, idle):
        
        width = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        screen_diag = distance.euclidean([0,0],[width,height])
        too_fast_size = screen_diag/MIN_FAST_MOVEMENT_FRACTION
        for person in audience.persons:
            if len(person.faceLocHistory) == FACE_HISTORY_LENGTH:
                # remove moving and still labels
                person.labels.pop('Moving', None)
                person.labels.pop('Still', None)
                pairdists = distance.squareform(distance.pdist(np.array(person.faceMidpointHistory)))
                if np.any(pairdists > too_fast_size):
                    #print("Moving\n")
                    person.update_label('Moving', 5)
                adjacentdists = np.diagonal(pairdists,offset=1)
                if np.all(adjacentdists<MAX_STILLNESS_MOVEMENT):
                    #print("Still\n")
                    person.update_label('Still', 2)
    
        # respond
        
        self.emotional_effect = {}
        self.persons_to_look_list = []
        
        #self.execute_rules(
        #    audience,
        #    # rules list 5.1 - 5.2
        #    [
        #        ("fear movement +2", [(['Moving', None, None, 'current'], 2)], "fear", "large", "", 0, "small"),
        #        ("fear movement M", [(['Moving', 'adult', 'M', 'current'], 0)], "fear", "extreme", "glance", 2, "small")
        #    ]
        #)
        
        #self.execute_rules(
        #    audience,
        #    # rules list 5.3 - 5.7
        #    [
        #        ("sad/shame movement F", [(['Moving', 'adult', 'F', 'current'], 0)], "shame", "small", "glance", 2, "large"),
        #        ("sad/shame movement +5", [(['Moving', None, None, 'current'], 5)], "shame", "medium", "", 0, "small"),
        #        ("sad/shame movement S", [(['Moving', 'senior', None, 'current'], 0)], "shame", "small", "glance", 1, "medium"),
             
        #        ("sad/shame still F+2", [(['Still', 'adult', 'F', 'current'], 2)], "shame", "small", "", 0, "small"),
        #        ("sad/shame still S", [(['Still', 'senior', None, 'current'], 0)], "shame", "medium", "", 0, "medium")
        #    ]
        #)
        
        #self.execute_rules(
        #    audience,
        #    # rules list 5.8 - 5.12
        #    [
        #        ("longing movement C", [(['Moving', 'child', None, 'current'], 0)], "longing", "large", "glance", 2, "large"),
        #        ("longing movement F", [(['Moving', 'adult', 'F', 'current'], 0)], "longing", "medium", "glance", 1, "medium"),
        #        ("longing movement F+M", [(['Moving', 'adult', 'F', 'current'], 0),
        #                      (['Moving', 'adult', 'M', 'current'], 0)], "longing", "medium", "", 0, "medium"),
        #     
        #        ("longing still F+2", [(['Still', 'adult', 'F', 'current'], 2)], "longing", "small", "", 0, "small"),
        #        ("longing still C+A", [(['Still', 'adult', None, 'current'], 0),
        #                               (['Still', 'child', None, 'current'], 0)], "longing", "small", "", 0, "large")
        #    ]
        #)

        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()
        
        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}

