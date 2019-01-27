import time
from threading import Thread

from SensorModule import SensorModule
from EmotionModule import EmotionModule
from ResponseModule import ResponseModule
from ActionModule import ActionModule

from PersonSensor import PersonSensor
from Audience import Audience

import tensorflow as tf

import cv2

import sys

from multiprocessing import Process

if __name__ == "__main__":
    actionModule = ActionModule(dummy="--dummyAction" in sys.argv)
    config = tf.ConfigProto(allow_soft_placement=True)

    print('Loaded Action Module...\n')

    with tf.Session(config=config) as tf_sess:

        response_module = ResponseModule(actionModule)

        print('Loaded Response Module...\n')

        emotion_module = EmotionModule(response_module, visualise=True)

        print('Loaded Emotion Module...\n')

        perceptionMode = "full"
        if "--dummyPerception" in sys.argv:
            perceptionMode = "dummy"
        elif "--fastPerception" in sys.argv:
            perceptionMode = "fast"

        sensor_module = SensorModule({"cv_path": '.', "tf_sess": tf_sess,"perception_mode":perceptionMode}, emotion_module)
        camera = cv2.VideoCapture(0)
        sensor_module.personSensor = PersonSensor(camera, tf_sess)
        sensor_module.personSensor.video_capture = camera
        sensor_module.audience = Audience(sensor_module.personSensor)
        sensor_module.loadReactors()

        print('Loaded Sensor Module...\n')

        person_detector_thread = Thread(target=sensor_module.personSensor.detectUndetectedPersons)
        person_detector_thread.setDaemon(True)
        person_detector_thread.start()
#        person_detector_process = Process(target=sensor_module.personSensor.detectUndetectedPersons)
#        person_detector_process.start()

        print('Loaded Person Detector...\n')

        while True:

            sensor_module.update()

            # Hit 'q' on the keyboard to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("stopping...")
#                person_detector_process.terminate()
                sensor_module.cleanup()
                cv2.destroyAllWindows()
                break
