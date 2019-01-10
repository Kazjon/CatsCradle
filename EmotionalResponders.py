from Responder import Responder
from random import random,choice
from EmotionModule import EMOTION_LABELS

class IdleResponder(Responder):

    def __init__(self, action_module, p=0.1):
        Responder.__init__(self,action_module, p)
        self.emotional_gestures = {e:[] for e in EMOTION_LABELS}
        self.emotional_gestures["neutral"] = []
        for e,g_list in self.emotional_gestures.iteritems():
            for gesture in action_module.emotionToSeq.keys():
                if gesture.startswith(e):
                    g_list.append(gesture)

    def respond(self, emotional_state, audience, idle):
        if idle:
            if random() < self.p:
                for emotion_name,emotion_quantity in emotional_state.iteritems():
                    if len(self.emotional_gestures[emotion_name]):
                        emotion_quantity -= 0.25
                        emotion_quantity = max(0,emotion_quantity)
                        emotion_quantity *= 1.33
                        if random() < emotion_quantity:
			    print "Responding to:", emotion_name
                            self.action_module.executeGesture(choice(self.emotional_gestures[emotion_name]))
                if len(self.emotional_gestures["neutral"]):
		    print "Responding in neutral."
                    self.action_module.executeGesture(choice(self.emotional_gestures["neutral"]))



