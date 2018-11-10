import cv2
import numpy

from Camera import *

class BodyPartDetector:
    """
    Use the OpenCV Haar cascades to detect bodies, faces, eyes and smiles from
    an image
    """
    def __init__(self):
        # TODO: Make sure the path is the same on all machines
        openCVPath = '/usr/local/Cellar/opencv/3.3.1_1/share/OpenCV/'
        haarcascadesPath = openCVPath + 'haarcascades/'

        self.frontalFaceCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_frontalface_default.xml')
        self.profileFaceCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_profileface.xml')
        # TODO: other cascade to try:
        #self.frontalFaceAltCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_frontalface_alt.xml')
        #self.frontalFaceAlt2Cascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_frontalface_alt2.xml')
        #self.frontalFaceAltTreeCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_frontalface_alt_tree.xml')
        self.eyeCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_eye.xml')
        self.smileCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_smile.xml')
        self.fullBodyCascade = cv2.CascadeClassifier(haarcascadesPath + 'haarcascade_fullbody.xml')

        # TODO: Try LBP cascades???

    def shiftROIs(self, rois, xOffset, yOffset, maxElements = -1):
        """Shift the rois in the list with the given offset
            If maxElements is defined, return only the first maxElements values
        """
        newROIS = []
        for (x, y, w, h) in rois:
            newROIS.append((x + xOffset, y + yOffset, w, h))
            if maxElements > 0 and len(newROIS) == maxElements:
                break
        return newROIS


    def detectFullBodies(self, image, xxx_todo_changeme = (0, 0, -1, -1)):
        """Detect the bodies in image roi (x, y, w, h)"""
        (x, y, w, h) = xxx_todo_changeme
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        bodies = self.fullBodyCascade.detectMultiScale(
                                             gray,
                                             scaleFactor=1.1,
                                             minNeighbors=5,
                                             minSize=(100, 100),
                                             flags=cv2.CASCADE_SCALE_IMAGE
                                             )

        return self.shiftROIs(bodies, x, y)


    def detectFaces(self, image, xxx_todo_changeme1 = (0, 0, -1, -1)):
        """Detect the faces in image roi (x, y, w, h)"""
        (x, y, w, h) = xxx_todo_changeme1
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        roiGray = gray[y:y+h, x:x+w]

        faces = self.frontalFaceCascade.detectMultiScale(
                                             roiGray,
                                             scaleFactor=1.1,
                                             minNeighbors=5,
                                             minSize=(30, 30),
                                             flags=cv2.CASCADE_SCALE_IMAGE
                                             )

        profileFaces = self.profileFaceCascade.detectMultiScale(
                                         roiGray,
                                         scaleFactor=1.1,
                                         minNeighbors=5,
                                         minSize=(30, 30),
                                         flags=cv2.CASCADE_SCALE_IMAGE
                                         )

        # TODO: Remove duplicate faces in profile faces

        if len(profileFaces) > 0:
            numpy.append(faces, profileFaces, axis = 0)

        return self.shiftROIs(faces, x, y)


    def detectEyes(self, image, xxx_todo_changeme2 = (0, 0, -1, -1)):
        """Detect the eyes in image roi (x, y, w, h)"""
        (x, y, w, h) = xxx_todo_changeme2
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        roiGray = gray[y:y+h, x:x+w]

        eyes = self.eyeCascade.detectMultiScale(
                                           roiGray,
                                           scaleFactor=1.1,
                                           minNeighbors=5,
                                           minSize=(30, 30),
                                           maxSize=(w / 2, h / 5),
                                           flags=cv2.CASCADE_SCALE_IMAGE
                                           )
        return self.shiftROIs(eyes, x, y, 2)


    def detectSmiles(self, image, xxx_todo_changeme3 = (0, 0, -1, -1)):
        """Detect the smile in image roi (x, y, w, h)"""
        (x, y, w, h) = xxx_todo_changeme3
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        roiGray = gray[y:y+h, x:x+w]

        smiles = self.smileCascade.detectMultiScale(
                                           roiGray,
                                           scaleFactor= 1.7,
                                           minNeighbors=20,
                                           minSize=(30, 30),
                                           maxSize=(w, h / 2),
                                           flags=cv2.CASCADE_SCALE_IMAGE
                                           )
        return self.shiftROIs(smiles, x, y, 1)

    def draw(self, image, rois, color):
        # Draw a rectangle around the rois
        for (x, y, w, h) in rois:
            cv2.rectangle(image, (x, y), (x+w, y+h), color, 2)

        return image



if __name__ == '__main__':
    # Tests
    camera = Camera(0)
    d = BodyPartDetector()

    while True:
        ret, frame = camera.getFrame()
        if not ret:
            continue

        bodies = d.detectFullBodies(frame)
        frame = d.draw(frame, bodies, (0, 255, 0)) # draw bodies in green

        faces = d.detectFaces(frame)
        frame = d.draw(frame, faces, (0, 0, 255)) # draw faces in red

        for face in faces:
            eyes = d.detectEyes(frame, face)
            frame = d.draw(frame, eyes, (0, 255, 255)) # draw eyes in yellow
            smiles = d.detectSmiles(frame, face)
            frame = d.draw(frame, smiles, (255, 0, 0)) # draw smile in blue

        cv2.imshow('BodyPartDetector', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
