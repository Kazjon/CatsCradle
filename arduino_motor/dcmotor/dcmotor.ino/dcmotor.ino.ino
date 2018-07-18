/* Encoder Library - Basic Example
   http://www.pjrc.com/teensy/td_libs_Encoder.html

   This example code is in the public domain.
*/

#include <Encoder.h>

// Change these two numbers to the pins connected to your encoder.
//   Best Performance: both pins have interrupt capability
//   Good Performance: only the first pin has interrupt capability
//   Low Performance:  neither pin has interrupt capability
Encoder myEnc(5, 6);
//   avoid using pins with LEDs attached

int head_speed;
int head_target_angle = 0;
int shoulder_speed;
int shoulder_target_angle = 0;
bool new_head_angle = false;

// required to allow motors to move
// must be called when controller restarts and after any error
void exitSafeStart()
{
  Serial1.write(0x83);
}
 
// speed should be a number from -3200 to 3200
void setMotorSpeed(int speed)
{
  if (speed < 0)
  {
    Serial1.write(0x86);  // motor reverse command
    speed = -speed;  // make speed positive
  }
  else
  {
    Serial1.write(0x85);  // motor forward command
  }
  Serial1.write(speed & 0x1F);
  Serial1.write(speed >> 5);
}



void setup() {
  Serial.begin(115200);
  //Serial.println("Basic Encoder Test:");

  // initialize software serial object with baud rate of 19.2 kbps
  Serial1.begin(19200);
 
  // the Simple Motor Controller must be running for at least 1 ms
  // before we try to send serial data, so we delay here for 5 ms
  delay(5);
 
  // if the Simple Motor Controller has automatic baud detection
  // enabled, we first need to send it the byte 0xAA (170 in decimal)
  // so that it can learn the baud rate
  Serial1.write(0xAA);  // send baud-indicator byte
 
  // next we need to send the Exit Safe Start command, which
  // clears the safe-start violation and lets the motor run
  exitSafeStart();  // clear the safe-start violation and let the motor run
}

void loop() {
  long newPosition = myEnc.read();
  if (Serial.available() == 2)
  {
    char cmd = Serial.read();
    if (cmd == 's')
    {
      
    }
    else if (cmd == 'h')
    {
      head_target_angle = Serial.read();
      if (head_target_angle>90)
      {
        head_target_angle -= 256;
      }
      new_head_angle = true;
    }
  }
  

  if (new_head_angle && (abs(newPosition-head_target_angle * 23) > 10))
  {
    if (newPosition > head_target_angle * 23)
    {
      head_speed = 200;
    }
    else if (newPosition < head_target_angle * 23)
    {
      head_speed = -200;
    }
  }
  else
  {
    head_speed = 0;
    new_head_angle = false;
  }
  
  setMotorSpeed(head_speed);
}
