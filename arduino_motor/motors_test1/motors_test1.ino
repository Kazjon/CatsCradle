#include <AccelStepper.h>

const int num_of_motors = 2;
int motors_cmd[num_of_motors];
AccelStepper motors[num_of_motors];
int motor_start_pin = 51;

void setupMotors() {
  for (int i = 0; i < num_of_motors; i++)
  {
    int step_pin = motor_start_pin - 2 * i -1;
    int dire_pin = motor_start_pin - 2 * i;
    motors[i] = AccelStepper(1, step_pin, dire_pin);
  }
}

int angle2Count(int angle) {
  return 0.5556 * (float) angle;
}

void setup() {
  Serial.begin(9600); // set the baud rate
}

void runAllMotors() {
  for (int i = 0; i < num_of_motors; i++)
  {
    motors[i].run();
  }
}

void loop() { 
  if (Serial.available() == 2 * num_of_motors)
  {
    for (int i = 0; i < num_of_motors; i++)
    {
      if (Serial.read())
      {
        motors_cmd[i] = -1 * Serial.read();
      }
      else
      {
        motors_cmd[i] = Serial.read();
      }
      motors[i].setSpeed(angle2Count(motors_cmd[i]));
      //motors[i].move(angle2Count(motors_cmd[i]));
    }

    //Serial.println(motors_cmd[1]);
  }
  
  //runAllMotors();
}
