import cv2
import numpy
import copy

from PersonSensor import *

ENTRY_EXIT_HISTORY_LENGTH = 25

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
        self.numLostHistory = deque([0]*ENTRY_EXIT_HISTORY_LENGTH,maxlen=ENTRY_EXIT_HISTORY_LENGTH)
        self.numNewHistory = deque([0]*ENTRY_EXIT_HISTORY_LENGTH,maxlen=ENTRY_EXIT_HISTORY_LENGTH)

    def update(self, tf_sess, getPersonBodies=False, cnn_detection=False):
        self.previousPersons = self.persons
        self.previousPersonBodies = self.personBodies

        #self.previousPersonBodiesBehindMarionette =\
        #    self.personBodiesBehindMarionette

        self.persons, self.personBodies =\
            self.personSensor.getPersonsAndPersonBodies\
            (self.previousPersons, self.previousPersonBodies, getPersonBodies=getPersonBodies, cnn_detection=cnn_detection)

        previousIDs = set([p.id for p in self.previousPersons])
        currentIDs = set([p.id for p in self.persons])
        self.numLostHistory.append(len(previousIDs.difference(currentIDs)))
        self.numNewHistory.append(len(currentIDs.difference(previousIDs)))

        #self.personBodiesBehindMarionette = self.personSensor.\
        #    getPersonBodiesOnly(self.previousPersonBodiesBehindMarionette)
        # print "Num persons =", len(self.persons)
        # for person in self.persons:
        #     print(person)

    def numLostRecently(self):
        return sum(self.numLostHistory)

    def numNewRecently(self):
        return sum(self.numNewHistory)



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
