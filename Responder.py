
class Responder(object):
    def __init__(self, action_module, response_module, p):
        self.p = p
        self.action_module = action_module
        self.response_module = response_module

    def respond(self, emotional_state, audience, idle):
        raise NotImplementedError
