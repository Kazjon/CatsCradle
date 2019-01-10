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

if __name__ == "__main__":
    
    actionModule = ActionModule()
    config = tf.ConfigProto(allow_soft_placement=True)
    
    raw_input('Loaded Action Module. Hit Enter to Continue...\n')
    
    with tf.Session(config=config) as tf_sess:
    
        response_module = ResponseModule(actionModule)
        
        raw_input('Loaded Response Module. Hit Enter to Continue...\n')
        
        emotion_module = EmotionModule(response_module, visualise=True)
        
        raw_input('Loaded Emotion Module. Hit Enter to Continue...\n')
        
        sensor_module = SensorModule({"cv_path": '.', "tf_sess": tf_sess}, emotion_module)
        camera = cv2.VideoCapture(0)
        sensor_module.personSensor = PersonSensor(camera, tf_sess)
        sensor_module.personSensor.video_capture = camera
        sensor_module.audience = Audience(sensor_module.personSensor)
        sensor_module.loadReactors()
        
        raw_input('Loaded Sensor Module. Hit Enter to Continue...\n')

        while True:
        
            sensor_module.personSensor.getPersons([])

            # Hit 'q' on the keyboard to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                sensor.video_capture.release()
                cv2.destroyAllWindows()
                break

