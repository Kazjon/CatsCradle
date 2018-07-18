/*
  String to Integer conversion

  Reads a serial input string until it sees a newline, then converts the string
  to a number if the characters are digits.

  The circuit:
  - No external components needed.

  created 29 Nov 2010
  by Tom Igoe

  This example code is in the public domain.

  http://www.arduino.cc/en/Tutorial/StringToInt
*/

String inString = "";    // string to hold input

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // send an intro:
  //Serial.println("\n\nString toInt():");
  //Serial.println();
}

void loop() {
  // Read serial input:
  while (Serial.available() > 0) {
    //int inChar = Serial.read();
    byte data[4];
    //Serial.readBytesUntil('z',data, 4);
    int num = Serial.parseInt();
    if (num != 0)
    {
       Serial.print("Value:");
      Serial.println(num);
      
    }
     
      //Serial.print("String: ");
      //Serial.println(data);
      // clear the string for new input:
  }
  /*
   * In [78]: port.write(struct.pack('>cccccc','-','2','3','z','4','5'))
KeyboardInterrupt

In [78]: args = ['-','2','3','z','4','5']

In [79]: port.write(struct.pack('>cccccc',args*))
  File "<ipython-input-79-0c32fcfc9106>", line 1
    port.write(struct.pack('>cccccc',args*))
                                          ^
SyntaxError: invalid syntax


In [80]: port.write(struct.pack('>cccccc',*args))
Out[80]: 6

In [81]: port.readline()
Out[81]: 'Value:-23\r\n'

In [82]: port.readline()
Out[82]: 'Value:45\r\n'

In [83]: a = '>'+'c'*5

In [84]: a
Out[84]: '>ccccc'*/

   */
}
