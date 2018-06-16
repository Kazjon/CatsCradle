class Eye:
    """Class to handle the eye and eyelid motions
    Eye reference space:
        origin = Eye center in the Head reference space
        x axis = front
        y axis = left
        z axis = up
    3 parameters:
        angleY: angle around y axis (look up/down)
        angleZ: angle around z axis (look right/left)
        eyelidPos: number between 0 and 9 (0 = closed, 9 = opened)
    """
    def __init__(self, name):
        self.name = name
        self.angleY = 0
        self.angleZ = 0
        self.eyelidPos = 9

    def pupilToEye(self):
        """ Get the pupil transform in eye space"""
        transform = np.identity(4)
        transform = RotateY(transform, self.angleY)
        transform = RotateZ(transform, self.angleZ)
        return transform
        
