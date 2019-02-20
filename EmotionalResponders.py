from Responder import Responder
from random import random
import numpy as np
from EmotionModule import EMOTION_LABELS, EMOTION_DELTAS, try_add

import time

import cv2

from scipy.spatial import distance

BASE_RESPONSE_CHANCE = 0.1 #Probability of conducting an idle gesture every response_interval
EXPRESSION_INTERVAL = 1. #Min seconds between checks for an expression.

HIGH_INTEREST_THRESH = 10 #An arbitrary line dividing "low" and "high" interest people
TOO_CLOSE_FRACTION = 8. #Fraction of the screen diagonal that the face diagonal must exceed for that person to be "too close"

MAX_STILLNESS_MOVEMENT = 5 #Max number of pixels you can have moved (every frame!) in order to be considered "too still"
MIN_FAST_MOVEMENT_FRACTION = 15.#Fraction of the screen diagonal that you must have covered quickly in order to be considered "too fast"

from Person import FACE_HISTORY_LENGTH

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
                                print "Expressing", emotion_name
                                return np.random.choice(self.emotional_gestures[emotion_name][1],p=self.emotional_gestures[emotion_name][0])
                    if len(self.emotional_gestures["neutral"]):
                        print "Expressing neutrality"
                        return np.random.choice(self.emotional_gestures["neutral"][1],p=self.emotional_gestures["neutral"][0])
                self.last_checked = t


#Responds to new people.  She's afraid of fast entry, but longs for children.
class EntryResponder(Responder):

    def __init__(self, action_module, response_module,p=0.5):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotion_module, audience, idle):
        emotional_effect = {}
        
        # rule 1.1
        if audience.get_num_people_with_condition(None, 'adult', 'F', 'new') > 2:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 1.1")
        # rule 1.2
        elif audience.get_num_people_with_condition(None, 'adult', 'F', 'new') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["medium"])
            print("rule 1.2")
        # rule 1.3
        elif audience.get_num_people_with_condition(None, 'senior', None, 'new') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["small"])
            print("rule 1.3")
        
        # rule 1.4
        if audience.get_num_people_with_condition(None, 'child', None, 'new') > 0 and audience.get_num_people_with_condition(None, 'adult', None, 'new') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["large"])
            print("rule 1.4")
        # rule 1.5
        elif audience.get_num_people_with_condition(None, 'child', None, 'new') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["large"])
            print("rule 1.5")
        # rule 1.6
        elif audience.get_num_people_with_condition(None, 'adult', 'F', 'new') > 0 and audience.get_num_people_with_condition(None, 'adult', 'M', 'new') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 1.6")

        # glance / look rule
        # ??
        # self.response_module.lookAt(person, duration=0.5)
        # self.response_module.glanceAt(person, duration=0.1)

        if len(emotional_effect):
            emotion_module.affectEmotions(emotional_effect)


