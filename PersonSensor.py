
import cv2
from image_processing import predictor
from imutils.face_utils import rect_to_bb
import numpy as np

from multiprocessing import Process, Queue

from datetime import datetime

import copy
import time
import logging

import Person

QUEUE_MAX_MESSAGES = 10
FRAME_PROCESSING_STRIDE = 1

class PersonSensor():
    """
    Class used to detect faces and bodies in front of the marionette and
    bodies behind the marionette.
    """
    def __init__(self):
        
        # a public variable to reference the camera (later to load)
        self.front_camera = None
        self.back_camera = None
        
        # The means to transfer frames to the prediction process
        self._frames_to_process_queue = Queue(QUEUE_MAX_MESSAGES)
        # The means to transfer back prediction results from the prediction process
        self._prediction_results_queue = Queue(QUEUE_MAX_MESSAGES)
        
        # bookkeeping the frames to process
        self._frame_counter = 0
        # bookkeeping the latest predictions
        self._latest_predictions = []
        # bookkeeping the last camera frame
        self._last_back_camera_frame = None
    
        # initialize the prediction process
        self._prediction_process = Process(target=predictor.process_image,
                                     args=(self._frames_to_process_queue, self._prediction_results_queue))
        self._prediction_process.daemon = True
        self._prediction_process.start()
    
        # history of face encodings.
        self._face_encodings = []
        self._person_objects = []
        self._last_id = 0
    
    
    # deconstructor
    def release(self):
        self._frames_to_process_queue.close()
        self._prediction_results_queue.close()
        self._prediction_process.terminate()
    

    def load_camera(self, front_camera, back_camera):
        self.front_camera = front_camera
        self.back_camera = back_camera
    
        if not back_camera is None:
            self.backCameraMaxX = self.back_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.backCameraMaxY = self.back_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    

    # the 'update' method
    def getPersonsAndPersonBodies(self, previousPersons, previousPersonBodies):
        """
        Get a list of Person objects and a list of PersonBody objects by processing one frame from the self.front_camera.
        This function should be called from the main thread since it displays the camera frame on a window.
        """
        
        # if no front camera return early
        if self.front_camera is None:
            return previousPersons, previousPersonBodies
        
        # read one frame from the camera
        ret, frame = self.front_camera.read()
        self._frame_counter = self._frame_counter + 1

        if self._frame_counter == FRAME_PROCESSING_STRIDE:
            # call to process the frame
            try:
                # put a message containing the frame to process for
                self._frames_to_process_queue.put({'frame': frame, 'time': datetime.now()}, False)
            except:
                # if the queue is full continue
                pass
            self._frame_counter = 0

        # update prediction results for display (only if new results available)
        try:
            results = self._prediction_results_queue.get(False)
            # prediction results is a list of tuples that each contains the following
            # index 0. face_rect of a face in the last frame,
            # index 1. ages of a face in the last frame,
            # index 2. genders of a face in the last frame,
            # index 3. face_descriptors of a face in the last frame,
            # index 4. probabilities of 100 bins for age of a face in the last frame,
            # index 5. a list probabilities of gender of a face in the last frame.
            #          The first item is the proba for female and the second item for male.
            # the length of prediction results is equal to the number of detected faces in the last frame.
            self._latest_predictions = results
        except:
            # no new results -- return early
            return previousPersons, previousPersonBodies

        # display frame
        self.display_front_frame(frame, self._latest_predictions)
        
        persons = []
        for prediction in self._latest_predictions:
            # prediction is a tuple containing prediction info for ONE detected face
            face_rect = prediction[0]
            face_position = self.get2dAnd3dCoordsFromLocation(face_rect.top(), face_rect.right(),
                                                              face_rect.bottom(), face_rect.left())
            face_encoding = prediction[3]
            age_probas = self.get_age_probas(prediction[4])
            gender_probas = self.get_gender_probas(prediction[5])
            
            # compare the face encoding to the history of encodings
            distances = np.array([100])
            if len(self._face_encodings) > 0:
                distances = np.linalg.norm(np.array(self._face_encodings) - np.array(face_encoding), axis=1, ord=2)
            if True in (distances < 0.6):
                # found a match in history -- return the person object
                person = self._person_objects[(distances < 0.6).argmax()]
                person.reappear()
                person.update_age_gender(age_probas, gender_probas)
                person.updateFace(face_position)
                persons.append(person)
            else:
                # new person
                self._face_encodings.append(face_encoding)
                person = Person.Person(age_probas, gender_probas, self._last_id, face_position)
                persons.append(person)
                self._person_objects.append(person)
                self._last_id += 1
        
        personBodies = previousPersonBodies
        
