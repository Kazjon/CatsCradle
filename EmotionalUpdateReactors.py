from Reactor import EmotionalReactor

#Induces slowly mounting fear when the room is empty
class LonelinessReactor(EmotionalReactor):
    def __init__(self, em, aud):
        EmotionalReactor.__init__(self,em, aud)

    def detect(self):
        if len(self.audience.persons):
            return False
        return True

    def effect(self):
        return {"fear":0.05}


# Induces slowly mounting shame when the audience is > 60% male
class MaleFearReactor(EmotionalReactor):
    def __init__(self, em, aud):
        EmotionalReactor.__init__(self,em, aud)

    def detect(self):
        if not len(self.audience.persons):
            return False
        males = 0.0
        for person in self.audience.persons:
            if person.gender == "M":
                males += 1
        if males/len(self.audience.persons) > 0.6:
            return True
        return False

    def effect(self):
        return {"shame":0.05}