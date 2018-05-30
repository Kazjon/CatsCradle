"""
SensorModule (Handles all the sensory data with the exception of the in-head IMU) [Alex]
  - Maintains a list of Cameras
  - Maintains a list of Sensors, which subscribe to Cameras
  - Maintains a list of Reactors, which subscribe to Sensors
  - Feeds Camera frames to all subscribed Sensors, merging multiple cameras if needed
  - Feeds Sensor states to subscribed Reactors
  - Able to visualise current sensory input (just as simple points/lines/labels)
"""

from Reactor import LonelinessReactor,NewPersonReactor
from Camera import Camera
from PersonSensor import PersonSensor
from Audience import Audience

class SensorModule(object):

    def __init__(self,config,emotion_module):
        self.config = config
        self.emotion_module = emotion_module
        self.cameras = []
        self.personSensor = None
        self.audience = None
        self.reactors = []

        self.loadCameras()
        self.loadSensors()
        self.loadReactors()

    def loadCameras(self):
        self.cameras.append(Camera(0))

    def loadSensors(self):
        self.personSensor = PersonSensor(self.cameras)
        self.audience = Audience(self.personSensor)

    def loadReactors(self):
        self.reactors.append(LonelinessReactor(self.emotion_module))
        self.reactors.append(NewPersonReactor(self.emotion_module))

    def update(self):
        self.audience.update()
        self.emotion_module.update(self.audience)
