#include <AccelStepper.h>

//AccelStepper Xaxis(1, 2, 5); // pin 2 = step, pin 5 = direction
//AccelStepper Yaxis(1, 3, 6); // pin 3 = step, pin 6 = direction
//AccelStepper Zaxis(1, 4, 7); // pin 4 = step, pin 7 = direction

AccelStepper Xaxis(1, 50, 51); // pin 3 = step, pin 6 = direction
AccelStepper Yaxis(1, 48, 49); // pin 4 = step, pin 7 = direction

void setup() {
  Xaxis.setMaxSpeed(400);
  Yaxis.setMaxSpeed(400);
  Xaxis.setSpeed(16);
  Yaxis.setSpeed(1);
}

void loop() {  
   Xaxis.runSpeed();
   Yaxis.runSpeed();
}
