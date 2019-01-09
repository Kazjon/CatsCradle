import cv2
import numpy

from MathUtils import *
from Camera import *
from BodyPartDetector import *
from sets import Set
from collections import deque
from scipy.spatial import distance
from threading import Lock

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

INTEREST_DECAY = 0.99
FACE_HISTORY_LENGTH = 10

def face_size(face_loc):
    return distance.euclidean([face_loc[0],face_loc[1]],[face_loc[2],face_loc[3]])

class Person:
    """Class to handle a person parameters"""

    def __str__(self):
        return "Id: %s, Gender: %s, Age: %s"%(self.id,\
            self.getGender(), self.getAgeRange())

    def __init__(self, frame, faceLocation, faceEncoding, gender, ageRange, personCount, roi):
        self.id = personCount
        self.labels = Set()
        self.interestingness = 0
        # detector
        self.bodyDetector = BodyPartDetector()
        # Person's properties
        self.gender = 'M'
        # As soon as a Person object is created, the age/gender detection thread
        # grabs the gender and ageRange Lock objects. If any other program logic
        # needs access to age and gender, it must access them through the
        # getAgeRange and getGender functions which check if the lock has been
        # released by the age/gender detection thread. If so, these methods
        # return the detected age and gender. If not, they return None
        self.genderLock = Lock()
        self.ageRange = '25-32'
        self.ageRangeLock = Lock()

        self.smile = False
        self.speed = 0
        # Height is a value proportional to the person's size on screen
        # could be a smaller person close to the camera, or a taller person
        # further from the camera
        self.height = 0
        # Person's position in Camera and World space
        self.posCamera = (0, 0)
        self.posWorld = (0, 0, 0)
        self.faceLocation = faceLocation # Tuple of bounding box: (top,right,bottom,left)
        self.faceLocHistory = deque(maxlen=FACE_HISTORY_LENGTH)
        self.faceSizeHistory = deque(maxlen=FACE_HISTORY_LENGTH)
        self.faceEncoding = faceEncoding # 128-length vector encoding differences from average face for easy cosine comparisons
        self.roi = roi
        # TODO: Find the best tracker type
        trackerType = 'KCF'
        if False:
            self.tracker = cv2.Tracker_create(trackerType)
        else:
            if trackerType == 'BOOSTING':
                self.tracker = cv2.TrackerBoosting_create()
            elif trackerType == 'MIL':
                self.tracker = cv2.TrackerMIL_create()
            elif trackerType == 'KCF':
                self.tracker = cv2.TrackerKCF_create()
            # elif trackerType == 'TLD':
            #     self.tracker = cv2.TrackerTLD_create()
            elif trackerType == 'MEDIANFLOW':
                self.tracker = cv2.TrackerMedianFlow_create()
            # elif trackerType == 'GOTURN':
            #     self.tracker = cv2.TrackerGOTURN_create()
            else:
                print "Invalid tracker type", trackerType

        ok = self.tracker.init(frame, self.roi)

    def updateFace(self,new_face_loc):
        self.faceLocation = new_face_loc
        self.faceLocHistory.appendleft(new_face_loc)
        self.faceSizeHistory.appendleft(face_size(new_face_loc))

    def updateInterest(self):
        self.interestingness *= INTEREST_DECAY
        self.interestingness = max(0,self.interestingness)

    def getAgeRange(self):
        """
        Checks if ageRangeLock has been released. If so, returns ageRange.
        If not returns None.
        """
        return None if self.ageRangeLock.locked() else self.ageRange

    def getGender(self):
        """
        Checks if genderLock has been released. If so, returns gender. If not
        returns None.
        """
        return None if self.genderLock.locked() else self.gender

    def update(self, frame):
        """Track the person in the frame"""
        # Watch out: update returns double values
        ok, droi = self.tracker.update(frame)
        self.roi = (int(droi[0]), int(droi[1]), int(droi[2]), int(droi[3]))
        if ok:
            self.posCamera = centerROI(self.roi)
            # Check for smile
            smiles = self.bodyDetector.detectSmiles(frame, self.roi)
            if len(smiles) > 0:
                self.smile = True
            else:
                self.smile = False
        else:
            print "Tracking error"


    def draw(self, frame):
        """Draw the person's face in frame"""
        p1 = (int(self.roi[0]), int(self.roi[1]))
        p2 = (int(self.roi[0] + self.roi[2]), int(self.roi[1] + self.roi[3]))
        p3 = (int(self.roi[0] + self.roi[2] / 3), int(self.roi[1] + self.roi[3] / 3))
        # Display person in blue
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2)
        cv2.putText(frame,
                    'Person ' + str(self.id),
                    p3,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (255, 0, 0),
                    2, cv2.LINE_AA)

        return frame

    #TODO: Replace this when the age-and-gender stuff is in properly.
    def isAdult(self):
        return True


if __name__ == '__main__':

    camera = Camera(0)
    detector = BodyPartDetector()

    persons = []

    while True:
        ret, frame = camera.getFrame()
        if not ret:
            continue

        faces = detector.detectFaces(frame)
        #bodies = sensor.detectFullBodies(frame)

        for p in persons:
            p.update(frame)

        if len(faces) != len(persons):
            newPersons = []
            for face in faces:
                found = False
                for p in persons:
                    if overlapROIs(p.roi, face):
                        # Match existing person
                        found = True
                        newPersons.append(p)
                        break
                if not found:
                    # Create new person
                    newPersons.append(Person(frame, face))
            persons = newPersons

        for p in persons:
            frame = p.draw(frame)

        # Display detected face in red
        detector.draw(frame, faces, (0, 0, 255))

        # Display the resulting frame
        cv2.imshow('Person tracking', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
