(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

class BackPerson:
    """Class to handle a person seen by the back camera. Essentially
        just encodes the person's position.
    """

    def __str__(self):
        return "Position"

    def __init__(self):
        pass
