"""
Reactor (Checks for a combination of conditions across sensors and triggers a response) [Alex]
  - Subscribes to a number of sensors
  - Triggers a reaction event that comprises a vector addition in EmotionalModule. This means it must be aware of the dimensions of the EmotionalModule.
  - [Optional] May trigger an Action directly (this is the idea of "reflexive actions" not governed by the AI)
  - e.g. LonelinessReactor, CrowdReactor, StaringReactor, ChildReactor
"""

class Reactor(object):
	def __init__(self,em):
		self.state = {}
		self.emotionModule = em
		pass

	def update(self,state):
		self.state = state
		if self.detect():
			self.trigger()

	def detect(self):
		pass

	def trigger(self):
		pass