#        for person in persons:
#            print(person)

        return persons, personBodies

    
    def update_back_camera(self):
        # return early if the camera is not setup
        if self.back_camera is None:
            return False
    
        # read a frame from the back camera
        ret, frame = self.back_camera.read()
        
        motion_amount_right = 0
        motion_amount_left = 0
        # if we have a previous frame calculate the motion
        if not self._last_back_camera_frame is None:
            # this code is adopted from here: https://software.intel.com/en-us/node/754940
            # get the difference between the current frame and the last frame
            dist = frame_distance(frame, self._last_back_camera_frame)
            mod = cv2.GaussianBlur(dist, (9,9), 0)
            _, threshold = cv2.threshold(mod, 100, 255, 0)
            left_threshold = threshold[:,:int(self.backCameraMaxX/2)]
            right_threshold = threshold[:,int(self.backCameraMaxX/2):]
            
            _, stdev_right = cv2.meanStdDev(right_threshold)
            _, stdev_left = cv2.meanStdDev(left_threshold)
            
            motion_amount_right = stdev_right[0][0]
            motion_amount_left = stdev_left[0][0]
#            print(str(motion_amount_left) + ", " + str(motion_amount_right))

            # display
            cv2.namedWindow('Back Camera -- Motion Detector', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Back Camera -- Motion Detector', 400, int(0.56*400))
            cv2.imshow('Back Camera -- Motion Detector', threshold)

        self._last_back_camera_frame = frame
#        cv2.namedWindow('Back Camera', cv2.WINDOW_NORMAL)
#        cv2.resizeWindow('Back Camera', 300, int(0.56*300))
#        cv2.imshow('Back Camera', frame)
        return motion_amount_left, motion_amount_right
    
    
    def get_age_probas(self, age_probas):
        age_probas = {'child': age_probas[0],
                      'adult': age_probas[1],
                      'senior': age_probas[2]}
        return age_probas
    
    
    def get_gender_probas(self, gender_probas):
        gender_probas = {'F': gender_probas[0], 'M': gender_probas[1]}
        return gender_probas
    
    
    def display_front_frame(self, frame, prediction_results):
        """
        Display frame on cv2 window.
        
        Args:
            frame (?): cv2 frame.
            prediction_results (list): a list of tuples. Each item corresponds to
                a face and has (face_rect, age, gender).
        """

        if frame is None:
            return
        
        height, width = frame.shape[:2]
        img_ratio = float(height) / float(width)
        w_scale_factor = float(width) / float(predictor.PROCESSING_SIZE)
        h_scale_factor = float(height) / (predictor.PROCESSING_SIZE * img_ratio)
        
        # write the last person id
        cv2.putText(frame, str(self._last_id) + ' - ' + str(len(prediction_results)), (10, 25), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 1)

        if len(prediction_results) > 0:
            # write the results on the frame
            for face_rect, age, gender, _, _, _ in prediction_results:
                # convert dlib.rectangle to regular bounding box
                (x, y, w, h) = rect_to_bb(face_rect)
                # re-scale based on predictor.PROCESSING_SIZE
                x = int(x * w_scale_factor)
                y = int(y * h_scale_factor)
                w = int(w * w_scale_factor)
                h = int(h * h_scale_factor)
                # draw rectangle on the frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (179, 178, 179), 2)
                # draw a filled rectangle to write text
                cv2.rectangle(frame, (x, y+h - 35), (x+w, y+h), (212, 211, 212), cv2.FILLED)
                # write age and gender if provided
                if not age is None and not gender is None:
                    text = predictor.GENDER_MAP[gender] + "(" + predictor.AGE_MAP[int(age)] + ")"
                    cv2.putText(frame, text, (x+2, y+h-6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 1)

        # display the frame
        cv2.namedWindow('Front Camera', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Front Camera', predictor.PROCESSING_SIZE, int(img_ratio*predictor.PROCESSING_SIZE))
        cv2.imshow('Front Camera', frame)


    def get2dAnd3dCoordsFromLocation(self, top, right, bottom, left):

        top_left_2d = (left, top)
        top_right_2d = (right, top)
        bottom_right_2d = (right, bottom)
        bottom_left_2d = (left, bottom)
        center_2d = ((bottom-top)/2.0, (right-left)/2.0)

        return top_left_2d, top_right_2d, bottom_right_2d, bottom_left_2d, center_2d


### Static methods

def frame_distance(frame1, frame2):
    """outputs pythagorean distance between two frames"""
    frame1_32 = np.float32(frame1)
    frame2_32 = np.float32(frame2)
    diff32 = frame1_32 - frame2_32
    norm32 = np.sqrt(diff32[:,:,0]**2 + diff32[:,:,1]**2 + diff32[:,:,2]**2)/np.sqrt(255**2 + 255**2 + 255**2)
    dist = np.uint8(norm32*255)
    return dist
