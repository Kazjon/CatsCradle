import numpy as np
import cv2
import xml.etree.cElementTree as et

from Camera import *

#
# Calibration class to calibrate the Camera
#
# The file can be run as a standalone (call run) and use keyboard strokes
# or imported in other python scripts
#    key  method               action
#    ' '  captureImage         capture the current chessboard corners if they are gridFound
#    'c'  computeCalibration   computes the calibration if enough samples have been capture_thread
#    's'  saveCalibration      saves the calibration in file
#    'l'  loadCalibration      loads the calibration from file
#    'q'  close                exits the application
#    'p'   -                   toggle the print variable (for debugging)
#

class Calibration:
    """Class to calibrate the camera"""

    def __init__(self):
        self.framePerSeconds = 20
        self.PRINT = False
        self.minCaptures = 15

        self.gray = None

        # termination criteria
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.chessboardLength = 9
        self.chessboardWidth = 6
        self.chessboardSize = (self.chessboardLength, self.chessboardWidth)

        # Chessboard corners
        self.corners = []

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
        self.objp = np.zeros((self.chessboardWidth * self.chessboardLength, 3), np.float32)
        self.objp[:,:2] = np.mgrid[0:self.chessboardLength, 0:self.chessboardWidth].T.reshape(-1,2)

        # Arrays to store object points and image points from all the images.
        self.objpoints = [] # 3d point in real world space
        self.imgpoints = [] # 2d points in image plane.

        self.rms = -1
        self.mtx = []
        self.dist = []

    def captureImage(self):
        """Capture one sample image if the grid was found"""
        if len(self.corners) > 0:
            self.objpoints.append(self.objp)
            self.imgpoints.append(self.corners)
        else:
            if self.PRINT:
                print "Grid not found"

        if self.PRINT == True:
            print "Num = ", len(self.objpoints)

    def enoughSamples(self):
        """Returns 1 if enough frames have been collected to compute the calibration"""
        return (len(self.objpoints) > self.minCaptures)

    def computeCalibration(self):
        """Compute calibration if enough samples have been captured"""
        if (self.enoughSamples()):
            self.rms, self.mtx, self.dist, rvecs, tvecs = cv2.calibrateCamera(self.objpoints,
                                                               self.imgpoints,
                                                               self.gray.shape[::-1],
                                                               None, None)
            if self.PRINT == True:
                print "num =", len(self.objpoints)
                print "rms =", self.rms
                print "mtx =", self.mtx
                print "dist =", self.dist

    def saveCalibration(self, filename):
        """Save the calibration in filename"""
        with open(filename, 'w') as f:
            np.savez(f, num=len(self.objpoints), rms=self.rms, mtx=self.mtx, dist=self.dist)
            f.close()

    def loadCalibration(self, filename):
        """Load the calibration file"""
        with open(filename, 'r') as f:
            npzfile = np.load(f)
            self.rms = npzfile['rms']
            self.mtx = npzfile['mtx']
            self.dist = npzfile['dist']

            if self.PRINT == True:
                print "files = ", npzfile.files
                print "num =", npzfile['num']
                print "rms =", self.rms
                print "mtx =", self.mtx
                print "dist =", self.dist
            f.close()

    def analyzeImage(self, img):
        """Get the current frame, with the grid if it was found"""
        self.gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners0 = cv2.findChessboardCorners(self.gray,
                                        self.chessboardSize,
                                        flags=cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_NORMALIZE_IMAGE)

        # If found, add object points, image points (after refining them)
        if ret == True:
            self.corners = cv2.cornerSubPix(self.gray, corners0, (11,11), (-1,-1), self.criteria)

            # Draw and display the corners
            img2 = cv2.drawChessboardCorners(img, self.chessboardSize, self.corners, ret)
            return img2

        else:
            self.corners = []
            return img

    def run(self, camera):
        """Starts the loop for the calibration"""
        while True:
            ret, img = camera.getFrame()
            if not ret:
                continue

            img = self.analyzeImage(img)
            cv2.imshow('Calibration View', img)

            key = cv2.waitKey(1000 / self.framePerSeconds)

            if (key == ord('q')):
                # exit
                break

            elif (key == ord(' ')):
                # Save image
                self.captureImage()

            elif (key == ord('c')):
                # Calibrate if enough data (>minCaptures)
                self.computeCalibration()

            elif (key == ord('s')):
                # save calibration in file
                self.saveCalibration("Calibration.npz")

            elif (key == ord('l')):
                # load calibration from file
                self.loadCalibration("Calibration.npz")

            elif (key == ord('p')):
                # toggle print state
                self.PRINT = not self.PRINT
                print "Switching PRINT = ", self.PRINT


if __name__ == '__main__':
    camera = Camera(0)

    calib = Calibration()
    calib.run(camera)

    cv2.destroyAllWindows()
