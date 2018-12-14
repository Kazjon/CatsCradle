
class Responder(object):
    def __init__(self, p):
        self.p = p

    def respond(self, audience, emotions, response_module, action_module):
        raise NotImplementedError
