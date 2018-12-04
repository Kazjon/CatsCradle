import cv2
import numpy

from MathUtils import *
from Camera import *
from BodyPartDetector import *

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

class Person:
    """Class to handle a person parameters"""

    def __str__(self):
        return "Id: %s, Gender: %s, Age: %s"%(self.id,\
            self.gender, self.ageRange)

    def __init__(self, frame, faceEncoding, gender, ageRange, personCount, roi):
        self.id = personCount
        # detector
        self.bodyDetector = BodyPartDetector()
        # Person's properties
        self.gender = gender
        self.smile = False
        self.ageRange = ageRange
        self.speed = 0
        # Height is a value proportional to the person's size on screen
        # could be a smaller person close to the camera, or a taller person
        # further from the camera
        self.height = 0
        # Person's position in Camera and World space
        self.posCamera = (0, 0)
        self.posWorld = (0, 0, 0)
        self.faceEncoding = faceEncoding
        self.roi = roi
        # TODO: Find the best tracker type
        trackerType = 'KCF'
        if int(minor_ver) < 3:
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
