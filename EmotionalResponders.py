from Responder import Responder
from random import random,choice
from EmotionModule import EMOTION_LABELS

class IdleResponder(Responder):

    def __init__(self, action_module, response_module, p=0.01):
        Responder.__init__(self,action_module, response_module, p)
        self.emotional_gestures = {e:[] for e in EMOTION_LABELS}
        self.emotional_gestures["neutral"] = []
        for e,g_list in self.emotional_gestures.iteritems():
            #TODO: Implement weights here and turn sequence into some kind of tuple including weight and sequence
            #TODO: Replace probability system with some kind of interval+probability thing?
            for name,sequence in action_module.gestureNameToSeq.iteritems():
                if name.startswith(e):
                    g_list.append(sequence)

    def respond(self, emotional_state, audience, idle):
        if idle:
            if random() < self.p:
                for emotion_name,emotion_quantity in emotional_state.iteritems():
                    if len(self.emotional_gestures[emotion_name]):
                        emotion_quantity -= 0.25
                        emotion_quantity = max(0,emotion_quantity)
                        emotion_quantity *= 1.33
                        if random() < emotion_quantity:
                            print "Expressing", emotion_name
                            return choice(self.emotional_gestures[emotion_name])
                if len(self.emotional_gestures["neutral"]):
                    print "Expressing neutrality"
                    return choice(self.emotional_gestures["neutral"])


#Responds to new people.  She's afraid of fast entry, but longs for children.
class EntryResponder(Responder):

    def __init__(self, action_module, response_module,p=0.1):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotional_state, audience, idle):
        #Check to see if there are any new people in the list of people
        #if any of them are a child, if so +longing, +interest and probably glance
        #If any of them are moving quickly, +fear, +interest and probably glance
        pass

#Responds to people who walk towards her. Variety of effects.
# TODO: Figure out how this should interact w/ (or subsume) threat detector
class ApproachResponder(Responder):

    def __init__(self, action_module, response_module, p=0.1):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotional_state, audience, idle):
        #Check to see if there are any people who are walking towards her
        #Add the "approached" tag to them
        #If any of them are approaching fast, add fear (more for men, less for children and seniors), interest and probably glance + respond
        #If any of them are approaching slow, add fear if male, shame if woman or senior, and longing if child, then probably glance
        pass

#Responds to people walking away from her based on how interesting they were.
class DepartResponder(Responder):

    def __init__(self, action_module, response_module, p=0.1):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotional_state, audience, idle):
        #Check to see if any people with the approached tag have been lost
        #If so, and they were low interest and a child, add longing
        #If so, and they were high interest, add interest to their record
        #If they were high interest and a child, add longing too
        #Additional interactions if there have been lots of recent exits
        pass

#Responds to people who are standing right up in her face.
class TooCloseResponder(Responder):

    def __init__(self, action_module, response_module, p=0.1):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotional_state, audience, idle):
        #Check to see if anyone is standing too close
        #If they were, add fear if adult (more if male), shame if senior, and low fear if child
        #If male, respond, otherwise glance
        pass

#Responds to families and couples entering her space.
class FamilyResponder(Responder):

    def __init__(self, action_module, response_module ,p=0.1):
        Responder.__init__(self,action_module, response_module, p)

    def respond(self, emotional_state, audience, idle):
        #Detect if people have been close for a while
        #If they're two adults, add the "Couple" tag and respond
        #If there's a child with them, add the "Family" tag and respond
        pass

