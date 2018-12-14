import cv2
import numpy
import copy

from PersonSensor import *


class Audience:
    """Class to handle the audience"""
    def __init__(self, personSensor):
        self.persons = []
        self.personSensor = personSensor
        self.previousPersons = []

    def update(self, tf_sess):
        self.previousPersons = self.persons
        self.persons = self.personSensor.getPersons(self.previousPersons, tf_sess)



if __name__ == '__main__':
    # Tests
    personSensor = PersonSensor([Camera(0)])
    personSensor.show = True

    audience = Audience(personSensor)

    while True:
        audience.update()
        for person in audience.persons:
            print(person)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
