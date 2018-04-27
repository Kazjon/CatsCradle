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
		self.cameras = self.loadCameras(config)
		self.sensors = self.loadSensors(config)
		self.reactors = self.loadReactors(config,emotion_module)

	def loadCameras(self,config):
		return []

	def loadSensors(self,config):
		return []

	def loadReactors(self,config,emotion_module):
		return []
