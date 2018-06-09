import serial
import struct

class ArduinoCommunicator(object):
    def __init__(self, port):
        self.serial_port = serial.Serial(port, 9600)

    def send(self, data):
        print "Sending"
        #self.serial_port.write(data)
        self.serial_port.write(struct.pack('>?B?B',False, 45, True, 0))


if __name__ == "__main__":

    import time

    ac = ArduinoCommunicator("COM4")
    while True:
        time.sleep(5)
        ac.send("1,2,3")
