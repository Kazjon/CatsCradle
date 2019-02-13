"""
SensorModule (Handles all the sensory data with the exception of the in-head IMU) [Alex]
  - Maintains a list of Cameras
  - Maintains a list of Sensors, which subscribe to Cameras
  - Maintains a list of Reactors, which subscribe to Sensors
  - Feeds Camera frames to all subscribed Sensors, merging multiple cameras if needed
  - Feeds Sensor states to subscribed Reactors
  - Able to visualise current sensory input (just as simple points/lines/labels)
"""

from PersonSensor import PersonSensor
from Audience import Audience
import EmotionalUpdateReactors
import inspect
import time
from threading import Thread

REACTOR_UPDATE_INTERVAL = 0.1 #Min seconds between reactor updates

class SensorModule(object):

    def __init__(self, emotion_module):
        self.emotion_module = emotion_module
        self.reactors = []
        self.getPersonBodies = False
        self.last_updated_reactors = 0
        self.personSensor = PersonSensor()
        self.audience = Audience(self.personSensor)


    def loadSensors(self, camera):
        self.personSensor.load_camera(camera)


    def loadReactors(self):
        baseReactors = ["Reactor", "EmotionalReactor"]
        # Load Emotional Updaters (reactors that only change the audience state for other reactors to work with)
        for r in dir(EmotionalUpdateReactors):
            if r not in baseReactors and inspect.isclass(getattr(EmotionalUpdateReactors,r)):
                self.reactors.append(getattr(EmotionalUpdateReactors, r)(self.emotion_module,self.audience))


    def update(self):
        self.audience.update()
        t = time.time()
        if t - self.last_updated_reactors > REACTOR_UPDATE_INTERVAL:
            self.last_updated_reactors = t
            for reactor in self.reactors:
                reactor.update()
        self.emotion_module.update(self.audience)


    def cleanup(self):
        self.personSensor.release()
