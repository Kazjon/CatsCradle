#Run in Python2.7
#GENERAL IMPORTS
#TODO: standardize camelCase vs underscored var names
import os
import sys
import numpy as np
from collections import deque

#FACE RECOGNITION IMPORTS
import cv2

_FACE_RECOGNITION = False

try:
    import face_recognition
    _FACE_RECOGNITION = True
except ImportError:
    print "ERROR: Unable to load face_recognition module."
    print "Run without face recognition..."

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
from PersonBody import *

from imutils.object_detection import non_max_suppression
from imutils import paths
import imutils

from scipy.optimize import minimize
from scipy.linalg import rq

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

# This is the minimum height and width for an image sent to rude carnie for
# an age and gender guess
TARGET_IMG_HEIGHT = 231
TARGET_IMG_WIDTH = 231

# the marionette will recoginze up to the last NUM_PEOPLE_TO_REMEMBER people
# it has seen
NUM_PEOPLE_TO_REMEMBER = 1000

# This determines whether a triangulation algorithm is used to determine the
# 3d coordinates of a person or person's face. It is set to False by default
# because it doesn't work well when there is only one camera.
USE_TRIANGULATION = False

# This variable is used in the getAgeAndGender function. It is explained there
SECOND_PROB_THRESHOLD = 0.3


class PersonSensor(Sensor):
    """
    Class used to detect faces and bodies in front of the marionette and
    bodies behind the marionette.
    """
    def __init__(self, camera, tf_sess, frame_division_factor=4, face_detection_frameskip=8):
        Sensor.__init__(self, camera)
        print "stride",face_detection_frameskip

        #self.cv_path = cv_path
        self.bodyDetector = BodyPartDetector()
        self.show = False

        # Create arrays of known face encodings and their names
        self.known_face_encodings = deque(maxlen=NUM_PEOPLE_TO_REMEMBER)
        self.known_face_numbers = deque(maxlen=NUM_PEOPLE_TO_REMEMBER)

        # the image is divided by this number when reducing its size to speed up
        # processing
        self.scaling_factor = frame_division_factor

        self.front_frame_process_timer = 0
        self.back_frame_process_timer = 0

        # 16 corresponds to processing roughly 1 frame every second
        self.frame_process_stride = face_detection_frameskip

        self.face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.known_face_numbers_to_person_objects = {}

        self.undetected_persons = deque()
        self.undetected_persons_lock = Lock()

        #Person body detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.front_camera = camera
        self.back_camera = None

        self.initialised = False


    def detectUndetectedPersons(self):
        """
            On a loop, checks if there are faces added to the queue whose age
            and gender haven't been guessed yet. If there are any such faces,
            guesses their age and gender and updates the necessary Person object
            with this information.
        """
        print "starting the process to detect people's age and gender..."

        gender_model_dir = "./age_and_gender_detection/pretrained_checkpoints/gender/"
        age_model_dir = "./age_and_gender_detection/pretrained_checkpoints/age/"

        # What processing unit to execute inference on
        # use CPU to free up GPU for face detection
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

            print "initializing the model to detect age and gender"

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

                print "starting the loop for detecting age and gender in each frame"
                self.initialised = True

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
        """
            Guesses the age and gender of the person in target_image and updates
            the Person object pointed to by person_number with this information
        """

        (age_range, age_range_prob), (age_range_guess_2, age_range_guess_2_prob) =\
            classify_one_multi_crop(sess, age_list, age_softmax_output, coder,\
            images, target_image, writer)
        (gender, gender_prob) = classify_one_multi_crop(sess, gender_list,\
            gender_softmax_output, coder, images, target_image, writer)

        first_age_guess = AGE_MAP[age_range]
        second_age_guess = AGE_MAP[age_range_guess_2]
        final_age_guess = first_age_guess

        # This block of logic works as follows:
        # If the second most likely age guess is a different age category than
        # the first, and the second guess has a probability greater than
        # SECOND_PROB_THRESHOLD, then use it as the final guess.

        if first_age_guess != second_age_guess and age_range_guess_2_prob > SECOND_PROB_THRESHOLD:
            final_age_guess = second_age_guess
            # print('first_age_guess', first_age_guess)
            # print('second_age_guess', second_age_guess)
            # print('final_age_guess', final_age_guess)

        # cv2.imwrite("/home/bill/Desktop/CatsCradle-fusion/imgs/age_gender_tests/%s-%s.jpg"%(gender, AGE_MAP[ageRange]), target_image)
        person = self.known_face_numbers_to_person_objects[person_number]

        with person.genderLock:
            person.gender = gender
        with person.ageRangeLock:
            person.ageRange = final_age_guess

    def getPersonsAndPersonBodies(self, previousPersons, previousPersonBodies,\
        getPersonBodies=True, cnn_detection=False):
        """
        Returns a list of Person objects and a list of PersonBody objects
        as seen by the front camera of the marionette.

        """
        if self.front_frame_process_timer == self.frame_process_stride:
            self.front_frame_process_timer = 0
        else:
            self.front_frame_process_timer += 1

        persons = []
        personBodies = previousPersonBodies

        # Grab a single frame of video
        ret, frame = self.front_camera.read()
        # print(ret, frame)

        # Resize frame of video to 1/4 size for faster face recognition
        # processing
        small_frame = cv2.resize(frame, (0, 0),
                fx=(1./self.scaling_factor), fy=(1./self.scaling_factor))

        # Convert the image from BGR color (which OpenCV uses) to RGB color
        # (which face_recognition uses)
        # rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every one in every few frames of video to save time
        if _FACE_RECOGNITION and self.front_frame_process_timer == 1:
            # Find all the faces and face encodings in the current frame of
            # video
            if cnn_detection:
                self.face_locations = face_recognition.face_locations\
                    (rgb_small_frame, number_of_times_to_upsample=3, model="cnn")
            else:
                self.face_locations = face_recognition.face_locations\
                    (rgb_small_frame)
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
                # Note after testing zoom, I found it to worsen the guess quality
                # (even a tiny zoom of 1.1)
                # face_close_up = cv2.resize(face_close_up, (0, 0),
                #         fx=2.0, fy=2.0)

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
                    person.reappear()
                    person.updateFace(self.get2dAnd3dCoordsFromLocation\
                        (top, right, bottom, left))
                    persons.append(person)
                else:
                    global personCount_
                    # print('face_location', face_location)
                    face_top_left_2d, face_top_right_2d, face_bottom_right_2d,\
                        face_bottom_left_2d, face_center_2d, face_top_left_3d,\
                        face_top_right_3d, face_bottom_right_3d,\
                        face_bottom_left_3d, face_center_3d =\
                        self.get2dAnd3dCoordsFromLocation(top, right,\
                            bottom, left)

                    person = Person(frame, face_close_up, face_encoding,\
                        None, None, personCount_, None, face_top_left_2d,\
                            face_top_right_2d, face_bottom_right_2d,\
                            face_bottom_left_2d, face_center_2d, face_top_left_3d,\
                            face_top_right_3d, face_bottom_right_3d,\
                            face_bottom_left_3d, face_center_3d)

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
                personBodies = self.getPersonBodies(frame)

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

            # Draw a red box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0,\
                255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0,\
                0, 0), 1)

        for personBody in personBodies:
            # Draw a green box around the body
            cv2.rectangle(frame, (personBody.body_top_left_2d),\
                (personBody.body_bottom_right_2d), (255, 0, 0), 2)

        name = 'Front Video'
        cv2.moveWindow(name, 800, 0)
        smallerFrame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow(name, smallerFrame)

        return persons, personBodies


    def getPersonBodies(self, frame):
        """
            Detects bodies.
            Params:
            frame (numpy.ndarray) : the frame to detect bodies in
            Returns a list of PersonBody objects
        """
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
        personBodies = []
    	for (left, top, right, bottom) in pick:
            body_top_left_2d, body_top_right_2d,\
                body_bottom_right_2d, body_bottom_left_2d, body_center_2d,\
                body_top_left_3d, body_top_right_3d, body_bottom_right_3d,\
                body_bottom_left_3d, body_center_3d =\
                self.get2dAnd3dCoordsFromLocation(top, right, bottom, left,\
                scale=False)
            personBodies.append(PersonBody(body_top_left_2d, body_top_right_2d,\
                body_bottom_right_2d, body_bottom_left_2d, body_center_2d,\
                body_top_left_3d, body_top_right_3d, body_bottom_right_3d,\
                body_bottom_left_3d, body_center_3d))

        return personBodies

