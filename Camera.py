import cv2
import threading
import Queue

# TODO: Add video file input option

class Camera:
    """
    Class to handle a camera
    Launches a thread to retrieve the frames of the camera at a certain rate
    """

    def __init__(self, port, fps = 30):
        # Device
        self.capture = None
        self.port = port
        self.fps = fps
        # Calibration variables
        # Used to convert point from camera space to World space
        # and estimate size of objects
        self.offset = (0, 0, 100)
        self.scale = 100
        # Thread related variables
        self.q = Queue.Queue()
        self.running = False
        self.capture_thread = None
        self.start()

    def __del__(self):
        self.stop()

    def stop(self):
        if self.running:
            self.running = False
            self.capture_thread.join()
            # When everything is done, release the capture
            self.capture.release()

    def start(self):
        self.capture = cv2.VideoCapture(self.port)
        # self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 680)
        # self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 280)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        if not self.running:
            # Starts the thread
            self.running = True
            self.capture_thread = threading.Thread(name='Camera'+ str(self.port), target=self.threadFunc)
            self.capture_thread.setDaemon(True)
            self.capture_thread.start()

    def threadFunc(self):
        while(self.running):
            self.capture.grab()
            retval, img = self.capture.read()

            if self.q.qsize() < 10:
                self.q.put(img)

    def getFrame(self):
        """Get the current frame"""
        if not self.q.empty():
            frame = self.q.get()
            return True, frame
        return False, None

    def calibrate(self, offset, scale):
        """Define calibration constants"""
        self.offset = offset
        self.scale = scale

    def cameraToWorld(self, (x, y)):
        """Returns world coordinates for the point in camera space"""
        # TODO: Implementation needed???
        return (x + self.offset[0], y + self.offset[1], self.offset[2])

    def estimateSize(self, size, standardSize):
        """Returns an estimation of the real size of an object
        Needs a standard size for the object"""
        return self.scale * size / standardSize


if __name__ == '__main__':
    # Tests
    c = Camera(0)

    while True:
        ret, frame = c.getFrame()
        if not ret:
            continue

        # Display the resulting frame
        cv2.imshow('Camera Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
