from Reactor import AudienceReactor
import numpy as np

# This reactor detects when an adult has rapidly approached the piece and labels them a threat.
class ThreateningPersonDetector(AudienceReactor):
    def __init__(self, em, aud, size_ratio = 2):
        AudienceReactor.__init__(self, em, aud)
        self.targets = []
        self.size_ratio_threshold = size_ratio

    def detect(self):
        found = False
        for person in self.audience.persons:
            if person.isAdult():
                if person.faceSizeHistory[0] / min(person.faceSizeHistory) > self.size_ratio_threshold:
                    self.targets.append(person)
                    found = True
        return found

    def effect(self):
        # Append the "Threat" label to the audience member
        for person in self.targets:
            person.labels.add("Threat")


# This reactor detects when an adult has rapidly approached the piece and labels them a threat.
class DefaultInterestReactor(AudienceReactor):
    def __init__(self, em, aud, default_interest=1):
        AudienceReactor.__init__(self, em, aud)
        self.closest = None
        self.default_interest = default_interest

    def detect(self):
        faceSizes = [p.faceSizeHistory[0] for p in self.audience.persons]
        self.closest = self.audience[np.argmax(faceSizes)]
        return True

    def effect(self):
        # Append the default level of interest to the closest person
        self.closest.interestingness += self.default_interest
