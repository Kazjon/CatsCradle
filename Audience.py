import cv2
import numpy
import copy

from PersonSensor import *


class Audience:
    """Class to handle the audience"""
    def __init__(self, personSensor):
        self.personSensor = personSensor
        self.persons = []
        self.previousPersons = []
        self.personBodies = []
        self.previousPersonBodies = []
        self.personBodiesBehindMarionette = []
        self.previousPersonBodiesBehindMarionette = []

    def update(self, tf_sess):
        self.previousPersons = self.persons
        self.previousPersonBodies = self.personBodies
        #self.previousPersonBodiesBehindMarionette =\
        #    self.personBodiesBehindMarionette

        self.persons, self.personBodies =\
            self.personSensor.getPersonsAndPersonBodies\
            (self.previousPersons, self.previousPersonBodies)

        #self.personBodiesBehindMarionette = self.personSensor.\
        #    getPersonBodiesOnly(self.previousPersonBodiesBehindMarionette)
        # print "Num persons =", len(self.persons)
        # for person in self.persons:
        #     print(person)



if __name__ == '__main__':
    # Tests
    personSensor = PersonSensor([Camera(0)], None)
    personSensor.show = True

    audience = Audience(personSensor)

    while True:
        audience.update(None)
        for person in audience.persons:
            print(person)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
