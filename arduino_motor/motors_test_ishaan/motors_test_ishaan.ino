#include <Encoder.h>
#define rxPin 15  // pin 3 connects to smcSerial TX  (not used in this example)
#define txPin 14  // pin 4 connects to smcSerial RX
//Encoder smcSerial = SoftwareSerial(rxPin, txPin);
Encoder smcSerial(rxPin, txPin);
 
// required to allow motors to move
// must be called when controller restarts and after any error
void exitSafeStart()
{
  smcSerial.write(0x83);
}
 
// speed should be a number from -3200 to 3200
void setMotorSpeed(int speed)
{
  if (speed < 0)
  {
    smcSerial.write(0x86);  // motor reverse command
    speed = -speed;  // make speed positive
  }
  else
  {
    smcSerial.write(0x85);  // motor forward command
  }
  smcSerial.write(speed & 0x1F);
  smcSerial.write(speed >> 5);
}
 
void setup()
{
  // initialize software serial object with baud rate of 19.2 kbps
  smcSerial.begin(19200);
 
  // the Simple Motor Controller must be running for at least 1 ms
  // before we try to send serial data, so we delay here for 5 ms
  delay(5);
 
  // if the Simple Motor Controller has automatic baud detection
  // enabled, we first need to send it the byte 0xAA (170 in decimal)
  // so that it can learn the baud rate
  smcSerial.write(0xAA);  // send baud-indicator byte
 
  // next we need to send the Exit Safe Start command, which
  // clears the safe-start violation and lets the motor run
  exitSafeStart();  // clear the safe-start violation and let the motor run
}
 
void loop()
{
  setMotorSpeed(3200);  // full-speed forward
  delay(1000);
  setMotorSpeed(-3200);  // full-speed reverse
  delay(1000);
}
