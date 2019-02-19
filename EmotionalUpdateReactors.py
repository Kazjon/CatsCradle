from Reactor import Reactor
import numpy as np

from EmotionModule import EMOTION_DELTAS, try_add

def male_fraction(persons):
    if len(persons) == 0:
        return float("nan")
    males = 0.
    for person in persons:
        if person.gender == "M":
            males += 1
    return males/len(persons)


# This reactor adds a small amount of interest to whoever is closest -- just as a test of the interest system.
class DefaultInterestReactor(Reactor):
    def __init__(self, em, aud, default_interest=1):
        Reactor.__init__(self, em, aud)
        self.closest = None
        self.default_interest = default_interest

    def detect(self):
        if len(self.audience.persons):
            faceSizes = [p.faceSizeHistory[0] if len(p.faceSizeHistory) else 0 for p in self.audience.persons]
            self.closest = self.audience.persons[np.argmax(faceSizes)]
            return True
        return False

    def effect(self):
        # Append the default level of interest to the closest person
        self.closest.interestingness += self.default_interest

# This reactor detects how many people are in the room and reacts.
class RoomFullnessReactor(Reactor):
    def __init__(self, em, aud, crowd_threshold = 5):
        Reactor.__init__(self, em, aud)
        self.crowd_threshold = crowd_threshold
        self.effect_to_send = {}

    def detect(self):
        self.effect_to_send = {}
        num_p = len(self.audience.persons)

        # If the room is empty, add longing
        if num_p == 0:
            self.effect_to_send["longing"] = EMOTION_DELTAS["tiny"]
            self.effect_to_send["fear"] = EMOTION_DELTAS["tiny"]
        # If there are a few people, add fear for males, shame for females and seniors, and longing for children
        elif num_p < self.crowd_threshold:
            for p in self.audience.persons:
                if p.ageRange == "child":
                    try_add(self.effect_to_send, "longing", EMOTION_DELTAS["small"])
                elif p.ageRange == "senior":
                    continue
                elif p.gender == "M":
                    try_add(self.effect_to_send, "fear", EMOTION_DELTAS["moderate"])
                elif p.gender == "F":
                    try_add(self.effect_to_send, "shame", EMOTION_DELTAS["tiny"])
        else:
            if male_fraction(self.audience.persons) > 0.6:
                self.effect_to_send["shame"] = EMOTION_DELTAS["small"]
            else:
                self.effect_to_send["shame"] = EMOTION_DELTAS["tiny"]
        if len(self.effect_to_send):
            return True
        return False

        # If the room is full, add shame
        # If there are a lot of children, add longing and interest to all children
        return False

    def effect(self):
        return self.effect_to_send
