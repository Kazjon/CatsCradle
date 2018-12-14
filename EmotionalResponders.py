from Responder import Responder
from random import random


class IdleResponder(Responder):

    def __init__(self, p=0.05):
        Responder.__init__(self,p)

    def respond(self, audience, emotions, gesture_queue, action_module):
        if not len(gesture_queue):
            if random() < self.p:
                for emotion_name,emotion_quantity in emotions:
                    if random() < emotion_quantity:
                        #TODO: Implement response from the emotion_name idle list!
                        continue


