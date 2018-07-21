#include <AccelStepper.h>
#include <Encoder.h>
#include <DueTimer.h>

// For motors other than shoulder and head rotation
const int num_of_motors = 10;
int motors_cmd[num_of_motors];
AccelStepper motors[num_of_motors];
int motor_start_pin = 51;

// For head rotation
int head_speed;
int head_target_angle = 0;
bool new_head_angle = false;
Encoder myEnc(5, 6);
long head_current_angle = 0;

// For shoulder rotation
#define shoulder_pot_pin 56
int shoulder_speed;
int shoulder_target_angle = 0;
bool new_shoulder_angle = false;
int shoulder_current_angle = 0;

void setupMotors() {
  for (int i = 0; i < num_of_motors; i++)
  {
    int step_pin = motor_start_pin - 2 * i -1;
    int dire_pin = motor_start_pin - 2 * i;
    motors[i] = AccelStepper(1, step_pin, dire_pin);
    motors[i].setMaxSpeed(1000 * 16);
  }

  Timer3.attachInterrupt(runAllMotors).start(100);
}

void setupHeadMotor() {
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
  Serial1.write(0x83);  // clear the safe-start violation and let the motor run
}

void runHeadMotor() {
  if (new_head_angle && (abs(head_current_angle-head_target_angle * 23) > 10))
  {
    if (head_current_angle > head_target_angle * 23)
    {
      head_speed = -400;
    }
    else if (head_current_angle < head_target_angle * 23)
    {
      head_speed = 400;
    }
  }
  else
  {
    head_speed = 0;
    new_head_angle = false;
  }
  setMotorSpeed('h', head_speed);
}

void runShoulderMotor() {
  if (new_shoulder_angle && (abs(shoulder_current_angle-shoulder_target_angle * 10) > 5))
  {
    if (shoulder_current_angle > shoulder_target_angle * 10)
    {
      //Serial.println("Going ccw");
      shoulder_speed = 1000;
    }
    else if (shoulder_current_angle < shoulder_target_angle * 10)
    {
      shoulder_speed = -1000;
      //Serial.println("Going cw");
    }
  }
  else
  {
    shoulder_speed = 0;
    new_shoulder_angle = false;
  }
  setMotorSpeed('s', shoulder_speed);
}


// speed should be a number from -3200 to 3200
void setMotorSpeed(char motor_id, int speed)
{
  if (speed < 0)
  {
    if (motor_id == 'h')
    {
      Serial1.write(0x86);  // motor reverse command
    }
    else if (motor_id == 's')
    {
      Serial2.write(0x86);  // motor reverse command
    }
    speed = -speed;  // make speed positive
  }
  else
  {
    if (motor_id == 'h')
    {
      Serial1.write(0x85);  // motor forwardrse command
    }
    else if (motor_id == 's')
    {
      Serial2.write(0x85);  // motor forward command
    }
  }

  if (motor_id == 'h')
  {
    Serial1.write(speed & 0x1F);
    Serial1.write(speed >> 5);
  }
  else if (motor_id == 's')
  {
    Serial2.write(speed & 0x1F);
    Serial2.write(speed >> 5);
  }
}

void setupShoulderMotor() {
  // initialize software serial object with baud rate of 19.2 kbps
  Serial2.begin(19200);
  // the Simple Motor Controller must be running for at least 1 ms
  // before we try to send serial data, so we delay here for 5 ms
  delay(5);
 
  // if the Simple Motor Controller has automatic baud detection
  // enabled, we first need to send it the byte 0xAA (170 in decimal)
  // so that it can learn the baud rate
  Serial2.write(0xAA);  // send baud-indicator byte
 
  // next we need to send the Exit Safe Start command, which
  // clears the safe-start violation and lets the motor run
  Serial2.write(0x83);  // clear the safe-start violation and let the motor run
}

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  setupMotors();
  setupHeadMotor();
  setupShoulderMotor();

  ////////////////// this is for head rotation ///////////////////
  
}

void runAllMotors() {
  for (int i = 0; i < num_of_motors; i++)
  {
    motors[i].runSpeed();
  }
}

void loop() {

  shoulder_current_angle = analogRead(shoulder_pot_pin);     // read the input pin
  shoulder_current_angle -= 400;

  // Read encoders
  head_current_angle = myEnc.read();
  
  // Read serial input:
  while (Serial.available() > 0) 
  {
    char cmd_type = Serial.read();
    if (cmd_type == 'm') // Move all motors
    {
      for (int i = 0; i < 10; ++i)
      {
        int num = Serial.parseInt();
        char end_char = Serial.read();
        //Serial.println(num * 16);
        motors[i].setSpeed(num * 16);
      }
    }
    else if (cmd_type == 's') // Shoulder spin
    {
      shoulder_target_angle = Serial.read();
      if (shoulder_target_angle>90)
      {
        shoulder_target_angle -= 256;
      }
      new_shoulder_angle = true;
    }
    else if (cmd_type == 'h') // Head spin
    {
      head_target_angle = Serial.read();
      if (head_target_angle>90)
      {
        head_target_angle -= 256;
      }
      new_head_angle = true;
    }
  }
  
  runHeadMotor();
  runShoulderMotor();
  runAllMotors();
}