#    def getPersonBodiesOnly(self, previousPersonBodiesBehindMarionette):
        """
            This function returns a list of PersonBody objects detected by the
            back camera.
        """

#        personBodiesBehindMarionette = previousPersonBodiesBehindMarionette

 #       if self.back_frame_process_timer == self.frame_process_stride:
 #           self.back_frame_process_timer = 0
 #       else:
 #           self.back_frame_process_timer += 1

        # Grab a single frame of video
 #       ret, frame = self.back_camera.read()

        # Process frames periodically
 #       if self.back_frame_process_timer == 1:
 #           personBodiesBehindMarionette = self.getPersonBodies(frame)


 #       for personBody in personBodiesBehindMarionette:
 #           cv2.rectangle(frame, (personBody.body_top_left_2d),\
 #               (personBody.body_bottom_right_2d), (0, 255, 0), 2)

 #       cv2.imshow('Back Video', frame)

 #       return personBodiesBehindMarionette


    def _multiply_points(self, p1, p2):
        return np.dot(p1, p2)


    def _objective_p(self, point3d, point_2d_0, point_2d_1, projection_mtx_0,\
        projection_mtx_1):
        left_term0 = np.square(point_2d_0[0] - self._multiply_points\
            (projection_mtx_0[0], point3d)/self._multiply_points\
            (projection_mtx_0[-1], point3d))
        right_term0 = np.square(point_2d_0[1] - self._multiply_points\
            (projection_mtx_0[1], point3d)/self._multiply_points\
            (projection_mtx_0[-1], point3d))
        left_term1 = np.square(point_2d_1[0] - self._multiply_points\
            (projection_mtx_1[0], point3d)/self._multiply_points\
            (projection_mtx_1[-1], point3d))
        right_term1 = np.square(point_2d_1[1] - self._multiply_points\
            (projection_mtx_1[1], point3d)/self._multiply_points\
            (projection_mtx_1[-1], point3d))

        return left_term0 + right_term0 + left_term1 + right_term1


    def get3dPointFrom2dPoint(self, point_cam_0, point_cam_1=None):
        """
            This function can either triangulate a 3D point estimate based on
            2 different camera's views of a given object or simply returns a
            3d point estimate for where the marionette should look to see this
            point based on the point's 2d coordinates.
        """
        # TODO: Experiment using triangulation or simply appending 1
        if USE_TRIANGULATION:
            #for now use point_cam_1 = point_cam_0
            point_cam_1 = point_cam_0
            projection_mtx_0 = numpy.load\
                ("camera_calibration/projection_mtx_0.npy")
            projection_mtx_1 = numpy.load\
                ("camera_calibration/projection_mtx_1.npy")
            point3d = np.ones((4,))
            point3d = minimize(self._objective_p, point3d, args=(point_cam_0,\
                point_cam_1, projection_mtx_0, projection_mtx_1),\
                method="Powell").x
            point3d = (point3d[0]/point3d[3], point3d[1]/point3d[3],\
                point3d[2]/point3d[3])

            return point3d
        else:
            #NOTE FROM ISHAAN TO ALEX: For now I just append a 1 in the z-coordinate
            # of the 2d point to convert it to 3d. Once I have the entire marionette
            # pipeline to play with, I will refine this so that based on where the camera
            # is located, and based on the 2d points it sees, we can figure out exactly
            # where the marionette should look in its own 3d coordinate system.
            return (point_cam_0[0], point_cam_0[1], 1)


    def get2dAnd3dCoordsFromLocation(self, top, right, bottom, left,\
        scale=True):

        if scale:
            top = int(top*self.scaling_factor)
            right = int(right*self.scaling_factor)
            bottom = int(bottom*self.scaling_factor)
            left = int(left*self.scaling_factor)

        top_left_2d = (left, top)
        top_right_2d = (right, top)
        bottom_right_2d = (right, bottom)
        bottom_left_2d = (left, bottom)
        center_2d = ((bottom-top)/2.0, (right-left)/2.0)

        top_left_3d = self.get3dPointFrom2dPoint(top_left_2d)
        top_right_3d = self.get3dPointFrom2dPoint(top_right_2d)
        bottom_right_3d = self.get3dPointFrom2dPoint(bottom_right_2d)
        bottom_left_3d = self.get3dPointFrom2dPoint(bottom_left_2d)
        center_3d = self.get3dPointFrom2dPoint(center_2d)

        return top_left_2d, top_right_2d, bottom_right_2d,\
            bottom_left_2d, center_2d, top_left_3d,\
            top_right_3d, bottom_right_3d, bottom_left_3d,\
            center_3d

