#include <Servo.h>

// The SFE_LSM9DS1 library requires both Wire and SPI be
// included BEFORE including the 9DS1 library.
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>

//////////////////////////
// LSM9DS1 Library Init //
//////////////////////////
// Use the LSM9DS1 class to create an object. [imu] can be
// named anything, we'll refer to that throught the sketch.
LSM9DS1 imu;

///////////////////////
// Example I2C Setup //
///////////////////////
// SDO_XM and SDO_G are both pulled high, so our addresses are:
#define LSM9DS1_M  0x1E // Would be 0x1C if SDO_M is LOW
#define LSM9DS1_AG  0x6B // Would be 0x6A if SDO_AG is LOW

// Earth's magnetic field varies by location. Add or subtract 
// a declination to get a more accurate heading. Calculate 
// your's here:
// http://www.ngdc.noaa.gov/geomag-web/#declination
#define DECLINATION -6.79 // Declination (degrees) in Miami, FL.


// For eye controls
// Set the pin number for each servo
// They need to be PWM pins
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

  Serial.begin(115200);
  
  // Before initializing the IMU, there are a few settings
  // we may need to adjust. Use the settings struct to set
  // the device's communication mode and addresses:
  imu.settings.device.commInterface = IMU_MODE_I2C;
  imu.settings.device.mAddress = LSM9DS1_M;
  imu.settings.device.agAddress = LSM9DS1_AG;
  // The above lines will only take effect AFTER calling
  // imu.begin(), which verifies communication with the IMU
  // and turns it on.
  if (!imu.begin())
  {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Double-check wiring.");
    while (1)
      ;
  }
  
  servo_lp.attach(left_pitch);
  servo_ly.attach(left_yaw);
  servo_rp.attach(right_pitch);
  servo_ry.attach(right_yaw);
}
 
 
void loop()
{

  if ( imu.accelAvailable() )
  {
    // To read from the accelerometer, first call the
    // readAccel() function. When it exits, it'll update the
    // ax, ay, and az variables with the most current data.
    imu.readAccel();
  }
  if ( imu.magAvailable() )
  {
    // To read from the magnetometer, first call the
    // readMag() function. When it exits, it'll update the
    // mx, my, and mz variables with the most current data.
    imu.readMag();
  }


  if (Serial.available() == 1)
  {
    Serial.read();
    printAttitude(imu.ax, imu.ay, imu.az, 
                 -imu.my, -imu.mx, imu.mz);
  }
                   
  //control the servo's direction and the position of the motor

  if (Serial.available() == num_of_servo)
  {
      servo_lp.write(Serial.read());
      servo_ly.write(Serial.read());
      servo_rp.write(Serial.read());
      servo_ry.write(Serial.read());
      delay(100);
  }
  /*else
  {
    servo_lp.write(90);
    servo_ly.write(90);
    servo_rp.write(90);
    servo_ry.write(90);
    delay(1000);
    servo_lp.write(70);
    servo_ly.write(90);
    servo_rp.write(110);
    servo_ry.write(90);
    delay(1000);
    servo_lp.write(110);
    servo_ly.write(90);
    servo_rp.write(70);
    servo_ry.write(90);
    delay(1000);
    servo_lp.write(90);
    servo_ly.write(70);
    servo_rp.write(90);
    servo_ry.write(70);
    delay(1000);
    servo_lp.write(90);
    servo_ly.write(110);
    servo_rp.write(90);
    servo_ry.write(110);
    delay(1000);
  }
  */
}

// Calculate pitch, roll, and heading.
// Pitch/roll calculations take from this app note:
// http://cache.freescale.com/files/sensors/doc/app_note/AN3461.pdf?fpsp=1
// Heading calculations taken from this app note:
// http://www51.honeywell.com/aero/common/documents/myaerospacecatalog-documents/Defense_Brochures-documents/Magnetic__Literature_Application_notes-documents/AN203_Compass_Heading_Using_Magnetometers.pdf
void printAttitude(float ax, float ay, float az, float mx, float my, float mz)
{
  float roll = atan2(ay, az);
  float pitch = atan2(-ax, sqrt(ay * ay + az * az));
  
  float heading;
  if (my == 0)
    heading = (mx < 0) ? PI : 0;
  else
    heading = atan2(mx, my);
    
  heading -= DECLINATION * PI / 180;
  
  if (heading > PI) heading -= (2 * PI);
  else if (heading < -PI) heading += (2 * PI);
  else if (heading < 0) heading += 2 * PI;
  
  // Convert everything from radians to degrees:
  heading *= 180.0 / PI;
  pitch *= 180.0 / PI;
  roll  *= 180.0 / PI;

  Serial.print(roll,2);
  Serial.print(',');
  Serial.print(pitch,2);
  Serial.print(',');
  Serial.println(heading,2);
  Serial.flush();
}

