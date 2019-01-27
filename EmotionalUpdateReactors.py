from Reactor import Reactor
import numpy as np

#Induces slowly mounting fear when the room is empty
#TODO: Roll this into the room fullness thing
class LonelinessReactor(Reactor):
    def __init__(self, em, aud):
        Reactor.__init__(self,em, aud)

    def detect(self):
        if len(self.audience.persons):
            return False
        return True

    def effect(self):
        return {"fear":0.005}


# Induces slowly mounting shame when the audience is > 60% male
class MaleShameReactor(Reactor):
    def __init__(self, em, aud):
        Reactor.__init__(self,em, aud)

    def detect(self):
        if len(self.audience.persons) > 2:
            males = 0.0
            for person in self.audience.persons:
                if person.gender == "M":
                    males += 1
            if males/len(self.audience.persons) > 0.6:
                return True
        return False

    def effect(self):
        return {"shame":0.05}

    from Reactor import Reactor
    import numpy as np

# This reactor detects when an adult has rapidly approached the piece and labels them a threat.
class ThreateningPersonReactor(Reactor):
    def __init__(self, em, aud, size_ratio=2):
        Reactor.__init__(self, em, aud)
        self.targets = []
        self.size_ratio_threshold = size_ratio

    def detect(self):
        found = False
        for person in self.audience.persons:
            if person.getAgeRange() == "adult" and len(person.faceSizeHistory):
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
    def __init__(self, em, aud, default_interest=1):
        Reactor.__init__(self, em, aud)

    def detect(self):
        num_p = len(self.audience.persons)

        # If the room is empty, add longing
        # If there are a few people, add fear for males, shame for females and seniors, and longing for children
        # If the room is full, add shame
        # If there are a lot of children, add longing and interest to all children
        return False

    def effect(self):
        pass

# Update who is moving quickly (or standing still) and then react based on proportions
class MovementReactor(Reactor):
    def __init__(self, em, aud, default_interest=1):
        Reactor.__init__(self, em, aud)

    def detect(self):
        # Detect anyone who hasn't moved for the last while, add "Still" tag, interest and fear
        # Detect anyone who has moved a lot for the last while, add "Moving" tag, interest and glance
        # Anyone who doesn't quality for one of those tags should have both removed
        return False

    def effect(self):
        pass

