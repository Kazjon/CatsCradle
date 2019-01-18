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

from imutils.object_detection import non_max_suppression
from imutils import paths
import imutils

personCount_ = 0

RESIZE_FINAL = 227
GENDER_LIST =['M','F']
AGE_LIST = ['(0, 2)','(4, 6)','(8, 12)','(15, 20)','(25, 32)','(38, 43)',\
    '(48, 53)','(60, 100)']

AGE_MAP = {'(0, 2)':"child",'(4, 6)':"child",'(8, 12)':"child",\
    '(15, 20)':"teen",'(25, 32)':"adult",'(38, 43)':"adult",\
    '(48, 53)':"adult",'(60, 100)':"senior"}
MAX_BATCH_SZ = 128

WHITE = [255, 255, 255]
TARGET_IMG_HEIGHT = 231
TARGET_IMG_WIDTH = 231

NUM_PEOPLE_TO_REMEMBER = 100
USE_TRIANGULATION = False


class PersonSensor(Sensor):
    """
    Use the BodyPartDetector to sense a person
    """
    def __init__(self, camera, tf_sess):
        Sensor.__init__(self, camera)

        #self.cv_path = cv_path
        self.bodyDetector = BodyPartDetector()
        self.show = False

        # TODO: Get proper standard values (mm)
        self.standardBodyWidth = 500
        self.standardBodyHeight = 1700
        self.standardFaceWidth = 200
        self.standardFaceHeight = 400

        # Create arrays of known face encodings and their names
        self.known_face_encodings = deque(maxlen=NUM_PEOPLE_TO_REMEMBER)
        self.known_face_numbers = deque(maxlen=NUM_PEOPLE_TO_REMEMBER)

        self.scaling_factor = 1.1
        self.frame_process_timer = 0
        self.frame_process_stride = 32 #corresponds to processing roughly 1 frame every 2 seconds

        self.face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.known_face_numbers_to_person_objects = {}

        self.undetected_persons = deque()
        self.undetected_persons_lock = Lock()

        #Person body detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


    def detectUndetectedPersons(self):
        #RUDE CARNIE DEFAULTS

        print("starting the process to detect people's age and gender...")

        gender_model_dir = "./age_and_gender_detection/pretrained_checkpoints/gender/"
        age_model_dir = "./age_and_gender_detection/pretrained_checkpoints/age/"
        # What processing unit to execute inference on
        device_id = '/device:CPU:0'
        # Checkpoint basename
        checkpoint = 'checkpoint'
        model_type = 'inception'

        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.0001)
        config = tf.ConfigProto(allow_soft_placement=True,
            gpu_options=gpu_options)

        with tf.Session(config=config) as sess:
            #Age detection model
            n_ages = len(AGE_LIST)
            age_model_fn = select_model(model_type)

            #Gender detection model
            n_genders = len(GENDER_LIST)
            gender_model_fn = select_model(model_type)

            print("initializing the model to detect age and gender")

            with tf.device(device_id):

                print "initializing the model to detect age and gender using ",\
                    str(device_id)
                images = tf.placeholder(tf.float32, [None, RESIZE_FINAL, \
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
                gender_logits = gender_model_fn("gender", n_genders, images,\
                    1, False)
                gender_checkpoint_path, global_step = \
                    get_checkpoint(gender_model_dir, requested_step, checkpoint)
                gender_vars = set(tf.global_variables()) - age_vars
                saver_gender = tf.train.Saver(list(gender_vars))
                saver_gender.restore(sess, gender_checkpoint_path)
                gender_softmax_output = tf.nn.softmax(gender_logits)

                coder = ImageCoder()

                writer = None

                print("starting the loop for detecting age and gender in each frame")

                while True:
                    self.undetected_persons_lock.acquire()
                    if len(self.undetected_persons):
                        (person_number, target_image) = \
                            self.undetected_persons.popleft()
                        self.undetected_persons_lock.release()
                        self.getAgeAndGender(person_number, target_image,\
                            sess, coder, images, writer, AGE_LIST, GENDER_LIST,\
                            age_softmax_output, gender_softmax_output)
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

        with person.genderLock:
            person.gender = gender
        with person.ageRangeLock:
            person.ageRange = ageRange

        # cv2.imwrite("/home/bill/Desktop/CatsCradle-fusion/imgs/age_gender_tests/%s-%s.jpg"%(gender, AGE_MAP[ageRange]), target_image)
        return AGE_MAP[ageRange], gender

    def getPersonsAndPersonBodies(self, previousPersons, previousPersonBodies,\
        getPersonBodies=True):

        if self.frame_process_timer == self.frame_process_stride:
            self.frame_process_timer = 0
        else:
            self.frame_process_timer += 1

        persons = []
        personBodies = []

        # Grab a single frame of video
        ret, frame = self.front_camera.read()
        # print(ret, frame)

        # Resize frame of video to 1/4 size for faster face recognition
        # processing
        small_frame = cv2.resize(frame, (0, 0),
                fx=(1/self.scaling_factor), fy=(1/self.scaling_factor))

        # Convert the image from BGR color (which OpenCV uses) to RGB color
        # (which face_recognition uses)
        # rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every one in every few frames of video to save time
        if self.frame_process_timer == 1:
            # Find all the faces and face encodings in the current frame of
            # video
            self.face_locations = face_recognition.face_locations\
                (rgb_small_frame, number_of_times_to_upsample=3, model="cnn")
            # self.face_locations = face_recognition.face_locations\
            #     (rgb_small_frame)
            self.face_encodings = face_recognition.face_encodings\
                (rgb_small_frame, self.face_locations)

            self.face_names = []
            for face_location, face_encoding in zip(self.face_locations,\
                self.face_encodings):
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces\
                    (self.known_face_encodings, face_encoding)
                name = "Unknown"
                (top, right, bottom, left) = face_location
                top = int(top)
                right = int(right)
                bottom = int(bottom)
                left = int(left)
                face_top = max(top - int((bottom-top)/2), 0)
                face_bottom = bottom + int((bottom-top)/2)
                face_left = max(left - int((right-left)/2), 0)
                face_right = right + int((right-left)/2)
                # NOTE FOR ISHAAN: Change to 1.5 and cut off if interfering
                # with next face
                face_close_up = small_frame[face_top:face_bottom,\
                    face_left:face_right, :]

                height, width, channels = face_close_up.shape
                vertical_padding = int(max(0, (TARGET_IMG_HEIGHT - height)/2))
                horizontal_padding = int(max(0, (TARGET_IMG_WIDTH - width)/2))

                #To experiment with zooming instead of adding padding/in
                # addition to adding padding
                # face_close_up = cv2.resize(face_close_up, (0, 0),
                #         fx=8.0, fy=8.0)

                # add padding so that image meets minimum image size requirement
                # of rude carnie
                face_close_up = cv2.copyMakeBorder(face_close_up,\
                    vertical_padding, vertical_padding, horizontal_padding, \
                    horizontal_padding, cv2.BORDER_CONSTANT, value=WHITE)

                # If a match was found in self.known_face_encodings,
                # just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    person_number = self.known_face_numbers[first_match_index]
                    name = "Person %d"%person_number
                    person = self.known_face_numbers_to_person_objects[person_number]
                    person.updateFace(self.get_2d_and_3d_coordinates_of_bb\
                        (face_location))
                    persons.append(person)
                else:
                    global personCount_
                    person = Person(frame, face_close_up, face_location,\
                        face_encoding, None, None, personCount_, None)
                    with self.undetected_persons_lock:
                        self.undetected_persons.append((personCount_,\
                            face_close_up))
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_numbers.append(personCount_)
                    self.known_face_numbers_to_person_objects[personCount_] =\
                        person
                    persons.append(person)
                    personCount_ += 1
                    # cv2.imwrite("/home/bill/Desktop/CatsCradle-fusion/imgs/age_gender_tests/%d.jpg"%personCount_, face_close_up)

                self.face_names.append(name)
                if getPersonBodies:
                    personBodies, frame = self.getPersonBodies(frame)

        else:
            persons = previousPersons
            personBodies = previousPersonBodies

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

        cv2.imshow('Video', frame)

        return persons, personBodies


    def getPersonBodies(self, frame):
        """
            Detects bodies.
            Params:
            frame (numpy.ndarray) : the frame to detect bodies in
            Returns a list of positions and the original frame with the bodies
            highlighted.
        """
        #Far away person detection
    	# detect people in the image
    	(rects, weights) = self.hog.detectMultiScale(frame, winStride=(4, 4),
    		padding=(8, 8), scale=1.05)

    	# draw the original bounding boxes
    	for (x, y, w, h) in rects:
    		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    	# apply non-maxima suppression to the bounding boxes using a
    	# fairly large overlap threshold to try to maintain overlapping
    	# boxes that are still people
    	rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    	pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

    	# draw the final bounding boxes
    	for (xA, yA, xB, yB) in pick:
    		cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

        return pick, frame

    def getPersonBodiesOnly(self, prevBackPersons):
        """
            This function returns a list of BackPerson objects corresponding
            to the people that the back camera sees.
        """

        back_persons = []

        if self.frame_process_timer == self.frame_process_stride:
            self.frame_process_timer = 0
        else:
            self.frame_process_timer += 1

        # Grab a single frame of video
        ret, frame = self.back_camera.read()

        # Process frames periodically
        if self.frame_process_timer == 1:
            now = time.localtime()
            print ("processing frame", "%s:%s:%s"%(now.tm_hour, now.tm_min, now.tm_sec))
            back_persons, frame = self.getFarawayPeoplePositions(frame)
            # convert each position to a BackPerson object

        else:
            back_persons = prevBackPersons

        cv2.imshow('Video', frame)

        return back_persons


    def _objective_p(self, point3d, point_2d_0, point_2d_1, projection_mtx_0,\
        projection_mtx_1):
        

    def get3dPointFrom2dPoint(self, point):
        # TODO: Experiment using triangulation or simply appending 1
        if USE_TRIANGULATION:

        else:
            return (point[0], point[1], 1)

if __name__ == '__main__':
    previousPersons = []
    prevBackPersons = []
    sensor = PersonSensor([], None)

    #Use filename for videos or 0 for the live camera
    #if you use 0 for the live camera, make sure its plugged in!
    # sensor.front_camera = cv2.VideoCapture(os.path.expanduser('/home/bill/Desktop/ishaanMovies/morePeople-converted.mp4'))
    sensor.front_camera = cv2.VideoCapture(0)
    # sensor.front_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    # sensor.front_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)

    # sensor.back_camera = cv2.VideoCapture(0)

    camera_to_release = sensor.front_camera


    t = Thread(target=sensor.detectUndetectedPersons)
    t.start()
    # time.sleep(7) # sleep to allow the tensor flow/rude carnie stuff to load
    while True:
        persons = sensor.getPersons(previousPersons)
        print "Num persons =", len(persons)
        for person in persons:
            print(person)
        previousPersons = persons

        # back_persons = sensor.getBackPersons(prevBackPersons)
        # print "Num back persons =", len(back_persons)

        # Hit 'q' on the keyboard to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            camera_to_release.release()
            cv2.destroyAllWindows()
            t._Thread_stop()
            break
