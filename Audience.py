import time
import cv2
import numpy
import copy
from scipy.spatial import Voronoi
from scipy.spatial.distance import cdist

from collections import deque

from PersonSensor import *
from Person import TAG_MEMORY_SPAN

# To get the PROCESSING_SIZE variable from predictor
from image_processing import predictor

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
        self.personSensor.update_back_camera()

        previousIDs = set([p.id for p in self.previousPersons])
        currentIDs = set([p.id for p in self.persons])
        
        lost_ids = list(previousIDs.difference(currentIDs))
        self.numLostHistory.append(len(lost_ids))
        
        new_ids = list(currentIDs.difference(previousIDs))
        self.numNewHistory.append(len(new_ids))

        self.new_persons = [p for p in self.persons if p.id in new_ids]
        self.lost_persons = [p for p in self.previousPersons if p.id in lost_ids]
    
        """
        if len(self.new_persons) > 0:
            for person in self.new_persons:
                print("New person :) " + str(person))
        if len(self.lost_persons) > 0:
            for person in self.lost_persons:
                print("Missed a person :( " + str(person))
        """
        #self.personBodiesBehindMarionette = self.personSensor.\
        #    getPersonBodiesOnly(self.previousPersonBodiesBehindMarionette)
        # print "Num persons =", len(self.persons)
        # for person in self.persons:
        #     print(person)


    def numLostRecently(self):
        return sum(self.numLostHistory)


    def numNewRecently(self):
        return sum(self.numNewHistory)


    def get_people_with_condition(self, filter_dict):
        """
        Get persons having some conditions.
        
        Args:
            filter_dict (dict): should have at least the following keys
                {
                    'having_label': (str) put None to remove this condition.
                    'having_age': (str) put None to remove this condition.
                    'having_gender': (str) put None to remove this condition.
                    'recency': (str) should be either 'new', 'lost', or 'current'.
                }
        
        Returns:
            list of Person objects.
        """
        
        having_label = filter_dict['having_label']
        having_age = filter_dict['having_age']
        having_gender = filter_dict['having_gender']
        recency = filter_dict['recency']
        
        result_persons = []
        
        # picking the population
        persons = self.persons
        if recency == 'new':
            persons = self.new_persons
        elif recency == 'lost':
            persons = self.lost_persons

        # checking each person
        for person in persons:
            # check label condition
            if (not having_label is None) and (having_label in person.labels):
                # tags older than MEMORY_SPAN are not valid
                if time.time() - person.labels[having_label] > TAG_MEMORY_SPAN:
                    continue
            # check age condition
            if not having_age is None:
                if person.getAgeRange() != having_age:
                    continue
            # check gender condition
            if not having_gender is None:
                if person.getGender() != having_gender:
                    continue
            # if reached here then we add this person
            result_persons.append(person)
        
        return result_persons


    #Returns the point in the camera field that is furthest away from any faces
    def furthestFromFaces(self):
	cameraMaxX = self.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        cameraMaxY = self.personSensor.front_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = predictor.PROCESSING_SIZE
        height = width * cameraMaxY / cameraMaxX
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
