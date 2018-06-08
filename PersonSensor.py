import cv2
import numpy

from MathUtils import *
from BodyPartDetector import *
from Person import *
from Sensor import *

class PersonSensor(Sensor):
    """
    Use the BodyPartDetector to sense a person
    """
    def __init__(self, cameras, cv_path):
        Sensor.__init__(self, cameras)

        self.cv_path = cv_path
        self.bodyDetector = BodyPartDetector(cv_path)
        self.show = False

        # TODO: Get proper standard values (mm)
        self.standardBodyWidth = 500
        self.standardBodyHeight = 1700
        self.standardFaceWidth = 200
        self.standardFaceHeight = 300


    def getPersons(self, previousPersons):
        persons = []
        for camera in self.cameras:
            ret, frame = camera.getFrame()
            if not ret:
                continue

            # For now only detect faces
            #
            # bodies = self.bodyDetector.detectFullBodies(frame)
            # for body in bodies:
            #     # detect the face(s???) inside the body
            #     face = self.bodyDetector.detectFaces(frame, body)
            faces = self.bodyDetector.detectFaces(frame)
            for face in faces:
                alreadyExists = False
                for prevPerson in previousPersons:
                    if overlapROIs(face, prevPerson.roi):
                        alreadyExists = True
                        persons.append(prevPerson)
                        #prevPerson.update(frame)
                        break
                if not alreadyExists:
                    person = Person(frame, face, self.cv_path)
                    eyes = self.bodyDetector.detectEyes(frame, face)
                    # Estimate person's position
                    # TODO: use eyes spacing to estimate distance from camera
                    person.posCamera = centerROI(face)
                    person.posWorld = camera.cameraToWorld(person.posCamera)
                    # Estimate person's height
                    person.height = camera.estimateSize(face[3], self.standardFaceHeight)
                    persons.append(person)

            if self.show:
                for (x, y, w, h) in faces:
                    # Display detected face in red
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)

                for p in persons:
                    # Display person in blue
                    p.draw(frame)

                cv2.imshow('Persons Sensor', frame)

        return persons



if __name__ == '__main__':
    # Tests
    camera = Camera(0)
    sensor = PersonSensor([camera])
    sensor.show = True

    previousPersons = []

    while True:
        persons = sensor.getPersons(previousPersons)
        print "Num persons =", len(persons)
        previousPersons = persons

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
