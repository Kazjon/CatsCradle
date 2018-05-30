import sys

from SensorModule import SensorModule
from EmotionModule import DummyEmotionModule
from ResponseModule import DummyResponseModule
from ActionModule import ActionModule

show = True
if show:
    import cv2

def runCatsCradle(config):
    """Main entry point for Cat's Cradle."""
    global show
    action_module = ActionModule(config)
    response_module = DummyResponseModule(config,action_module)
    emotion_module = DummyEmotionModule(config,response_module)
    sensor_module = SensorModule(config,emotion_module)

    sensor_module.personSensor.show = show

    while True:
        sensor_module.update()
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
