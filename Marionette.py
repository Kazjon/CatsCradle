from MatrixUtil import *
from Motor import *

#
# Marionette's motors layout
#      S = Shoulder rotation
#      SR/SL = Shoulder Right and Left
#      H = Head rotation (????? question: is the head motor static on the shoulders rod?????)
#      HR/HL = Head Right and Left
#      FR/FL = Foot Right and Left
#      AR/AL = Arm Right and Left
#      WR/WL = Wrist Right and Left
#
#        WR  FR     W     FL   WL    -> Fixed on ceiling
#                   |
#                   |
#        SR_________S__________SL    -> Horizontal rotation (Shoulders)
#          AR__|    |      |__AL
#                   |
#             HR____H____HL          -> Horizontal rotation (Head)
#
#

class Marionette:
    """Hold the marionette physical data"""

    def __init__(self):
        """motors is the list of Motors objects in the following order:
        S, SR, SL, AR, AL, H, HR, HL, FR, FL, WR, WL"""

        # Marionette's dimensions in mm (to be updated)
        rod_O_S = 300 # length of upper vertical rod (shoulders)
        rod_S_H = 200 # length of lower vertical rod (head)
        # Offset definition: Fixed point of the string.
        # Could be a hole in the horizontal rods (for Head and Shoulders)
        # or the last contact point of the string on the motor circonference
        offset = {}
        offset['SR'] = (0, -150, 0) # offset of the motor SR string hole on the right end of shoulders rod
        offset['SL'] = (0,  150, 0) # offset of the motor SL string hole on the left end of shoulders rod
        offset['AR'] = (2, -150, 0) # offset of the motor AR string hole on the right end of shoulders rod
        offset['AL'] = (2,  150, 0) # offset of the motor AL string hole on the left end of shoulders rod
        offset['HR'] = (0, -100, 0) # offset of the motor HR string hole on the right end of the head rod
        offset['HL'] = (0,  100, 0) # offset of the motor HL string hole on the left end of the head rod
        offset['FL'] = (-120,  100, -10) # offset of the motor FL on the ceiling (marionette's top attachment)
        offset['FR'] = (-120, -100, -10) # offset of the motor FR on the ceiling (marionette's top attachment)
        offset['WL'] = ( 150,  150, -10) # offset of the motor WL on the ceiling (marionette's top attachment)
        offset['WR'] = ( 150, -150, -10) # offset of the motor WR on the ceiling (marionette's top attachment)
        self.length = {}
        self.length['SR'] = 400  # Initial length of string on SR (at 0 degrees rotation)
        self.length['SL'] = 400  # Initial length of string on SL (at 0 degrees rotation)
        self.length['AR'] = 600  # Initial length of string on AR (at 0 degrees rotation)
        self.length['AL'] = 600  # Initial length of string on AL (at 0 degrees rotation)
        self.length['HR'] = 100  # Initial length of string on HR (at 0 degrees rotation)
        self.length['HL'] = 100  # Initial length of string on HL (at 0 degrees rotation)
        self.length['FR'] = 1800 # Initial length of string on FR (at 0 degrees rotation)
        self.length['FL'] = 1800 # Initial length of string on FL (at 0 degrees rotation)
        self.length['WL'] = 800  # Initial length of string on WL (at 0 degrees rotation)
        self.length['WR'] = 800  # Initial length of string on WR (at 0 degrees rotation)
        # Non static motors (no string -> length = 0)
        self.length['S'] = 0
        self.length['H'] = 0
        radius = 10 # All motors have the same radius????

        # Motors
        self.motor = {}
        self.motorList = []
        for key in ['S', 'SR', 'SL', 'AR', 'AL', 'H', 'HR', 'HL', 'FR', 'FL', 'WR', 'WL']:
            self.motor[key] = Motor('motor' + key, radius, self.length[key])
            self.motorList.append(self.motor[key])

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
