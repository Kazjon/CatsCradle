import cv2
import numpy
import copy
from scipy.spatial import Voronoi
from scipy.spatial.distance import cdist

from collections import deque

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

    def update(self):
        self.previousPersons = self.persons
        self.previousPersonBodies = self.personBodies

        #self.previousPersonBodiesBehindMarionette =\
        #    self.personBodiesBehindMarionette

        self.persons, self.personBodies = self.personSensor.getPersonsAndPersonBodies(
            self.previousPersons,
            self.previousPersonBodies
        )

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

    #Returns the point in the camera field that is furthest away from any faces
    def furthestFromFaces(self):
        width = self.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        corners = [[0,0],[0,height],[width,0],[width,height]]
        #If there's no people, return the bottom left corner
        if len(self.persons) == 0:
            return corners[1]
        else:
            points = corners
            personlocs = [p.faceMidpoint() for p in self.persons]
            #If there's one person, return the furthest corner
            #If there's two or three people, return the furthest out of the corners plus midpoint between them
            if len(self.persons) > 1 and len(self.persons) < 4:
                points.append(np.mean(personlocs,axis=0))
            # If there's four or more people, return the furthest out of the Voronoi points plus the corners
            elif len(self.persons) >= 4:
                voronoi = Voronoi(personlocs)
                #print "voronoi",voronoi.vertices
                for vp in list(voronoi.vertices):
                    if all(vp>0) and vp[0] < width and vp[1] < height:
                        points.append(list(vp))
            #Choose the point with the highest minimum distance to all people
            #print "points",points
            dists = cdist(np.array(personlocs), np.array(points))
            #print "dists",dists
            minDists = np.amin(dists,axis=0)
            #print "minDists",minDists
            #print "furthestPoint",np.argmax(minDists)
            furthest = points[np.argmax(minDists)]
            return furthest

if __name__ == '__main__':
    # Tests
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    personSensor = PersonSensor()
    personSensor.load_camera(camera)
    personSensor.show = True

    audience = Audience(personSensor)

    while True:
        audience.update()
        for person in audience.persons:
            print(person)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
