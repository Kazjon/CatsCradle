"""
SensorModule (Handles all the sensory data with the exception of the in-head IMU) [Alex]
  - Maintains a list of Cameras
  - Maintains a list of Sensors, which subscribe to Cameras
  - Maintains a list of Reactors, which subscribe to Sensors
  - Feeds Camera frames to all subscribed Sensors, merging multiple cameras if needed
  - Feeds Sensor states to subscribed Reactors
  - Able to visualise current sensory input (just as simple points/lines/labels)
"""

from Reactor import Reactor

class SensorModule(object):

	def __init__(self,config,emotion_module):
		self.config = config
		self.emotion_module = emotion_module

	def loadCameras(self):
		raise NotImplementedError

	def loadSensors(self):
		raise NotImplementedError

	def loadReactors(self):
		raise NotImplementedError

class PrototypeSensorModule(SensorModule):

	def __init__(self,config,emotion_module):
		SensorModule.__init__(self,config,emotion_module)
		self.loadCameras()
		self.loadSensors()
		self.loadReactors()

	def loadCameras(self):
		pass

	def loadSensors(self):
		pass

	def loadReactors(self):
		pass