if __name__ == '__main__':
    previousPersons = []
    previousPersonBodies = []
    previousPersonBodiesBehindMarionette = []
    sensor = PersonSensor([], None)

    #Use filename for videos or 0 for the live camera
    #if you use 0 for the live camera, make sure its plugged in!
    # sensor.front_camera = cv2.VideoCapture(os.path.expanduser('/home/bill/Desktop/ishaanMovies/morePeople-converted.mp4'))
    sensor.front_camera = cv2.VideoCapture(0)
    # sensor.front_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    # sensor.front_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)

    # sensor.back_camera = sensor.front_camera
    # sensor.back_camera = cv2.VideoCapture(0)


    t = Thread(target=sensor.detectUndetectedPersons)
    t.start()
    time.sleep(7) # sleep to allow the tensor flow/rude carnie stuff to load
    while True:
        persons, personBodies = sensor.getPersonsAndPersonBodies(previousPersons,\
            previousPersonBodies, False)
        previousPersons = persons
        previousPersonBodies = personBodies

        # if len(persons):
        #     print "Num persons =", len(persons)
        # if len(personBodies):
        #     print "Num person bodies =", len(personBodies)
        for person in persons:
            print(person)

        # personBodiesBehindMarionette = sensor.getPersonBodiesOnly\
        #     (previousPersonBodiesBehindMarionette)
        # previousPersonBodiesBehindMarionette = personBodiesBehindMarionette
        #
        # if len(personBodiesBehindMarionette):
        #     print "Num persons behind marionette =", len(personBodiesBehindMarionette)

        # Hit 'q' on the keyboard to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            if sensor.front_camera:
                sensor.front_camera.release()
            if sensor.back_camera:
                sensor.back_camera.release()
            cv2.destroyAllWindows()
            t._Thread__stop()
            break

class DummyPersonSensor(Sensor):

    def __init__(self):
        raise NotImplementedError("Dummy perception (with keyboard entries for generating random persons) has not been implemented.")
