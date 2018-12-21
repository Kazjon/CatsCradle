#Run in Python2.7
#GENERAL IMPORTS
#TODO: standardize camelCase vs underscored var names
import os
import sys
import numpy as np
from collections import deque

#FACE RECOGNITION IMPORTS
import cv2
import face_recognition

#RUDE CARNIE IMPORTS
sys.path.append("age_and_gender_detection")
# import tensorflow as tf
from model import select_model, get_checkpoint
from utils import *
from guess import classify_one_multi_crop

from MathUtils import *
from BodyPartDetector import *
from Person import *
from Sensor import *
from threading import Lock, Thread
import time

personCount_ = 0

RESIZE_FINAL = 227
GENDER_LIST =['M','F']
AGE_LIST = ['(0, 2)','(4, 6)','(8, 12)','(15, 20)','(25, 32)','(38, 43)',\
    '(48, 53)','(60, 100)']
MAX_BATCH_SZ = 128

#TODO: 1 figure out how to call rude carnie
# 2 - figure out relationship with previousPersons
# 3 - document
# 4 - push and write email to Kaz/Alex

class PersonSensor(Sensor):
    """
    Use the BodyPartDetector to sense a person
    """
    def __init__(self, cameras):
        Sensor.__init__(self, cameras)

        self.bodyDetector = BodyPartDetector()
        self.show = False

        # TODO: Get proper standard values (mm)
        self.standardBodyWidth = 500
        self.standardBodyHeight = 1700
        self.standardFaceWidth = 200
        self.standardFaceHeight = 300
        self.scaling_factor = 2
        self.skip_this_frame = False
        # Create arrays of known face encodings and their names
        self.known_face_encodings = deque(maxlen=50)
        self.known_face_numbers = deque(maxlen=50)
        self.scaling_factor = 1.5
        self.process_this_frame = True
        self.video_capture = cv2.VideoCapture(0)
        # self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        # self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        # self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 420)
        # self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 680)
        self.face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.known_face_numbers_to_person_objects = {}
        self.undetected_persons = deque()
        self.undetected_persons_lock = Lock()

    def detectUndetectedPersons(self):
        #RUDE CARNIE DEFAULTS
        gender_model_dir = "/home/bill/Desktop/ish/CatsCradle/age_and_gender_detection/" +\
            "pretrained_checkpoints/gender/"
        age_model_dir = "/home/bill/Desktop/ish/CatsCradle/age_and_gender_detection/" +\
            "pretrained_checkpoints/age/"
        # What processing unit to execute inference on
        device_id = '/gpu:0'
        # Checkpoint basename
        checkpoint = 'checkpoint'
        model_type = 'inception'

        config = tf.ConfigProto(allow_soft_placement=True)

        with tf.Session(config=config) as sess:
            #Age detection model
            n_ages = len(AGE_LIST)
            age_model_fn = select_model(model_type)

            #Gender detection model
            n_genders = len(GENDER_LIST)
            gender_model_fn = select_model(model_type)

            with tf.device(device_id):
                images = tf.placeholder(tf.float32, [None, RESIZE_FINAL,\
                    RESIZE_FINAL, 3])
                requested_step = None
                init = tf.global_variables_initializer()

                #age model
                age_logits = age_model_fn("age", n_ages, images, 1, False)
                age_checkpoint_path, global_step = get_checkpoint(age_model_dir,\
                        requested_step, checkpoint)
                age_vars = set(tf.global_variables())
                saver_age = tf.train.Saver(list(age_vars))
                saver_age.restore(sess, age_checkpoint_path)
                age_softmax_output = tf.nn.softmax(age_logits)

                #gender_model
                gender_logits = gender_model_fn("gender", n_genders, images, 1,\
                    False)
                gender_checkpoint_path, global_step = get_checkpoint\
                    (gender_model_dir, requested_step, checkpoint)
                gender_vars = set(tf.global_variables()) - age_vars
                saver_gender = tf.train.Saver(list(gender_vars))
                saver_gender.restore(sess, gender_checkpoint_path)
                gender_softmax_output = tf.nn.softmax(gender_logits)

                coder = ImageCoder()

                writer = None

                while True:
                    self.undetected_persons_lock.acquire()
                    if len(self.undetected_persons):
                        (person_number, target_image) = self.undetected_persons.popleft()
                        self.undetected_persons_lock.release()
                        self.getAgeAndGender(person_number, target_image, sess, coder, images,\
                                writer, AGE_LIST, GENDER_LIST, age_softmax_output,\
                                gender_softmax_output)
                    else:
                        self.undetected_persons_lock.release()




    def getAgeAndGender(self, person_number, target_image, sess, coder, images,\
        writer, age_list, gender_list, age_softmax_output,\
        gender_softmax_output):
        (ageRange, ageRange_prob) = classify_one_multi_crop(sess, age_list,\
            age_softmax_output, coder, images, target_image,\
            writer)
        (gender, gender_prob) = classify_one_multi_crop(sess,\
            gender_list, gender_softmax_output, coder,\
            images, target_image, writer)

        person = self.known_face_numbers_to_person_objects[person_number]
        print(person)
        with person.genderLock:
            person.gender = gender
        with person.ageRangeLock:
            person.ageRange = ageRange
        print(person)

    def getPersons(self, previousPersons):
        self.process_this_frame = not self.process_this_frame
        persons = []
        # Grab a single frame of video
        ret, frame = self.video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition
        # processing
        small_frame = cv2.resize(frame, (0, 0), \
            fx=(1/self.scaling_factor), fy=(1/self.scaling_factor))

        # Convert the image from BGR color (which OpenCV uses) to RGB color
        # (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if self.process_this_frame:
            # Find all the faces and face encodings in the current frame of
            # video
            self.face_locations = face_recognition.face_locations\
                (rgb_small_frame)
                #(rgb_small_frame, model="cnn")
            self.face_encodings = face_recognition.face_encodings\
                (rgb_small_frame, self.face_locations)

            self.face_names = []
            for face_encoding in self.face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces\
                    (self.known_face_encodings, face_encoding)
                name = "Unknown"

                # If a match was found in self.known_face_encodings,
                # just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    person_number = self.known_face_numbers[first_match_index]
                    name = "Person %d"%person_number
                    persons.append(self.known_face_numbers_to_person_objects\
                        [person_number])
                else:
                    global personCount_
                    # age, gender = self.getAgeAndGender(sess, gender_list,\
                    #     age_list, gender_softmax_output, age_softmax_output,\
                    #     coder, images, small_frame, writer)
                    person = Person(frame, face_encoding, personCount_, None)
                    with self.undetected_persons_lock:
                        self.undetected_persons.append((personCount_,\
                            small_frame))
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_numbers.append(personCount_)
                    self.known_face_numbers_to_person_objects[personCount_] =\
                        person
                    persons.append(person)
                    personCount_ += 1

                self.face_names.append(name)
        else:
            persons = previousPersons

        # Display the results
        for (top, right, bottom, left), name in zip(self.face_locations,\
            self.face_names):
            # Scale back up face locations since the frame we detected in
            # was scaled to 1/4 size
            top = int(top*self.scaling_factor)
            right = int(right*self.scaling_factor)
            bottom = int(bottom*self.scaling_factor)
            left = int(left*self.scaling_factor)

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0,\
                255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0,\
                0, 0), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)

        return persons



################################################################################
########################### WITHOUT RUDE CARNIE ################################
################################################################################

# if __name__ == '__main__':
#     # Tests
#     sensor = PersonSensor([], None, None, None, None, None, None, None, None)
#     sensor.show = True
#
#     previousPersons = []
#     Thread(target=sensor.detectUndetectedPersons).start()
#     while True:
#         persons = sensor.getPersons(previousPersons)
#         print "Num persons =", len(persons)
#         previousPersons = persons
#
#         # Hit 'q' on the keyboard to quit
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             sensor.video_capture.release()
#             cv2.destroyAllWindows()
#             break

################################################################################
########################### WITH RUDE CARNIE ################################
################################################################################

if __name__ == '__main__':
    previousPersons = []
    sensor = PersonSensor([])
    sensor.show = True
    Thread(target=sensor.detectUndetectedPersons).start()
    time.sleep(10) # sleep to allow the tensor flow/rude carnie stuff to load
    while True:
        persons = sensor.getPersons(previousPersons)
        print "Num persons =", len(persons)
        for person in persons:
            print(person)
        previousPersons = persons

        # Hit 'q' on the keyboard to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sensor.video_capture.release()
            cv2.destroyAllWindows()
            break
