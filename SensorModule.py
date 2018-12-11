"""
SensorModule (Handles all the sensory data with the exception of the in-head IMU) [Alex]
  - Maintains a list of Cameras
  - Maintains a list of Sensors, which subscribe to Cameras
  - Maintains a list of Reactors, which subscribe to Sensors
  - Feeds Camera frames to all subscribed Sensors, merging multiple cameras if needed
  - Feeds Sensor states to subscribed Reactors
  - Able to visualise current sensory input (just as simple points/lines/labels)
"""

from Camera import Camera
from PersonSensor import PersonSensor
from Audience import Audience
import AudienceUpdateReactors
import EmotionalUpdateReactors
import inspect

class SensorModule(object):

    def __init__(self,config,emotion_module):
        self.config = config
        self.emotion_module = emotion_module
        self.cameras = []
        self.personSensor = None
        self.audience = None
        self.reactors = []

        self.loadCameras()
        self.loadSensors(config["cv_path"])
        self.loadReactors()

    def loadCameras(self):
        self.cameras.append(Camera(0))

    def loadSensors(self,cv_path):
        self.personSensor = PersonSensor(self.cameras)
        self.audience = Audience(self.personSensor)

    def loadReactors(self):
        baseReactors = ["Reactor","AudienceReactor","EmotionalReactor"]
        # Load Audience Updaters (reactors that only change the audience state for other reactors to work with)
        for r in dir(AudienceUpdateReactors):
            if r not in baseReactors and inspect.isclass(getattr(AudienceUpdateReactors,r)):
                self.reactors.append(getattr(AudienceUpdateReactors, r)(self.emotion_module,self.audience))
        # Load Emotional Updaters (reactors that only change the audience state for other reactors to work with)
        for r in dir(EmotionalUpdateReactors):
            if r not in baseReactors and inspect.isclass(getattr(EmotionalUpdateReactors,r)):
                self.reactors.append(getattr(EmotionalUpdateReactors, r)(self.emotion_module,self.audience))


    def update(self):
        self.audience.update()
        for reactor in self.reactors:
            reactor.update(self.audience)
        self.emotion_module.update(self.audience)
