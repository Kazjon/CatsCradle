"""
Running this script will open the camera. Take 10 pictures of a chessboard from
different angles and positions by pressing "p" on the keyboard. After the 10th
picture is taken, the script will automatically terminate.
"""

import numpy as np
import cv2

def main():
    camera = cv2.VideoCapture(0)
    i = 0

    while True:
        ret, frame = camera.read()
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('p'):
            cv2.imwrite("calibration_imgs/%d.png"%i, frame)
            i += 1
        if i == 10:
            camera.release()
            cv2.destroyAllWindows()
            break

if __name__ == '__main__':
    main()