#Responds to people who walk towards her. Variety of effects.
class ApproachResponder(Responder):
    def __init__(self, action_module, response_module, p=0.5, slow_size_ratio_range = [1.2,1.3],
                 approach_size_ratio = 1.5, threat_size_ratio = 1.75):
        Responder.__init__(self,action_module, response_module, p)
        self.approach_size_ratio = approach_size_ratio
        self.threat_size_ratio = threat_size_ratio
        self.slow_size_ratio_range = slow_size_ratio_range

    def respond(self, emotion_module, audience, idle):
        emotional_effect = {}
        
        # adding tags based on proximity and speed of audience
        for person in audience.persons:
            if person.faceSizeHistory is None or len(person.faceSizeHistory) == 0 or person.faceSizeHistory[0] is None:
                continue

            # Check to see if there are any people who are walking towards her, add the "approached" tag to them
            if person.faceSizeHistory[0] / min(person.faceSizeHistory) > self.approach_size_ratio:
                if not "RecentApproach" in person.labels:
                    print "APPROACHED!"
                    person.labels.add("Approached")
                    person.labels.add("RecentApproach")
                    person.interestingness += 5
                else:
                    person.labels.discard("RecentApproach")
            # If any of them are approaching fast, add "threat" tag
            if person.faceSizeHistory[0] / min(person.faceSizeHistory) > self.threat_size_ratio:
                if not "RecentThreat" in person.labels:
                    person.labels.add("Threat")
                    person.labels.add("RecentThreat")
                    person.interestingness += 25
                else:
                    person.labels.discard("RecentThreat")
            # If any of them are approaching slow, add "creeping" tag
            max_size_diff = max(person.faceSizeHistory) / min(person.faceSizeHistory)
            if max_size_diff > self.slow_size_ratio_range[0] and max_size_diff < self.slow_size_ratio_range[1]:
                if not "RecentCreeping" in person.labels:
                    person.labels.add("Creeping")
                    person.labels.add("RecentCreeping")
                    person.interestingness += 5
                else:
                    person.labels.discard("RecentCreeping")
            
        # respond based on tags
        
        # rule 2.1
        if audience.get_num_people_with_condition('RecentApproach', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["extreme"])
            print("rule 2.1")
        # rule 2.2
        elif audience.get_num_people_with_condition('RecentThreat', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["large"])
            print("rule 2.2")
        # rule 2.3
        elif audience.get_num_people_with_condition('RecentThreat', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["large"])
            print("rule 2.3")
        
        # rule 2.4
        if audience.get_num_people_with_condition('RecentApproach', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["medium"])
            print("rule 2.4")
        # rule 2.5
        elif audience.get_num_people_with_condition('RecentCreeping', 'adult', 'F', 'current') > 2:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 2.5")
        # rule 2.6
        elif audience.get_num_people_with_condition('RecentCreeping', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["small"])
            print("rule 2.6")
        # rule 2.7
        elif audience.get_num_people_with_condition('RecentCreeping', None, None, 'current') > 5:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 2.7")
        
        # rule 2.8
        if audience.get_num_people_with_condition('RecentThreat', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
            print("rule 2.8")
        # rule 2.9
        elif audience.get_num_people_with_condition('RecentThreat', 'child', None, 'current') > 0:
            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
            print("rule 2.9")

        # rule 2.10
        if audience.get_num_people_with_condition('RecentCreeping', 'adult', 'F', 'current') > 0 and audience.get_num_people_with_condition('Creeping', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 2.10")
        # rule 2.11
        elif audience.get_num_people_with_condition('RecentApproach', 'adult', None, 'current') > 0 and audience.get_num_people_with_condition('Approached', 'child', None, 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["large"])
            print("rule 2.11")
        # rule 2.12
        elif audience.get_num_people_with_condition('RecentCreeping', 'child', None, 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["large"])
            print("rule 2.12")
        # rule 2.13
        elif audience.get_num_people_with_condition('RecentCreeping', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["small"])
            print("rule 2.13")
        # rule 2.14
        elif audience.get_num_people_with_condition('RecentApproach', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 2.14")
        # rule 2.15
        elif audience.get_num_people_with_condition('RecentCreeping', 'adult', 'F', 'current') > 2:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 2.15")

        if len(emotional_effect):
            emotion_module.affectEmotions(emotional_effect)


#Responds to people walking away from her based on how interesting they were.
class DepartResponder(Responder):

    def __init__(self, action_module, response_module, p=0.5):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotion_module, audience, idle):
        emotional_effect = {}
        for person in audience.previousPersons:
            if person not in audience.persons:
                if "Approached" in person.labels:
                    if person.interestingness < HIGH_INTEREST_THRESH:
                        person.interestingness += 5
                    else:
                        person.interestingness += 10
                    if audience.numLostRecently() > 3:
                        if random() < self.p:
                            self.response_module.lookAt(person, duration=1)

        # respond
        
        # rule 3.1
        if audience.get_num_people_with_condition(None, 'child', None, 'lost') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 3.1")
        # rule 3.2
        elif audience.get_num_people_with_condition(None, 'adult', 'F', 'lost') > 0 and audience.get_num_people_with_condition(None, 'adult', 'M', 'lost') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 3.2")
        # rule 3.3
        elif audience.get_num_people_with_condition(None, 'senior', None, 'lost') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["medium"])
            print("rule 3.3")
        
        # rule 3.4
        if audience.get_num_people_with_condition(None, 'adult', 'F', 'lost') > 2:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["small"])
            print("rule 3.4")
        # rule 3.5
        elif audience.get_num_people_with_condition(None, 'senior', None, 'lost') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["small"])
            print("rule 3.5")
        # rule 3.6
        elif audience.get_num_people_with_condition(None, 'adult', None, 'lost') > 0 and audience.get_num_people_with_condition(None, 'child', None, 'lost') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 3.6")
        # rule 3.7
        elif audience.get_num_people_with_condition(None, 'adult', 'F', 'lost') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 3.7")
        
        if len(emotional_effect):
            emotion_module.affectEmotions(emotional_effect)

