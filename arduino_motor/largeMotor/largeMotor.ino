#include <RunningMedian.h>

#include <AccelStepper.h>
#include <Encoder.h>
#include <DueTimer.h>
#include "RunningMedian.h"

#define DEBUG 0

// For motors other than shoulder and head rotation
const int num_of_motors = 10;
int motors_cmd[num_of_motors];
AccelStepper motors[num_of_motors];
int motor_start_pin = 51;

// For head rotation
float head_speed = 4.0;
int head_target_position = 0;
bool new_head_position = false;
Encoder myEnc(5, 6);
int head_current_position = 0;
int head_current_reading = 0;
#define head_negative_max -2837
#define head_positive_max 2837
#define head_interface_negative_max -1000
#define head_interface_positive_max 1000
#define medium_head_speed 2.5
#define slow_head_speed 2

// For shoulder rotation
#define shoulder_pot_pin 56
int shoulder_speed = 10;
int shoulder_target_position = 0;
bool new_shoulder_position = false;
int shoulder_current_position = 0;
int shoulder_current_reading = 600;
#define shoulder_negative_max 965
#define shoulder_positive_max 50
#define shoulder_interface_negative_max -100
#define shoulder_interface_positive_max 137
//fix it so that it goes from -100 to +120 with 0 at the known 0 value

RunningMedian samples = RunningMedian(50);

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
  if (DEBUG > 0) {
    Serial.begin(19200);
  }
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
  // 0: 0
  //max negative (-100): -2837, max positive (100): 2837
  float speed_cmd = 0.0;
  int position_diff = abs(head_current_position - head_target_position);
//  if (new_head_position && position_diff > 0)
  if (position_diff > 10)
  {
    if (head_current_position > head_target_position)
    //move in the negative direction
    {
      if (position_diff > 300)
      //regular speed
      {
        speed_cmd = -1.0 * head_speed * 100.0;
      } else if (position_diff <= 300 && position_diff > 100)
      //medium speed
      {
        //get the slowdown to be proportional
        speed_cmd = -1.0 * medium_head_speed * 100.0;
      } else
      //slowest speed
      {
        speed_cmd = -1.0 * slow_head_speed * 100.0;
      }

    }
    else if (head_current_position < head_target_position)
    //move in the positive direction
    {
      if (position_diff >= 300)
      //regular speed
      {
        speed_cmd = 1.0 * head_speed * 100.0;
      } else if (position_diff <= 300 && position_diff > 100)
      //medium speed
      {
        speed_cmd = 1.0 * medium_head_speed * 100.0;
      } else
      //slowest speed
      {
        speed_cmd = 1.0 * slow_head_speed * 100.0;
      }
    }
    else
    {
      speed_cmd = 0.0;
      new_head_position = false;
    }
  } else
  {
    speed_cmd = 0.0;
    new_head_position = false;
  }
    setMotorSpeed('h', (int)speed_cmd);
}

void runShoulderMotor() {
  // 0: 600
  //max negative (-100): 967, max positive (100): 50
  int speed_cmd = 0;
  if (new_shoulder_position && abs(shoulder_current_position - shoulder_target_position) >= 3)
  {
    if (shoulder_current_position > shoulder_target_position)
    {
      speed_cmd = -1 * shoulder_speed * 100;
    }
    else if (shoulder_current_position < shoulder_target_position)
    {
      speed_cmd = 1 * shoulder_speed * 100;
    }
    else {
      speed_cmd = 0;
      new_shoulder_position = false;
    }
  }
  else
  {
    speed_cmd = 0;
    new_shoulder_position = false;
  }
  setMotorSpeed('s', speed_cmd);
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
      Serial3.write(0x86);  // motor reverse command
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
      Serial3.write(0x85);  // motor forward command
    }
  }

  if (motor_id == 'h')
  {
    Serial1.write(speed & 0x1F);
    Serial1.write(speed >> 5);
  }
  else if (motor_id == 's')
  {
    Serial3.write(speed & 0x1F);
    Serial3.write(speed >> 5);
  }
}

