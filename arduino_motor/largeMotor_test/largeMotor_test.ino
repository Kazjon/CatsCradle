#include <RunningMedian.h>

#include <AccelStepper.h>
#include <Encoder.h>
#include <DueTimer.h>
#include "RunningMedian.h"

#define shoulder_pot_pin 56

// For shoulder rotation
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

//RunningMedian samples = RunningMedian(50);

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
  setupShoulderMotor();

  shoulder_target_position = 0;
  new_shoulder_position = true;
  shoulder_speed = 30;

  ////////////////// this is for head rotation ///////////////////

}

void loop() {

  int shoulder_raw_data = analogRead(shoulder_pot_pin);     // read the input pin

//  samples.add(shoulder_raw_data);
  shoulder_current_reading = shoulder_raw_data;
  shoulder_current_position = map(shoulder_current_reading, shoulder_negative_max, shoulder_positive_max, shoulder_interface_negative_max, shoulder_interface_positive_max);
  Serial.print("Reading from shoulder potentiometer: ");
  Serial.println(shoulder_current_reading);
  // Serial.print("Shoulder current position: ");
  // Serial.println(shoulder_current_position);
  // Serial.print("Shoulder target position: ");
  // Serial.println(shoulder_target_position);

  // Read serial input:
  int speed = 2000;
  int zero = 0;
  bool flag = true;
  while (Serial.available() > 0)
  {
    char cmd_type = Serial.read();
    if (flag)
    {
      if (cmd_type == 'l') // Shoulder spin
      {
        Serial.println("*************************READ*********************************");
        Serial3.write(0x86);  // motor forward command
        Serial3.write(speed & 0xF);
        Serial3.write(speed >> 5);
      } else if (cmd_type == 'r') {
        Serial.println("*************************READ 2*********************************");
        Serial3.write(0x85);  // motor reverse command
        Serial3.write(speed & 0xF);
        Serial3.write(speed >> 5);
      } else if (cmd_type == 's') {
        flag = false;
     }
    } else {
      flag = true;
    }
  }
}

