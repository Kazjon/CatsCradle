import serial
import random
import struct
import time

class ArduinoCommunicator(object):
    def __init__(self, port = ""):
        self.serial_port = None
        if not port == "":
            try:
                self.serial_port = serial.Serial(port, 115200, timeout = 1.0)
            except:
                print("Invalid port :", port)

        print("Using port : ", self.serial_port)
        
        self.servo_min = -50
        self.servo_max = 50
        self.head_angle_max = 1000
        self.head_angle_min = -1000
        self.shoulder_angle_min = -100
        self.shoulder_angle_max = 137

        self.motor_name_list = ['Right head','Left head','Right hand','Left hand','Left foot','Right foot','Right arm','Left arm','Left shoulder','Right shoulder']
        self.motor_sign_list = [-1, 1, 1, 1, 1, -1, -1, 1, 1, -1]
        self.motor_sign_dict = {}

        self.motor_cmd_dict = {}
        for i, name in enumerate(self.motor_name_list):
            self.motor_cmd_dict[name] = 0
            self.motor_sign_dict[name] = self.motor_sign_list[i]

        # Wait a bit for the arduino to get ready
        time.sleep(2)

    def send(self, data):
        print("Sending: ", data)
        if self.serial_port is not None:
            self.serial_port.write(data)
            self.serial_port.flush()

    def receive(self):
        print("Receiving " + self.serial_port.readline())

    def _checkLookAtInput(self, angle):
        """
        Check if the look at input is in range defined by servo_max and servo_min
        """
        if angle > self.servo_max:
            return False
        if angle < self.servo_min:
            return False
        return True

    def _checkHeadAngleInput(self, angle):
        """
        """
        if angle > self.head_angle_max:
            return False
        if angle < self.head_angle_min:
            return False
        return True

    def _checkShoulderAngleInput(self, angle):
        """
        """
        if angle > self.shoulder_angle_max:
            return False
        if angle < self.shoulder_angle_min:
            return False
        return True

    def move(self, cmd_dict = None):

        if cmd_dict is None: cmd_dict = self.motor_cmd_dict

        # Make sure all motors are given a command
        for name in self.motor_name_list:
            if name not in list(cmd_dict.keys()):
                print("No command given for {!r}, default to 0".format(name))
                cmd_dict[name] = 0

        # First send the command character
        self.send(struct.pack('>c', 'm'))

        # Pack command
        for name in self.motor_name_list:
            # Convert command to string
            cmd = str(self.motor_sign_dict[name] * cmd_dict[name])+'z'
            # Pack data
            data = struct.pack('>' + 'c'*len(cmd), *cmd)
            # Send
            self.send(data)

    def eyeClose(self):
        self.send(struct.pack('>cBBBB', 'b', 120, 60, 0, 0))

    def eyeOpen(self):
        self.send(struct.pack('>cBBBB', 'b', 70, 110, 0, 0))

    def lookAt(self, left_pitch, left_yaw, right_pitch, right_yaw):
        """
        All input are integers. 0 means neutral at that dimension.
        Positive for pitch means look up.
        Positive for yaw means look right.
        """
        offset = 90

        if not self._checkLookAtInput(left_pitch):
            print("Error: Left eye pitch angle {} is out of allowed range.".format(left_pitch))
            return
        if not self._checkLookAtInput(left_yaw):
            print("Error: Left eye yaw angle {} is out of allowed range.".format(left_yaw))
            return
        if not self._checkLookAtInput(right_pitch):
            print("Error: right eye pitch angle {} is out of allowed range.".format(right_pitch))
            return
        if not self._checkLookAtInput(right_yaw):
            print("Error: right eye yaw angle {} is out of allowed range.".format(right_yaw))
            return
        # Send four integers to control the eyes
        self.send(struct.pack('>cBBBB', 'e', -left_pitch + offset, left_yaw + offset, right_pitch + offset, right_yaw + offset))

    def getRPY(self):
        # Send any single character to receive the roll pitch yaw reading.
        self.send(struct.pack('>c', 'a'))
        time.sleep(0.01)
        print(self.receive())

    def rotateHead(self, angle, speed = 4):
        if not self._checkHeadAngleInput(angle):
            print("Error: Head angle {} is out of allowed range.".format(angle))
            return
        cmd = 'h,' + str(angle) + ',' + str(speed)
        self.send(cmd)
        # self.send(struct.pack('>cbb', 'h', angle, speed))

    def rotateShoulder(self, angle, speed = 10):
        if not self._checkShoulderAngleInput(angle):
            print("Error: Shoulder angle {} is out of allowed range.".format(angle))
            return
        cmd = 's,' + str(angle) + ',' + str(speed)
        self.send(cmd)
        # self.send(struct.pack('>cbb', 's', angle, speed))

    def rotateStringMotor(self, id, angle, speed = 10):
        cmd = 'm,' + str(id) + ',' + str(angle) + ',' + str(speed)
        self.send(cmd)
        # self.send(struct.pack('>cbb', 'm', id, angle, speed))

    def rotateEyes(self, angleX, angleY, speedX, speedY):
        cmd = 'e,' + str(angleX) + ',' + str(angleY) + ',' + str(speedX) + ',' + str(speedY)
        self.send(cmd)
        # self.send(struct.pack('>cbb', 'e', angleX, angleY, speedX, speedY))

    def receiveLines(self, num_of_times):
        for i in range(num_of_times):
            self.receive()

    def stopAllSteppers(self):
        self.setAllSteppers(0)

    def setAllSteppers(self,speed):
        for name in self.motor_name_list:
            self.motor_cmd_dict[name] = speed
        self.move()

    def backforth(self, speed):
        while True:
            self.setAllSteppers(speed)
            time.sleep(2)
            self.setAllSteppers(-speed)
            time.sleep(2)

    def shake(self):
        self.motor_cmd_dict['lshoulder'] = -30
        self.motor_cmd_dict['rshoulder'] = -30
        self.move()
        time.sleep(0.3)
        self.motor_cmd_dict['lshoulder'] = 30
        self.motor_cmd_dict['rshoulder'] = 30
        self.move()
        time.sleep(0.3)
        self.stopAllSteppers()

    def shakeHead(self, speed, peroid):
        self.motor_cmd_dict['lhead'] = -speed
        self.motor_cmd_dict['rhead'] = -speed
        self.move()
        time.sleep(peroid)
        self.motor_cmd_dict['lhead'] = speed
        self.motor_cmd_dict['rhead'] = speed
        self.move()
        time.sleep(peroid)
        self.stopAllSteppers()

    def testMotor(self, name, speed, period):
        self.motor_cmd_dict[name] = speed
        self.move()
        time.sleep(period)
        self.stopAllSteppers()



if __name__ == "__main__":

    import time

    ac = ArduinoCommunicator("COM8")
    """
    while True:
        a = raw_input("Angle ")
        for i in ac.motor_name_list:
            ac.motor_cmd_dict[i] = random.randint(100,101)
        #ac.motor_cmd_dict['la'] = int(a)
        ac.move()
        time.sleep(1)
    """
