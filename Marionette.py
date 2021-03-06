from Eye import *
from MatrixUtil import *
from Motor import *
from ReferenceSpace import *

#
# Marionette's motors layout
#      S = Shoulder rotation
#      SR/SL = Shoulder Right and Left
#      H = Head rotation (????? question: is the head motor static on the shoulders rod?????)
#      HR/HL = Head Right and Left
#      FR/FL = Foot Right and Left
#      AR/AL = Arm Right and Left
#      WR/WL = Wrist Right and Left
#      EX/EY = Eye angle around Horizontal (left/right - Yaw = x) and angle around Vertical (up/down - Pitch = y)
#
#        WR  FR     W     FL   WL    -> Fixed on ceiling
#                   |
#                   |
#        SR_________S__________SL    -> Horizontal rotation (Shoulders)
#          AR__|    |      |__AL        (no AR motor but needed for simulator)
#                   |
#            HR_ER__H__EL_HL          -> Horizontal rotation (Head)
#
#

class Marionette:
    """Hold the marionette physical data"""

    def __init__(self):
        """motors is the list of Motors objects in the following order:
        S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL, EX, EY"""

        # Marionette's dimensions in mm (to be updated)
        rod_O_S = 50 # length of upper vertical rod (shoulders)
        rod_S_H = 100 # length of lower vertical rod (head)
        # Offset definition: Fixed point of the string.
        # Could be a hole in the horizontal rods (for Head and Shoulders)
        # or the last contact point of the string on the motor circonference
        offset = {}
        offset['SR'] = (0, -405, 0) # offset of the motor SR string hole on the right end of shoulders rod
        offset['SL'] = (0,  405, 0) # offset of the motor SL string hole on the left end of shoulders rod
        offset['AR'] = (65, -405, 0) # offset of the motor AR string hole on the right end of shoulders rod
        offset['AL'] = (65,  405, 0) # offset of the motor AL string hole on the left end of shoulders rod
        offset['HR'] = (0, -150, 0) # offset of the motor HR string hole on the right end of the head rod
        offset['HL'] = (0,  150, 0) # offset of the motor HL string hole on the left end of the head rod
        offset['FL'] = (-255,  255, -25) # offset of the motor FL on the ceiling (marionette's top attachment)
        offset['FR'] = (-255, -255, -25) # offset of the motor FR on the ceiling (marionette's top attachment)
        offset['WL'] = ( 255,  255, -25) # offset of the motor WL on the ceiling (marionette's top attachment)
        offset['WR'] = ( 255, -255, -25) # offset of the motor WR on the ceiling (marionette's top attachment)
        offset['EX'] = ( 0, 0, 0) # offset of the motor EX in the Head
        offset['EY'] = ( 0, 0, 0) # offset of the motor EY in the Head
        self.length = {}
        self.length['SR'] = 1314.45 # 51.75 inches  # Initial length of string on SR (at 0 degrees rotation)
        self.length['SL'] = 1314.45 # 51.75 inches  # Initial length of string on SL (at 0 degrees rotation)
        self.length['AR'] = 1066.8  # UNUSED        # Initial length of string on AR (at 0 degrees rotation)
        self.length['AL'] = 1066.8  # 42 inches     # Initial length of string on AL (at 0 degrees rotation)
        self.length['HR'] = 590.55  # 23.25 inches  # Initial length of string on HR (at 0 degrees rotation)
        self.length['HL'] = 584.2   # 23 inches     # Initial length of string on HL (at 0 degrees rotation)
        self.length['FR'] = 2114.55 # 83.25 inches  # Initial length of string on FR (at 0 degrees rotation)
        self.length['FL'] = 2108.2  # 83 inches     # Initial length of string on FL (at 0 degrees rotation)
        self.length['WR'] = 1485.9  # 58.5 inches   # Initial length of string on WR (at 0 degrees rotation)
        self.length['WL'] = 1479.55 # 58.25 inches  # Initial length of string on WL (at 0 degrees rotation)
        # Non static motors (no string -> length = 0)
        self.length['S'] = 0
        self.length['H'] = 0
        self.length['EX'] = 0
        self.length['EY'] = 0
        # Motors settings
        radius = 25.5 / 2 # All motors have the same diameter (1 inch)
        # Number of microsteps of the stepper motors (2 for Arms and Wrists, 8 otherwise)
        self.motorMicrosteps = {}
        self.motorMicrosteps['S'] = 0
        self.motorMicrosteps['SR'] = 8
        self.motorMicrosteps['SL'] = 8
        self.motorMicrosteps['AR'] = 2
        self.motorMicrosteps['AL'] = 2
        self.motorMicrosteps['H'] = 0
        self.motorMicrosteps['HR'] = 8
        self.motorMicrosteps['HL'] = 8
        self.motorMicrosteps['FR'] = 8
        self.motorMicrosteps['FL'] = 8
        self.motorMicrosteps['WL'] = 2
        self.motorMicrosteps['WR'] = 2
        self.motorMicrosteps['EX'] = 0
        self.motorMicrosteps['EY'] = 0

        # Marionette's measurements (mm):
        self.headWidth = 176
        self.shoulderWidth = 280
        self.armLengthR = 250
        self.armLengthL = 250
        self.forearmLengthR = 260
        self.forearmLengthL = 260
        # eyes offset from the head RIGHT attachment point, along the HR/HL line
        self.eyeOffset = {}
        self.eyeOffset['ER'] = ( 15, 25, 40)
        self.eyeOffset['EL'] = ( 15, self.headWidth - 25, 40)

        # Motors
        self.motor = {}
        self.motorList = []
        self.stepperMotorList = []
        for key in ['S', 'SR', 'SL', 'AR', 'AL', 'H', 'HR', 'HL', 'FR', 'FL', 'WR', 'WL', 'EX', 'EY']:
            self.motor[key] = Motor('motor' + key, radius, self.motorMicrosteps[key], self.length[key])
            self.motorList.append(self.motor[key])
            if self.motor[key].isStatic:
                self.stepperMotorList.append(self.motor[key])

        # Default angles for the eyes are 90
        self.motor['EX'].defaultAngle = 90
        self.motor['EY'].defaultAngle = 90

        # The max for motor driving strings is the angle at which the string length is at its inital length (0 degrees)
        # Stepper (from Lilla's tests)
        self.motor['SR'].minAngle = -70
        self.motor['SL'].minAngle = -70
        self.motor['AR'].minAngle = 0
        self.motor['AL'].minAngle = -673
        self.motor['HR'].minAngle = -200
        self.motor['HL'].minAngle = -270
        self.motor['FR'].minAngle = -105
        self.motor['FL'].minAngle = -150
        self.motor['WR'].minAngle = -3500
        self.motor['WL'].minAngle = -4500
        # Eyes
        self.motor['EX'].minAngle = 70
        self.motor['EY'].minAngle = 70
        self.motor['EX'].maxAngle = 110
        self.motor['EY'].maxAngle = 110
        # Head and Shoulder
        self.motor['S'].minAngle = -45
        self.motor['S'].maxAngle =  45
        self.motor['H'].minAngle = -60
        self.motor['H'].maxAngle =  60
        # max speeds from Lilla's email:            -> motor.angleFromStringLength(motor.initialLength + lengthPerSecondInMM)
        # Head -        2 inches in .5 seconds      -> 456 degrees /sec (1.25 revolutions /sec)
        # Shoulder - 	.5 inch in .25 seconds      -> 228 degrees /sec (0.75 revolution / sec)
        # Rt Arm - 		12 inches in 1 second       -> 1369 degrees / sec (3.8 revolutions / sec)
        # Rt Hand - 	12 inches in 1 second       -> 1369 degrees / sec
        # Left Arm - 	25 inches in 1 second       -> 2853 degrees / sec (8 revolutions / sec)
        # Left Hand -	25 inches in 1 second       -> 2853 degrees / sec
        # Rt. Foot -	2 inches in .5 seconds      -> 456 degrees /sec
        # Left Foot - 	2 inches in .5 seconds      -> 456 degrees /sec
        self.motor['HR'].maxSpeed = 456
        self.motor['HL'].maxSpeed = 456
        self.motor['SR'].maxSpeed = 228
        self.motor['SL'].maxSpeed = 228
        self.motor['AR'].maxSpeed = 1369
        self.motor['WR'].maxSpeed = 1369
        self.motor['AL'].maxSpeed = 2853
        self.motor['WL'].maxSpeed = 2853
        self.motor['FR'].maxSpeed = 456
        self.motor['FL'].maxSpeed = 456
        # Rotation motors
        self.motor['H'].maxSpeed = 10
        # BUG: Shoulders can go up to 32, but then:
        # After the first command asking for a speed higher than 32, the
        # shoulders motor can't rotate anymore and Arduino needs to be restarted
        self.motor['S'].maxSpeed = 32
        # TODO: Update values
        self.motor['EX'].maxSpeed = 32
        self.motor['EY'].maxSpeed = 32

        # Eyes
        self.eye = {}
        self.eyeList = []
        for key in ['ER', 'EL']:
            self.eye[key] = Eye('eye' + key)
            self.eyeList.append(self.eye[key])

        # Define the path from one reference space to world
        self.pathToWorld = {}
        self.pathToWorld[self.motor['S']]  = []
        self.pathToWorld[self.motor['SR']] = [self.motor['S']]
        self.pathToWorld[self.motor['SL']] = [self.motor['S']]
        self.pathToWorld[self.motor['AR']] = [self.motor['S']]
        self.pathToWorld[self.motor['AL']] = [self.motor['S']]
        self.pathToWorld[self.motor['H']]  = [] # or [self.motor['S']] if moving with S
        self.pathToWorld[self.motor['HR']] = [self.motor['H']]
        self.pathToWorld[self.motor['HL']] = [self.motor['H']]
        self.pathToWorld[self.motor['FR']] = []
        self.pathToWorld[self.motor['FL']] = []
        self.pathToWorld[self.motor['WR']] = []
        self.pathToWorld[self.motor['WL']] = []
        # TODO: Also depends on HL and HR
        self.pathToWorld[self.motor['EX']] = [self.motor['H']]
        self.pathToWorld[self.motor['EY']] = [self.motor['H']]

        # From these dimensions we get the transform matrices from one referenceSpace to another (with no rotation of the motors)
        self.initialAToB = {}
        self.initialAToB[self.motor['S']] = {}
        self.initialAToB[self.motor['S']]['World'] = np.identity(4)
        self.initialAToB[self.motor['S']]['World'][2][3] = -rod_O_S

        # Initial transform of motors related to the Shoulder space (S)
        for key in ['SR', 'SL', 'AR', 'AL']:
            self.initialAToB[self.motor[key]] = {}
            self.initialAToB[self.motor[key]][self.motor['S']] = RotateX(Translate(np.identity(4), offset[key]), -90)

        self.initialAToB[self.motor['H']] = {}
        self.initialAToB[self.motor['H']]['World'] = np.identity(4)
        self.initialAToB[self.motor['H']]['World'][2][3] = -rod_O_S - rod_S_H

        # Initial transform of motors related to the Head space (H)
        for key in ['HR', 'HL']:
            self.initialAToB[self.motor[key]] = {}
            self.initialAToB[self.motor[key]][self.motor['H']] = RotateX(Translate(np.identity(4), offset[key]), -90)

        # Initial transform of motors related to the ceiling space (World)
        for key in ['FR', 'FL', 'WR', 'WL']:
            self.initialAToB[self.motor[key]] = {}
            self.initialAToB[self.motor[key]]['World'] = RotateX(Translate(np.identity(4), offset[key]), -90)

        # Initial transform of motors related to the eyes
        for key in ['EX', 'EY']:
            self.initialAToB[self.motor[key]] = {}
            self.initialAToB[self.motor[key]][self.motor['H']] = np.identity(4)

        # Sanity check: makes sure all path inital tranforms have been defined
        for srcMotor, path in self.pathToWorld.items():
            if srcMotor not in self.initialAToB.keys():
                print "ERROR: Undefined initial transform from ", srcMotor.name, " To anything"
            for destMotor in path:
                if destMotor not in self.initialAToB[srcMotor].keys():
                    print "ERROR: Undefined initial transform from ", srcMotor.name, " To ", destMotor.name
                srcMotor = destMotor
            if 'World' not in self.initialAToB[srcMotor].keys():
                print "ERROR: Undefined initial transform from ", srcMotor.name, " To World"

        # # Marionettes attachment points position
        # self.nodes = {}
        # for key in ['SR', 'SL', 'AR', 'AL', 'HR', 'HL', 'FR', 'FL', 'WR', 'WL', 'ER', 'EL']:
        #     self.nodes[key] = [0, 0, 0]
        #
        # # Truss for the Head position (0: motorHR, 1: motorHL, 2: headR, 3: headL)
        # headEdges = np.array([[0, 1], [0, 2], [2, 3], [1, 3]])
        # headAnchors = np.array([0, 1])
        # self.trussHead = truss(4, headEdges, headAnchors)
        #
        # # Truss for the Shoulders and Arms position
        # # (0: motorSR, 1: motorSL, 2: motorAR, 3: motorAL, 4: motorWR, 5:motorWL,
        # #  6: shoulderR, 7:shoulderL, 8: armR, 9:armL, 10: wristR, 11: wristL)
        # shouldersEdges = np.array([[0, 1], [0, 6], [6, 7], [1, 7],
        #                             [6, 8], [8, 2], [8, 10], [10, 4],
        #                             [7, 9], [9, 3], [9, 11], [11, 5]])
        # shouldersAnchors = np.array([0, 1, 2, 3, 4, 5])
        # self.trussShoulders = truss(12, shouldersEdges, shouldersAnchors)
        #
        # # Compute initial positions
        # self.computeNodesPosition()


    def setAngles(self, angles):
        """ Set the motor angles in the following order:
            'S', 'SR', 'SL', 'AR', 'AL', 'H', 'HR', 'HL', 'FR', 'FL', 'WR', 'WL', 'EX', 'EY'
        """
        if len(angles) != len(self.motorList):
            # print "angles = ", angles
            raise InvalidAnglesNumberError
        for m, a in zip(self.motorList, angles):
            m.angle = a


    def getAngles(self):
        """ Get the current motor angles in the following order:
            'S', 'SR', 'SL', 'AR', 'AL', 'H', 'HR', 'HL', 'FR', 'FL', 'WR', 'WL', 'EX', 'EY'
        """
        angles = []
        for m in self.motorList:
            angles.append(m.angle)
        return angles


    # Following code used to compute the position of the marionette in 3D space
    # using the angles of the motors. Not used anymore.

    # def circleIntersect(self, o, o1, r1, o2, r2):
    #     """Returns the intersection points of 2 circles
    #         o1: center of circle1
    #         r1: radius of circle1
    #         o2: center of circle2
    #         r2: radius of circle2
    #         o:  define the circles plane [o1 o2 o]
    #         http://mathworld.wolfram.com/Sphere-SphereIntersection.html
    #     """
    #     # In circle1 referenceSpace:
    #     d = np.linalg.norm(np.subtract(o1, o2))
    #     if d == 0 or d > r1 + r2 or (d < r1 and d < r2):
    #         print "No intersection found: r1 = ", r1, " r2 = ", r2, " d = ", d
    #         raise NoIntersectionError
    #
    #     x = (d * d - r2 * r2 + r1 * r1) / (2 * d)
    #     y = r1 * np.sin(np.arccos(x / r1))
    #     p1 = [x, -y, 0]
    #     p2 = [x,  y, 0]
    #
    #     # Transform in World coordinates
    #     circle1ToWorld = BuildTransformMatrix(o1, o2, o)
    #     p1 = TransformPoint(p1, circle1ToWorld)
    #     p2 = TransformPoint(p1, circle1ToWorld)
    #     return [p1, p2]
    #
    #
    # def computeNodesPosition(self):
    #     """Uses the motor angles to compute the marionette's nodes position
    #         If a position cannot be reached returns FALSE and the nodes are not updated
    #     """
    #     ref = ReferenceSpace(self)
    #     xHead = []
    #     xShoulders = []
    #
    #     try:
    #         # Original positions
    #         # Head motors (anchors):
    #         # motorHR (node 0) and motorHL (node 1) positions
    #         for name in ['HR', 'HL']:
    #             motor = self.motor[name]
    #             motorToWorld = ref.motorToWorld(motor)
    #             pos = GetMatrixOrigin(motorToWorld)
    #             xHead.append(pos)
    #         # HR (node 2) is straight down from motorHR (node 0):
    #         motor = self.motor['HR']
    #         lengthHR = motor.stringLengthFromAngle(motor.angle)
    #         pos = [xHead[0][0], xHead[0][1], xHead[0][2] - lengthHR]
    #         xHead.append(pos)
    #         # HL (node 3) is on on intersection of 2 circles:
    #         # circle 1: origin motorHL (node 1), radius length of string HL
    #         # circle 2: origin HR (node 2), radius headWidth
    #         # use motorHR (node 0) to define the plane
    #         motor = self.motor['HL']
    #         lengthHL = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xHead[0], xHead[2], self.headWidth, xHead[1], lengthHL)
    #         xHead.append(inter[0])
    #
    #         # Compute final head positions
    #         xHead = self.trussHead.computeNodesPositions(np.array(xHead))
    #
    #         # Shoulder, arms and wrists motors (anchors)
    #         # motorSR (node 0), motorSL (node 1) positions
    #         # motorAR (node 2), motorAL (node 3) positions
    #         # motorWR (node 4), motorWL (node 5) positions
    #         for name in ['SR', 'SL', 'AR', 'AL', 'WR', 'WL']:
    #             motor = self.motor[name]
    #             motorToWorld = ref.motorToWorld(motor)
    #             pos = GetMatrixOrigin(motorToWorld)
    #             xShoulders.append(pos)
    #         # SR (node 6) is straight down from motorSR (node 0):
    #         motor = self.motor['SR']
    #         lengthSR = motor.stringLengthFromAngle(motor.angle)
    #         pos = [xShoulders[0][0], xShoulders[0][1], xShoulders[0][2] - lengthSR]
    #         xShoulders.append(pos)
    #         # SL (node 7) is on on intersection of 2 circles:
    #         # circle 1: origin motorSL (node 1), radius length of string SL
    #         # circle 2: origin SR (node 6), radius shoulderWidth
    #         # use motorSR (node 0) to define the plane
    #         motor = self.motor['SL']
    #         lengthSL = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xShoulders[0], xShoulders[6], self.shoulderWidth, xShoulders[1], lengthSL)
    #         xShoulders.append(inter[0])
    #         # AR (node 8) is on on intersection of 2 circles:
    #         # circle 1: origin motorAR (node 2), radius length of string AR
    #         # circle 2: origin SR (node 6), radius armLengthR
    #         # use motorSR (node 0) to define the plane
    #         motor = self.motor['AR']
    #         lengthAR = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xShoulders[0], xShoulders[6], self.armLengthR, xShoulders[2], lengthAR)
    #         xShoulders.append(inter[0])
    #         # AL (node 9) is on on intersection of 2 circles:
    #         # circle 1: origin motorAL (node 3), radius length of string AL
    #         # circle 2: origin SL (node 7), radius armLengthL
    #         # use motorSL (node 1) to define the plane
    #         motor = self.motor['AL']
    #         lengthAL = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xShoulders[1], xShoulders[7], self.armLengthL, xShoulders[3], lengthAL)
    #         xShoulders.append(inter[0])
    #         # WR (node 10) is on on intersection of 2 circles:
    #         # circle 1: origin motorWR (node 4), radius length of string WR
    #         # circle 2: origin AR (node 8), radius forearmLengthR
    #         # use motorAR (node 2) to define the plane
    #         motor = self.motor['WR']
    #         lengthWR = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xShoulders[2], xShoulders[8], self.forearmLengthR, xShoulders[4], lengthWR)
    #         xShoulders.append(inter[0])
    #         # WL (node 11) is on on intersection of 2 circles:
    #         # circle 1: origin motorWL (node 5), radius length of string WL
    #         # circle 2: origin AL (node 9), radius forearmLengthL
    #         # use motorAL (node 3) to define the plane
    #         motor = self.motor['WL']
    #         lengthWL = motor.stringLengthFromAngle(motor.angle)
    #         inter = self.circleIntersect(xShoulders[3], xShoulders[9], self.forearmLengthL, xShoulders[5], lengthWL)
    #         xShoulders.append(inter[0])
    #
    #         # Compute final shoulders, arms and wrists positions
    #         xShoulders = self.trussShoulders.computeNodesPositions(np.array(xShoulders))
    #
    #     except:
    #         # The position was not valid
    #         # TODO: record invalid pos???
    #         print "Invalid position"
    #         return False
    #
    #     # Everything went fine in the computation:
    #     # Update the marionette's nodes
    #     idx = 2
    #     for key in ['HR', 'HL']:
    #         self.nodes[key] = xHead[idx * 3 : (idx + 1) * 3]
    #         idx = idx + 1
    #
    #     idx = 6
    #     for key in ['SR', 'SL', 'AR', 'AL', 'WR', 'WL']:
    #         self.nodes[key] = xShoulders[idx * 3 : (idx + 1) * 3]
    #         idx = idx + 1
    #
    #     # Foot points are straight down from their motors (for now)
    #     # TODO: Improve this part (use a truss ???)
    #     for key in ['FR', 'FL']:
    #         motor = self.motor[key]
    #         motorToWorld = ref.motorToWorld(motor)
    #         pointInMotor = motor.getStringPoint()
    #         self.nodes[key] = TransformPoint(pointInMotor, motorToWorld)
    #
    #     # Eyes position
    #     for key in ['ER', 'EL']:
    #         eye = self.eye[key]
    #         eyeToWorld = ref.eyeToWorld(eye)
    #         self.nodes[key] = GetMatrixOrigin(eyeToWorld)
    #
    #     return True
    #
    #
    # def computeMotorAnglesFromNodes(targetPos):
    #     """Inverse operation of computeNodesPosition
    #         Get the motors angle to put the marionette in a given position
    #         targetPos: list of nodes positions in the following order:
    #         'HR', 'HL', 'SR', 'SL', 'AR', 'AL', 'WR', 'WL', 'FR', 'FL'
    #     """
    #     # TODO: implement Marionette::computeMotorAnglesFromNodes
    #     return []


if __name__ == '__main__':
    # Tests
    np.set_printoptions(suppress=True, precision=2)

    m = Marionette()

    print "InitialAToB"
    for k1 in m.initialAToB.keys():
        for k2 in m.initialAToB[k1].keys():
            if k2 == 'World':
                n = k2
            else:
                n = k2.name
            print k1.name, "To", n
            print m.initialAToB[k1][k2]

    for motor in m.motorList:
        if motor.isStatic:
            print motor.name

            minLength = motor.stringLengthFromAngle(motor.minAngle)
            # convert in inches:
            minLength = minLength * 0.039370079
            print "MinAngle (", motor.minAngle, ") string length is ", minLength, " inches"

            maxLength = motor.stringLengthFromAngle(motor.maxAngle)
            # convert in inches:
            maxLength = maxLength * 0.039370079
            print "MaxAngle (", motor.maxAngle, ") string length is ", maxLength, " inches"
