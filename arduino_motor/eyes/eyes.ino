#include <Servo.h>
 
const int left_pitch = 3;
const int left_yaw = 5;
const int right_pitch = 6;
const int right_yaw = 9;
const int num_of_servo = 4;
 
Servo servo_lp;
Servo servo_ly;
Servo servo_rp;
Servo servo_ry;  
 
int servoAngle = 0;   // servo position in degrees
 
void setup()
{
  Serial.begin(9600);  
  servo_lp.attach(left_pitch);
  servo_ly.attach(left_yaw);
  servo_rp.attach(right_pitch);
  servo_ry.attach(right_yaw);
}
 
 
void loop()
{
//control the servo's direction and the position of the motor

  if (Serial.available() == num_of_servo)
  {
      servo_lp.write(Serial.read());
      servo_ly.write(Serial.read());
      servo_rp.write(Serial.read());
      servo_ry.write(Serial.read());
      delay(100);
  }
  delay(10);
}

