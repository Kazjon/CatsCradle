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
from PersonSensor import PersonSensor,DummyPersonSensor
from Audience import Audience
import AudienceUpdateReactors
import EmotionalUpdateReactors
import inspect
from threading import Thread

class SensorModule(object):

    def __init__(self,config,emotion_module, getPersonBodies=False):
        self.config = config
        self.emotion_module = emotion_module
        self.cameras = []
        self.personSensor = None
        self.audience = None
        self.reactors = []
        self.getPersonBodies = False
        if "getPersonBodies" in config.keys():
            self.getPersonBodies = config["getPersonBodies"]
        if config["perception_mode"] == "full":
            self.cnn_detection = True
        else:
            self.cnn_detection = False

    def loadSensors(self,tf_sess):
        if self.config["perception_mode"] == "full":
            frame_div = 1
            frameskip = 4
        elif self.config["perception_mode"] == "fast":
            frame_div = 4
            frameskip = 16
        if self.config["perception_mode"] == "dummy":
            self.personSensor = DummyPersonSensor()
        else:
            self.personSensor = PersonSensor(self.cameras, tf_sess, frame_division_factor=frame_div,face_detection_frameskip=frameskip)
        self.audience = Audience(self.personSensor)


    def loadReactors(self):
        baseReactors = ["Reactor", "AudienceReactor", "EmotionalReactor"]
        # Load Audience Updaters (reactors that only change the audience state for other reactors to work with)
        for r in dir(AudienceUpdateReactors):
            if r not in baseReactors and inspect.isclass(getattr(AudienceUpdateReactors,r)):
                self.reactors.append(getattr(AudienceUpdateReactors, r)(self.emotion_module,self.audience))
        # Load Emotional Updaters (reactors that only change the audience state for other reactors to work with)
        for r in dir(EmotionalUpdateReactors):
            if r not in baseReactors and inspect.isclass(getattr(EmotionalUpdateReactors,r)):
                self.reactors.append(getattr(EmotionalUpdateReactors, r)(self.emotion_module,self.audience))


    def update(self):
        self.audience.update(self.config["tf_sess"], getPersonBodies=self.getPersonBodies, cnn_detection=self.cnn_detection)
        for reactor in self.reactors:
            reactor.update()
        self.emotion_module.update(self.audience)


    def cleanup(self):
        self.personSensor.video_capture.release()
