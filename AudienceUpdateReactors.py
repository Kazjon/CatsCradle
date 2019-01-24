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
            if person.isAdult() and len(person.faceSizeHistory):
                if person.faceSizeHistory is None or person.faceSizeHistory[0] is None:
		    continue
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
        if len(self.audience.persons):
            faceSizes = [p.faceSizeHistory[0] if len(p.faceSizeHistory) else 0 for p in self.audience.persons]
            self.closest = self.audience.persons[np.argmax(faceSizes)]
            return True
        return False

    def effect(self):
        # Append the default level of interest to the closest person
        self.closest.interestingness += self.default_interest

