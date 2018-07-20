import serial
import random
import struct

class ArduinoCommunicator(object):
    def __init__(self, port):
        self.serial_port = serial.Serial(port, 115200, timeout = 1.0)
        self.servo_min = -35
        self.servo_max = 35
        self.head_angle_max = 90
        self.head_angle_min = -90

        self.motor_name_list = ['ls','la','lh','lf','lh','rs','ra','rh','rf','rh']
        self.motor_cmd_dict = {}
        for name in self.motor_name_list:
            self.motor_cmd_dict[name] = 0

        # Wait a bit for the arduino to get ready
        time.sleep(2)

    def send(self, data):
        print "Sending: ", data
        self.serial_port.write(data)
        self.serial_port.flush()

    def receive(self):
        print "Receiving " + self.serial_port.readline()

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
        Check if the look at input is in range defined by servo_max and servo_min
        """
        if angle > self.head_angle_max:
            return False
        if angle < self.head_angle_min:
            return False
        return True

    def move(self, cmd_dict = None):

        if cmd_dict is None: cmd_dict = self.motor_cmd_dict

        # Make sure all motors are given a command
        for name in self.motor_name_list:
            if name not in cmd_dict.keys():
                print "No command given for {!r}, default to 0".format(name)
                cmd_dict[name] = 0

        # First send the command character
        self.send(struct.pack('>c', 'm'))

        # Pack command
        for name in self.motor_name_list:
            # Convert command to string
            cmd = str(cmd_dict[name])+'z'
            # Pack data
            data = struct.pack('>' + 'c'*len(cmd), *cmd)
            # Send
            self.send(data)

    def eyeClose(self):
        self.send(struct.pack('>cBB', 'b', 110, 70))

    def eyeOpen(self):
        self.send(struct.pack('>cBB', 'b', 70, 110))

    def lookAt(self, left_pitch, left_yaw, right_pitch, right_yaw):
        """
        All input are integers. 0 means neutral at that dimension.
        Positive for pitch means look up.
        Positive for yaw means look right.
        """
        offset = 90

        if not self._checkLookAtInput(left_pitch):
            print "Error: Left eye pitch angle {} is out of allowed range.".format(left_pitch)
            return
        if not self._checkLookAtInput(left_yaw):
            print "Error: Left eye yaw angle {} is out of allowed range.".format(left_yaw)
            return
        if not self._checkLookAtInput(right_pitch):
            print "Error: right eye pitch angle {} is out of allowed range.".format(right_pitch)
            return
        if not self._checkLookAtInput(right_yaw):
            print "Error: right eye yaw angle {} is out of allowed range.".format(right_yaw)
            return
        # Send four integers to control the eyes
        self.send(struct.pack('>cBBBB', 'e', -left_pitch + offset, left_yaw + offset, right_pitch + offset, right_yaw + offset))

    def getRPY(self):
        # Send any single character to receive the roll pitch yaw reading.
        self.send(struct.pack('>c', 'a'))
        time.sleep(0.01)
        print self.receive()

    def rotateHead(self, angle):
        if not self._checkHeadAngleInput(angle):
            print "Error: Head angle {} is out of allowed range.".format(angle)
            return
        self.send(struct.pack('>cb', 'h', angle))

if __name__ == "__main__":

    import time

    ac = ArduinoCommunicator("COM4")
    """
    while True:
        a = raw_input("Angle ")
        for i in ac.motor_name_list:
            ac.motor_cmd_dict[i] = random.randint(100,101)
        #ac.motor_cmd_dict['la'] = int(a)
        ac.move()
        time.sleep(1)
    """
