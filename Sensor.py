"""
Sensor (a single thing we want to detect, e.g. position of people, age of people, eye gaze, etc) [Alex/Kaz]
  - Subscribes to Camera(s) necessary for it to detect.
  - Requests Camera frames as able to process them.
  - Need to figure out how to deal with participant coreference. Some Sensors may have to subscribe to other Sensors
    (maybe just the sensor that detects people) in order to attach their events to a particular person. Possibly do this
    using a parent/child relationship between sensors?  e.g. PersonSensor is the parent for AgeSensor, because the
    former's output is required for the latter to do its job?
  - e.g. PersonSensor, AgeSensor, GazeSensor, RearMovementSensor
  - Needs to implement a visualise() function that draws symbols for what it currently sees
"""

class Sensor(object):
	def __init__(self,cameras):
		self.cameras = cameras

