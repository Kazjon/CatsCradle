from Responder import Responder
from random import random
import numpy as np
from EmotionModule import EMOTION_LABELS, EMOTION_DELTAS, try_add

import time

import cv2

from scipy.spatial import distance

BASE_RESPONSE_CHANCE = 0.375 #Probability of conducting an idle gesture every response_interval
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
                if random() < self.p:
                    for emotion_name,emotion_quantity in emotion_module.emotion_as_dict().iteritems():
                        if len(self.emotional_gestures[emotion_name]):
                            emotion_quantity -= 0.25
                            emotion_quantity = max(0,emotion_quantity)
                            emotion_quantity *= 1.33
                            if random() < emotion_quantity:
                                print "Expressing", str(emotion_name).upper()
                                return np.random.choice(self.emotional_gestures[emotion_name][1],p=self.emotional_gestures[emotion_name][0])
                    if len(self.emotional_gestures["neutral"]):
                        print "Expressing NEUTRALITY"
                        return np.random.choice(self.emotional_gestures["neutral"][1],p=self.emotional_gestures["neutral"][0])
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
                ("rule 1.1", [([None, 'adult', 'F', 'new'], 2)], "shame", "large", "", 0, "small"),
                ("rule 1.2", [([None, 'adult', 'F', 'new'], 0)], "shame", "medium", "look", 2, "large"),
                ("rule 1.3", [([None, 'senior', None, 'new'], 0)], "shame", "small", "look", 2, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 1.4 - 1.6
            [
                ("rule 1.4", [([None, 'child', None, 'new'], 0),
                              ([None, 'adult', None, 'new'], 0)], "longing", "large", "", 0, "large"),
                ("rule 1.5", [([None, 'child', None, 'new'], 0)], "longing", "large", "look", 2, "large"),
                ("rule 1.6", [([None, 'adult', 'F', 'new'], 0),
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
                ("rule 2.1", [(['Approach', 'adult', 'M', 'current'], 0)], "fear", "extreme", "look", 2, "small"),
                ("rule 2.2", [(['Threat', 'adult', 'F', 'current'], 0)], "fear", "large", "look", 1, "small"),
                ("rule 2.3", [(['Threat', 'senior', None, 'current'], 0)], "fear", "large", "look", 1, "small")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.4 - 2.7
            [
                ("rule 2.4", [(['Approach', 'adult', 'F', 'current'], 0)], "shame", "medium", "look", 1, "large"),
                ("rule 2.5", [(['Creeping', 'adult', 'F', 'current'], 2)], "shame", "large", "", 0, "small"),
                ("rule 2.6", [(['Creeping', 'senior', None, 'current'], 0)], "shame", "small", "glance", 1, "medium"),
                ("rule 2.7", [(['Creeping', None, None, 'current'], 5)], "shame", "large", "", 0, "small")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.8 - 2.10
            [
                ("rule 2.8", [(['Threat', 'adult', 'M', 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny"),
                ("rule 2.9", [(['Threat', 'child', None, 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny"),
                ("rule 2.10", [(['Threat', 'adult', 'F', 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 2.11 - 2.16
            [
                ("rule 2.11", [(['Creeping', 'adult', 'F', 'current'], 0),
                               (['Creeping', 'adult', 'M', 'current'], 0)], "longing", "medium", "", 0, "medium"),
                ("rule 2.12", [(['Approach', 'adult', None, 'current'], 0),
                               (['Approach', 'child', None, 'current'], 0)], "longing", "large", "", 0, "large"),
                ("rule 2.13", [(['Creeping', 'child', None, 'current'], 0)], "longing", "large", "look", 2, "large"),
                ("rule 2.14", [(['Creeping', 'senior', None, 'current'], 0)], "longing", "small", "look", 1, "medium"),
                ("rule 2.15", [(['Approach', 'adult', 'F', 'current'], 0)], "longing", "medium", "look", 1, "large"),
                ("rule 2.16", [(['Creeping', 'adult', 'F', 'current'], 2)], "longing", "medium", "", 0, "small")
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
                ("rule 3.1", [([None, 'child', None, 'lost'], 0)], "shame", "large", "look", 2, "large"),
                ("rule 3.2", [([None, 'adult', 'F', 'lost'], 0),
                              ([None, 'adult', 'M', 'lost'], 0)], "shame", "large", "", 0, "small"),
                ("rule 3.3", [([None, 'senior', None, 'lost'], 0)], "shame", "medium", "look", 0.5, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 3.4 - 3.7
            [
                ("rule 3.4", [([None, 'adult', 'F', 'lost'], 2)], "longing", "small", "", 0, "small"),
                ("rule 3.5", [([None, 'senior', None, 'lost'], 0)], "longing", "small", "look", 1, "medium"),
                ("rule 3.6", [([None, 'adult', None, 'lost'], 0),
                              ([None, 'child', None, 'lost'], 0)], "longing", "medium", "", 0, "large"),
                ("rule 3.7", [([None, 'adult', 'F', 'lost'], 0)], "longing", "medium", "look", 2, "large")
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
            # rules list 4.1
            [
                ("rule 4.1", [(['RecentClose', 'adult', 'M', 'current'], 0)], "fear", "extreme", "look", 2, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 4.2 - 4.4
            [
                ("rule 4.2", [(['Close', 'adult', 'F', 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny"),
                ("rule 4.3", [(['Close', 'senior', None, 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny"),
                ("rule 4.4", [(['Close', 'child', None, 'current'], 0)], "surprise", "instant", "look", 0.5, "tiny")
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
        
        self.execute_rules(
            audience,
            # rules list 5.1 - 5.2
            [
                ("rule 5.1", [(['Moving', None, None, 'current'], 2)], "fear", "large", "", 0, "small"),
                ("rule 5.2", [(['Moving', 'adult', 'M', 'current'], 0)], "fear", "extreme", "look", 2, "small")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 5.3 - 5.7
            [
                ("rule 5.3", [(['Moving', 'adult', 'F', 'current'], 0)], "shame", "medium", "glance", 2, "large"),
                ("rule 5.4", [(['Moving', None, None, 'current'], 5)], "shame", "large", "", 0, "small"),
                ("rule 5.5", [(['Moving', 'senior', None, 'current'], 0)], "shame", "small", "glance", 1, "medium"),
             
                ("rule 5.6", [(['Still', 'adult', 'F', 'current'], 2)], "shame", "small", "", 0, "small"),
                ("rule 5.7", [(['Still', 'senior', None, 'current'], 0)], "shame", "small", "", 0, "medium")
            ]
        )
        
        self.execute_rules(
            audience,
            # rules list 5.8 - 5.12
            [
                ("rule 5.8", [(['Moving', 'child', None, 'current'], 0)], "longing", "large", "glance", 2, "large"),
                ("rule 5.9", [(['Moving', 'adult', 'F', 'current'], 0)], "longing", "medium", "glance", 1, "medium"),
                ("rule 5.10", [(['Moving', 'adult', 'F', 'current'], 0),
                              (['Moving', 'adult', 'M', 'current'], 0)], "longing", "medium", "", 0, "medium"),
             
                ("rule 5.11", [(['Still', 'adult', 'F', 'current'], 2)], "longing", "small", "", 0, "small"),
                ("rule 5.12", [(['Still', 'adult', None, 'current'], 0),
                               (['Still', 'child', None, 'current'], 0)], "longing", "small", "", 0, "large")
            ]
        )

        # glance / look rule
        # get a random person from self.persons_to_look_list and based on the item picked execute some response.
        self.execute_tracking()
        
        if len(self.emotional_effect) > 0:
            emotion_module.affectEmotions(self.emotional_effect.copy())
            # reset emotional_effects
            self.emotional_effect = {}

