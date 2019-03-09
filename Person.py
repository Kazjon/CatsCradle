import cv2
import numpy

from MathUtils import *
from Camera import *
from BodyPartDetector import *
from sets import Set
from collections import deque
from scipy.spatial import distance
from threading import Lock

import time

INTEREST_DECAY = 0.99
FACE_HISTORY_LENGTH = 5
INTEREST_DECAY_INTERVAL = 0.1 #seconds between applying INTEREST_DECAY
NEW_INTERACTION_TIMEOUT = 15 #seconds someone can go missing before their movement history is thrown out
# the maximum number of samples that we need to have before we can predict age/gender accurately
MAX_NUM_SAMPLES = 20

TAG_MEMORY_SPAN = 10 # person labels older than this much seconds are not active anymore

def face_size(face_top_left, face_bottom_right):
    """
        Gives the size of a given face bounding box. Typically would use 2d
        coordinates for this, but can use 3d too.
    """
    return distance.euclidean([face_top_left[0],face_top_left[1]],\
        [face_bottom_right[0],face_bottom_right[1]])


class Person:
    """Class to handle a person parameters"""

    def __str__(self):
        return "Person " + str(self.id) + ": " + self.gender + " (" + self.ageRange + ") Interestingness: " + str(self.interestingness) + " labels: " + str(self.labels.keys())


    def __init__(self, age_probas, gender_probas, person_id,
                 (face_top_left_2d, face_top_right_2d,
                  face_bottom_right_2d, face_bottom_left_2d, face_center_2d)):
        self.id = person_id
        self.labels = {}
        self.interestingness = 0
        self.last_seen = time.time()
        
        # Person's properties
        self.gender_probabilities = gender_probas
        self.gender = max(gender_probas.iterkeys(), key=(lambda key: gender_probas[key]))
        
        self.age_probabilities = age_probas
        self.ageRange = max(age_probas.iterkeys(), key=(lambda key: age_probas[key]))
        
        # number of samples (frames) that the age/gender are being predicted based on
        self.num_samples = 1

        self.speed = 0
        # Height is a value proportional to the person's size on screen
        # could be a smaller person close to the camera, or a taller person
        # further from the camera
        self.height = 0
        # Person's position in Camera and World space
        self.posCamera = (0, 0)
        self.posWorld = (0, 0, 0)
        #2d face bounding box location coordinates
        self.face_top_left_2d = face_top_left_2d
        self.face_top_right_2d = face_top_right_2d
        self.face_bottom_right_2d = face_bottom_right_2d
        self.face_bottom_left_2d = face_bottom_left_2d
        self.face_center_2d = face_center_2d

        #3d face bounding box location coordinates
        self.face_top_left_3d = face_top_left_2d
        self.face_top_right_3d = face_top_right_2d
        self.face_bottom_right_3d = face_bottom_right_2d
        self.face_bottom_left_3d = face_bottom_left_2d
        self.face_center_3d = face_center_2d

        self.faceLocHistory = deque(maxlen=FACE_HISTORY_LENGTH)
        self.faceSizeHistory = deque(maxlen=FACE_HISTORY_LENGTH)
        self.faceMidpointHistory = deque(maxlen=FACE_HISTORY_LENGTH)

        self.faceLocHistory.appendleft(
            (face_top_left_2d, face_top_right_2d,
             face_bottom_right_2d, face_bottom_left_2d, face_center_2d))
        
        self.faceSizeHistory.appendleft(face_size(face_top_left_2d, face_bottom_right_2d))


    def update_age_gender(self, age_probas, gender_probas):
        if self.num_samples >= MAX_NUM_SAMPLES:
            return
        
        # update the new probas and prediction
        
        # 1. update gender probas
        for key in self.gender_probabilities.keys():
            self.gender_probabilities[key] = self.update_probability(self.gender_probabilities[key], gender_probas[key])
        # 2. update gender prediction
        self.gender = max(self.gender_probabilities.iterkeys(), key=(lambda key: self.gender_probabilities[key]))
        
        # 3. update age probas
        for key in self.age_probabilities.keys():
            self.age_probabilities[key] = self.update_probability(self.age_probabilities[key], age_probas[key])
        # 4. update age prediction
        self.ageRange = max(self.age_probabilities.iterkeys(), key=(lambda key: self.age_probabilities[key]))
        
        self.num_samples = self.num_samples + 1
        

    def update_probability(self, old_value, new_value):
        return (float(self.num_samples * old_value) + new_value) / (self.num_samples + 1)
    
    
    def updateFace(self, (face_top_left_2d, face_top_right_2d,
                          face_bottom_right_2d, face_bottom_left_2d, face_center_2d)):

        self.face_top_left_2d = face_top_left_2d
        self.face_top_right_2d = face_top_right_2d
        self.face_bottom_right_2d = face_bottom_right_2d
        self.face_bottom_left_2d = face_bottom_left_2d
        self.face_center_2d = face_center_2d

        self.face_top_left_3d = face_top_left_2d
        self.face_top_right_3d = face_top_right_2d
        self.face_bottom_right_3d = face_bottom_right_2d
        self.face_bottom_left_3d = face_bottom_left_2d
        self.face_center_3d = face_center_2d

        self.faceMidpointHistory.appendleft(self.faceMidpoint())

        self.faceLocHistory.appendleft(
            (face_top_left_2d, face_top_right_2d,
             face_bottom_right_2d, face_bottom_left_2d, face_center_2d))
        
        self.faceSizeHistory.appendleft(face_size(face_top_left_2d, face_bottom_right_2d))


    def faceMidpoint(self):
        return ((self.face_top_left_2d[0] + self.face_bottom_right_2d[0]) / 2., (self.face_top_left_2d[1] + self.face_bottom_right_2d[1]) / 2.)


    def faceSize(self):
        return face_size(self.face_top_left_2d,self.face_bottom_left_2d)


    #Called when a match is found against a previous person, but before updateFace is called on them.
    def reappear(self):
        
        time_diff = time.time() - self.last_seen
        
        if time_diff > NEW_INTERACTION_TIMEOUT:
            self.faceSizeHistory = deque(maxlen=FACE_HISTORY_LENGTH)
            self.faceLocHistory = deque(maxlen=FACE_HISTORY_LENGTH)
            self.faceMidpointHistory = deque(maxlen=FACE_HISTORY_LENGTH)
        
        if time_diff > INTEREST_DECAY_INTERVAL:
            self.interestingness *= INTEREST_DECAY
            self.interestingness = max(0, self.interestingness)
        
        self.last_seen = time.time()
    
    
    def update_label(self, label_str, interestingness_increase):
        """
        Try to add or update a person's label
        
        Args:
            label_str (str).
            interestingness_increase (int). The number to add to this person's interestingness only when adding the label.
        """
        
        time_now = time.time()
        if not label_str in self.labels:
            self.labels[label_str] = time_now
            self.interestingness += interestingness_increase
        else:
            if time_now - self.labels[label_str] > TAG_MEMORY_SPAN:
                # update the label
                self.labels[label_str] = time_now

    
    def getAgeRange(self):
        return self.ageRange


    def getGender(self):
        return self.gender

