
class Responder(object):
    def __init__(self, action_module, p):
        self.p = p
        self.action_module = action_module

    def respond(self, emotional_state, audience, idle):
        raise NotImplementedError
