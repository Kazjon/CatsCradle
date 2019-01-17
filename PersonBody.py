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
            (self.top_left_2d, self.top_right_2d, self.bottom_right_2d,\
            self.bottom_left_2d, self.center_2d, self.top_left_3d,\
            self.top_right_3d, self.bottom_right_3d, self.bottom_left_3d,\
            self.center_3d)

    def __init__(self, top_left_2d, top_right_2d, bottom_right_2d,\
        bottom_left_2d, center_2d, top_left_3d, top_right_3d,\
        bottom_right_3d, bottom_left_3d, center_3d):
            self.top_left_2d = top_left_2d
            self.top_right_2d = top_right_2d
            self.bottom_right_2d = bottom_right_2d
            self.bottom_left_2d = bottom_left_2d
            self.center_2d = center_2d
            self.top_left_3d = top_left_3d
            self.top_right_3d = top_right_3d
            self.bottom_right_3d = bottom_right_3d
            self.bottom_left_3d = bottom_left_3d
            self.center_3d = center_3d
