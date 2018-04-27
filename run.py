import sys
from SensorModule import SensorModule
from EmotionModule import EmotionModule
from ResponseModule import ResponseModule
from ActionModule import ActionModule

def runCatsCradle(config):
	"""Main entry point for Cat's Cradle."""
	action_module = ActionModule(config)
	response_module = ResponseModule(config,action_module)
	emotion_module = EmotionModule(config,response_module)
	sensor_module = SensorModule(config,emotion_module)

	while True:
		pass

def initialise():
	config = {}
	return config

if __name__ == "__main__":
	config = initialise()
	runCatsCradle(config)
	sys.exit()
