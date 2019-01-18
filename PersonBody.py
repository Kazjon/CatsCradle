import cv2
(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

class PersonBody:
    """Class to handle the full body of a person. This class has nothing to do
        with a person's face, age or gender. It is only concerned with the
        person's position. The back camera only sees PersonBody objects, not
        Person objects. The front camera sees Person objects as well as
        PersonBody objects.
    """

    def __str__(self):
        return "2D Position:\ntop left: %.2f, top right: %.2f," + \
            "bottom left: %.2f, bottom right: %.2f, center: %.2f\n" + \
            "3D Position:\ntop left: %.2f, top right: %.2f," + \
            "bottom left: %.2f, bottom right: %.2f, center: %.2f"%\
            (self.body_top_left_2d, self.body_top_right_2d, self.body_bottom_right_2d,\
            self.body_bottom_left_2d, self.body_center_2d, self.body_top_left_3d,\
            self.body_top_right_3d, self.body_bottom_right_3d, self.body_bottom_left_3d,\
            self.body_center_3d)

    def __init__(self, body_top_left_2d, body_top_right_2d,\
        body_bottom_right_2d, body_bottom_left_2d, body_center_2d,\
        body_top_left_3d, body_top_right_3d, body_bottom_right_3d,\
        body_bottom_left_3d, body_center_3d):
            self.body_top_left_2d = body_top_left_2d
            self.body_top_right_2d = body_top_right_2d
            self.body_bottom_right_2d = body_bottom_right_2d
            self.body_bottom_left_2d = body_bottom_left_2d
            self.body_center_2d = body_center_2d
            self.body_top_left_3d = body_top_left_3d
            self.body_top_right_3d = body_top_right_3d
            self.body_bottom_right_3d = body_bottom_right_3d
            self.body_bottom_left_3d = body_bottom_left_3d
            self.body_center_3d = body_center_3d

    def getHeight(self):
        return self.body_top_left_2d[1] - self.body_bottom_left_2d[1]
