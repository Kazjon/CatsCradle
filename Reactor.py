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
        if self.detect():
            effect = self.effect()
            if type(effect) is dict:
                self.emotionModule.affectEmotions(effect)

    def detect(self):
        raise NotImplementedError

    def effect(self):
        raise NotImplementedError
