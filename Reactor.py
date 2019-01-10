"""
Reactor (Checks for a combination of conditions across sensors and triggers a response) [Alex]
  - Subscribes to a number of sensors
  - Triggers a reaction event that comprises a vector addition in EmotionalModule. This means it must be aware of the dimensions of the EmotionalModule.
  - [Optional] May trigger an Action directly (this is the idea of "reflexive actions" not governed by the AI)
  - e.g. LonelinessReactor, CrowdReactor, StaringReactor, ChildReactor
"""

##TODO: Need to refactor these in order to affect the Audience object directly. Refer to the new 5pt system and redesign.

# Base class for all Reactor objects
class Reactor(object):
    def __init__(self,em, aud):
        self.emotionModule = em
        self.audience = aud
        self.responseModule = self.emotionModule.response_module

    def update(self):
        raise NotImplementedError

    def detect(self):
        raise NotImplementedError

    def effect(self):
        raise NotImplementedError

class AudienceReactor(Reactor):
    def __init__(self, em, aud):
        Reactor.__init__(self,em, aud)

    def update(self):
        if self.detect():
            self.effect()

class EmotionalReactor(Reactor):
    def __init__(self, em, aud):
        Reactor.__init__(self, em, aud)

    def update(self):
        if self.detect():
            self.emotionModule.affectEmotions(self.effect())

class ReflexReactor(Reactor):
    def __init__(self, em, aud):
        Reactor.__init__(self, em, aud)

    def update(self):
        if self.detect():
            self.emotionModule.affectEmotions(self.effect())


#-----------
'''
class NewPersonReactor(Reactor):
    def __init__(self,em):
        Reactor.__init__(self,em)
        self.previous_persons = 0

    def detect(self):
        if len(self.audience.persons) and not self.previous_persons:
            self.previous_persons = len(self.audience.persons)
            return True
        self.previous_persons = len(self.audience.persons)
        return False

    def effect(self):
        return [0,0,0.5,0]

class LeftReactor(Reactor):
    def __init__(self,em):
        Reactor.__init__(self,em)

    def detect(self):
        if not len(self.audience.persons):
            return False
        averageXPos = 0
        for person in self.audience.persons:
            averageXPos += person.posCamera[0]
        averageXPos /= len(self.audience.persons)
        if averageXPos < 500:
            return True
        return False

    def effect(self):
        return [0,0,0,0.05]

class RightReactor(Reactor):
    def __init__(self, em):
        Reactor.__init__(self, em)

    def detect(self):
        if not len(self.audience.persons):
            return False
        averageXPos = 0
        for person in self.audience.persons:
            averageXPos += person.posCamera[0]
        averageXPos /= len(self.audience.persons)
        if averageXPos > 900:
            return True
        return False

    def effect(self):
        return [0, 0.05, 0, 0]
'''
