 #include <AccelStepper.h>
 #define micro_step 16
 
 int speed = 300;
 
 //AccelStepper Xaxis(1, 2, 5); // pin 2 = step, pin 5 = direction
 //AccelStepper Yaxis(1, 3, 6); // pin 3 = step, pin 6 = direction
 //AccelStepper Zaxis(1, 4, 7); // pin 4 = step, pin 7 = direction
 
 AccelStepper Xaxis(1, 50, 51); // pin 3 = step, pin 6 = direction
 AccelStepper Yaxis(1, 48, 49); // pin 4 = step, pin 7 = direction
 AccelStepper Zaxis(1, 46, 47);
 AccelStepper Uaxis(1, 44, 45);
 AccelStepper LHaxis(1, 42, 43);
 AccelStepper RHaxis(1, 40, 41);

 AccelStepper LSaxis(1, 38, 39);
 AccelStepper LAaxis(1, 36, 37);
 AccelStepper RSaxis(1, 34, 35);
 AccelStepper RAaxis(1, 32, 33);

 
 void setup() {
   Xaxis.setMaxSpeed(speed * micro_step);
   Yaxis.setMaxSpeed(speed * micro_step);
   Zaxis.setMaxSpeed(speed * micro_step);
   Uaxis.setMaxSpeed(speed * micro_step);
   LHaxis.setMaxSpeed(speed * micro_step);
   RHaxis.setMaxSpeed(speed * micro_step);
   LSaxis.setMaxSpeed(speed * micro_step);
   LAaxis.setMaxSpeed(speed * micro_step);
   RSaxis.setMaxSpeed(speed * micro_step);
   RAaxis.setMaxSpeed(speed * micro_step);
   Xaxis.setSpeed(speed * micro_step);
   Yaxis.setSpeed(speed * micro_step);
   Zaxis.setSpeed(speed * micro_step);
   Uaxis.setSpeed(speed * micro_step);
   LHaxis.setSpeed(speed * micro_step);
   RHaxis.setSpeed(speed * micro_step);
   LSaxis.setSpeed(speed * micro_step);
   LAaxis.setSpeed(speed * micro_step);
   RSaxis.setSpeed(speed * micro_step);
   RAaxis.setSpeed(speed * micro_step);
   
 }
 
 void loop() {  
    Xaxis.runSpeed();
    Yaxis.runSpeed();
    Zaxis.runSpeed();
    Uaxis.runSpeed();
    LHaxis.runSpeed();
    RHaxis.runSpeed();
    LSaxis.runSpeed();
    LAaxis.runSpeed();
    RSaxis.runSpeed();
    RAaxis.runSpeed();
 }