void setupShoulderMotor() {
  // initialize software serial object with baud rate of 19.2 kbps
  Serial3.begin(19200);
  // the Simple Motor Controller must be running for at least 1 ms
  // before we try to send serial data, so we delay here for 5 ms
  delay(5);

  // if the Simple Motor Controller has automatic baud detection
  // enabled, we first need to send it the byte 0xAA (170 in decimal)
  // so that it can learn the baud rate
  Serial3.write(0xAA);  // send baud-indicator byte

  // next we need to send the Exit Safe Start command, which
  // clears the safe-start violation and lets the motor run
  Serial3.write(0x83);  // clear the safe-start violation and let the motor run
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

  shoulder_target_position = 0;
  new_shoulder_position = true;
  shoulder_speed = 30;

  ////////////////// this is for head rotation ///////////////////

}

void runAllMotors() {
  for (int i = 0; i < num_of_motors; i++)
  {
    motors[i].runSpeed();
  }
}

void loop() {
  delay(100);

  int shoulder_raw_data = analogRead(shoulder_pot_pin);     // read the input pin

  samples.add(shoulder_raw_data);
  shoulder_current_reading = samples.getMedian();
  shoulder_current_position = map(shoulder_current_reading, shoulder_negative_max, shoulder_positive_max, shoulder_interface_negative_max, shoulder_interface_positive_max);
  if (DEBUG == 1) {
    Serial.print("Reading from shoulder potentiometer: ");
    Serial.println(shoulder_current_reading);
    Serial.print("Shoulder current position: ");
    Serial.println(shoulder_current_position);
  }
  // shoulder_current_position -= 425;

  // Read encoders
  head_current_reading = myEnc.read();
  head_current_position = map(head_current_reading, head_negative_max, head_positive_max, head_interface_negative_max, head_interface_positive_max);
  if (DEBUG == 2) {
    Serial.print("Reading from head encoder: ");
    Serial.println(head_current_reading);
    Serial.print("Head current position: ");
    Serial.println(head_current_position);
    Serial.print("Head target position: ");
    Serial.println(head_target_position);
  }

  // Read serial input:
  while (Serial.available() > 0)
   {
     char cmd_type = Serial.read();
     if (cmd_type == 'd') // Debug steppers - using left hand
     {
       //read out a comma
       Serial.read();
       int num = Serial.parseInt();
       //read out a comma
       Serial.read();
       int motor_to_move_for_debug = 5;
       motors[motor_to_move_for_debug].setSpeed(num * 16);
       if (DEBUG == 3) {
         Serial.print("Setting motor ");
         Serial.print(motor_to_move_for_debug);
         Serial.print(" to speed ");
         Serial.println(num*16);
       }
     }
     else if (cmd_type == 'm') // Move all motors
     {
       for (int i = 0; i < 10; ++i)
       {
         int num = Serial.parseInt();
         char end_char = Serial.read();
         motors[i].setSpeed(num * 16);
         if (DEBUG == 3) {
           Serial.print("Setting motor ");
           Serial.print(i);
           Serial.print(" to speed ");
           Serial.println(num*16);
         }

       }
     }
     else if (cmd_type == 's') // Shoulder spin
     {
       //read out a comma
       Serial.read();
       shoulder_target_position = Serial.parseInt();
       //add limits
       //read out a comma
       Serial.read();
       shoulder_speed = Serial.parseInt();
       // Serial.println('I');
       // Serial.println(shoulder_target_position);
       // Serial.println(shoulder_speed);
       // if (shoulder_target_position>90)
       // {
       //   shoulder_target_position -= 256;
       // }
       new_shoulder_position = shoulder_target_position != shoulder_current_position;
     }
     else if (cmd_type == 'h') // Head spin
     {
       //read out a comma
       Serial.read();
       head_target_position = Serial.parseInt();
       //add limits
       //read out a comma
       Serial.read();
       head_speed = Serial.parseFloat();
       // if (head_target_position>90)
       // {
       //   head_target_position -= 256;
       // }
//       new_head_position = true;
       new_head_position = head_target_position != head_current_position;
     }
   }

   runAllMotors();
   runShoulderMotor();
   runHeadMotor();
}
