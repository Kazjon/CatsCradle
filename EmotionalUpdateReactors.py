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

        # If the room is empty, be neutral
        if num_p == 0:
            # rule 6
            pass
        
        if len(self.effect_to_send):
            return True
        
        return False

    def effect(self):
        return self.effect_to_send
