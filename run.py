import sys

from SensorModule import SensorModule
from EmotionModule import EmotionModule
from ResponseModule import ResponseModule
from ActionModule import ActionModule
from Audience import Audience
from Marionette import Marionette

show = True
if show:
	import cv2

def runCatsCradle(config):
	"""Main entry point for Cat's Cradle."""
	global show
	marionette = Marionette()
	action_module = ActionModule(config, marionette.getAngles())
	response_module = ResponseModule(config,action_module)
	emotion_module = EmotionModule(config,response_module)
	sensor_module = SensorModule(config,emotion_module)

	audience = Audience(sensor_module.personSensor)
	audience.personSensor.show = show

	while True:
		audience.update()
		#print "found ", len(audience.persons), " persons"

		if show:
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break


def initialise():
	config = {}
	return config

if __name__ == "__main__":
	config = initialise()

	runCatsCradle(config)

	if show:
		cv2.destroyAllWindows()

	sys.exit()