#Responds to people who are standing right up in her face.
class TooCloseResponder(Responder):

    def __init__(self, action_module, response_module, p=0.1):
        Responder.__init__(self,action_module, response_module, p)


    def respond(self, emotion_module, audience, idle):
        emotional_effect = {}
        width = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        screen_diag = distance.euclidean([0,0],[width,height])
        too_close_size = screen_diag/TOO_CLOSE_FRACTION
        #Check to see if anyone is standing too close
        for person in audience.persons:
            if person.faceSize() > too_close_size:
                if not "RecentClose" in person.labels:
                    person.labels.add("Close")
                    person.labels.add("RecentClose")
                    person.interestingness += 5
                else:
                    person.labels.discard("RecentClose")
                if random() < self.p:
                    self.response_module.glanceAt(person, duration=0.1)
    
        # respond
        
        # rule 4.1
        if audience.get_num_people_with_condition('RecentClose', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["extreme"])
            print("rule 4.1")
        
        # rule 4.2
        if audience.get_num_people_with_condition('RecentClose', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
            print("rule 4.2")
        # rule 4.3
        elif audience.get_num_people_with_condition('RecentClose', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
            print("rule 4.3")
        
        if len(emotional_effect):
            emotion_module.affectEmotions(emotional_effect)
            
class MovementResponder(Responder):
    
    def __init__(self, action_module, response_module, p=0.5):
        Responder.__init__(self,action_module, response_module, p)
        
    def respond(self, emotion_module, audience, idle):
        emotional_effect = {}
        width = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = audience.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        screen_diag = distance.euclidean([0,0],[width,height])
        too_fast_size = screen_diag/MIN_FAST_MOVEMENT_FRACTION
        for person in audience.persons:
            if len(person.faceLocHistory) == FACE_HISTORY_LENGTH:
                person.labels.discard("Still")
                person.labels.discard("Moving")
                pairdists = distance.squareform(distance.pdist(np.array(person.faceMidpointHistory)))
                if np.any(pairdists > too_fast_size):
                    person.labels.add("Moving")
                    person.interestingness += 5
                    if random() < self.p:
                        self.response_module.glanceAt(person, duration=0.5)
                adjacentdists = np.diagonal(pairdists,offset=1)
                if np.all(adjacentdists<MAX_STILLNESS_MOVEMENT):
                    person.labels.add("Still")
                    person.interestingness += 2
    
        # respond
        
        # rule 5.1
        if audience.get_num_people_with_condition('Moving', None, None, 'current') > 2:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["large"])
            print("rule 5.1")
        # rule 5.2
        elif audience.get_num_people_with_condition('Moving', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "fear", EMOTION_DELTAS["extreme"])
            print("rule 5.2")
        
        # rule 5.3
        if audience.get_num_people_with_condition('Moving', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["medium"])
            print("rule 5.3")
        # rule 5.4
        elif audience.get_num_people_with_condition('Moving', None, None, 'current') > 5:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["large"])
            print("rule 5.4")
        # rule 5.5
        elif audience.get_num_people_with_condition('Moving', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["small"])
            print("rule 5.5")
        # rule 5.6
        elif audience.get_num_people_with_condition('Still', 'adult', 'F', 'current') > 2:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["small"])
            print("rule 5.6")
        # rule 5.7
        elif audience.get_num_people_with_condition('Still', 'senior', None, 'current') > 0:
            try_add(emotional_effect, "shame", EMOTION_DELTAS["small"])
            print("rule 5.7")

#        # rule 5.8
#        if audience.get_num_people_with_condition('Moving', 'adult', 'M', 'current') > 0:
#            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
#            print("rule 5.8")
#        # rule 5.9
#        elif audience.get_num_people_with_condition('Moving', 'adult', 'F', 'current') > 0:
#            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
#            print("rule 5.9")
#        # rule 5.10
#        elif audience.get_num_people_with_condition('Moving', 'child', None, 'current') > 0:
#            try_add(emotional_effect, "surprise", EMOTION_DELTAS["instant"])
#            print("rule 5.10")

        # rule 5.8
        if audience.get_num_people_with_condition('Moving', 'child', None, 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["large"])
            print("rule 5.8")
        # rule 5.9
        elif audience.get_num_people_with_condition('Moving', 'adult', 'F', 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 5.9")
        # rule 5.10
        elif audience.get_num_people_with_condition('Moving', 'adult', 'F', 'current') > 0 and audience.get_num_people_with_condition('Moving', 'adult', 'M', 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["medium"])
            print("rule 5.10")
        # rule 5.11
        elif audience.get_num_people_with_condition('Still', 'adult', 'F', 'current') > 2:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["small"])
            print("rule 5.11")
        # rule 5.12
        elif audience.get_num_people_with_condition('Still', 'adult', None, 'current') > 0 and audience.get_num_people_with_condition('Still', 'child', None, 'current') > 0:
            try_add(emotional_effect, "longing", EMOTION_DELTAS["small"])
            print("rule 5.12")

        if len(emotional_effect):
            emotion_module.affectEmotions(emotional_effect)
            

