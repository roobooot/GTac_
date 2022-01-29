//sending data by CAN BUS
//#include <Servo.h>
//int servoPin = 9;
//Servo Servo1;
String readString;
int pos_1;
const PROGMEM int pos_1_roof = 55;
const PROGMEM int pos_1_floor = 180;
int pos_2;
const PROGMEM int pos_2_roof = 55;
const PROGMEM int pos_2_floor = 180;
int pos_3;
const PROGMEM int pos_3_roof = 178;
const PROGMEM int pos_3_floor = 3;
int pos_4;
const PROGMEM int pos_4_roof = 6;
const PROGMEM int pos_4_floor = 180;
int pos_5;
const PROGMEM int pos_5_roof = 180;
const PROGMEM int pos_5_floor = 3;
int pos_6;
const PROGMEM int pos_6_roof = 180;
const PROGMEM int pos_6_floor = 3;

#include <Servo.h>
Servo myservo_1;  // create servo object to control a servo
Servo myservo_2;  // create servo object to control a servo
Servo myservo_3;  // create servo object to control a servo
Servo myservo_4;  // create servo object to control a servo
Servo myservo_5;  // create servo object to control a servo
Servo myservo_6;  // create servo object to control a servo

// name init-final 20210515
#define Servo_1 6 //thumb flexion 
#define Servo_2 7 //thumb abduction
#define Servo_3 8 //midlle 
#define Servo_4 9 //index 
#define Servo_5 10 //little 
#define Servo_6 12 //ring 


#include <CD74HC4067.h>
CD74HC4067 my_mux(0, 1, 2, 3);
#define S3 3
#define S2 2
#define S1 1
#define S0 0

#define NUM_Data 41
#define NUM_MAG 6
#define NUM_RES 32 //piezoresistive sensing

int x = 0;

#include <Wire.h>
#include <MLX90393.h> //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo

//MLX90393 mlx;
//MLX90393::txyz data; //Create a structure, called data, of four floats (t, x, y, and z)
//
//MLX90393 mlx_2;
//MLX90393::txyz data_2; //Create a structure, called data, of four floats (t, x, y, and z)

MLX90393 mlx_3;
MLX90393::txyz data_3; //Create a structure, called data, of four floats (t, x, y, and z)

#define TCAADDR 0x70
#define bus1 0
#define bus2 1
//#define bus3 2
//#define bus4 3
//#define bus5 4


#define delay_n (uint8_t)1

#define A_0 4
#define B_0 5

int8_t n = 0; //starting from 0 can make the equavalent number for each column reading
uint8_t col;
uint8_t col_ind;
//int16_t mag_x;
//int16_t mag_y;
//int16_t mag_z;
//int8_t temp;
////int16_t mag_x_2;
////int16_t mag_y_2;
////int16_t mag_z_2;
////int8_t temp_2;
int16_t mag_x_3;
int16_t mag_y_3;
int16_t mag_z_3;
int16_t temp_3;

int16_t data_to_send[NUM_Data];
unsigned long previousTime = micros();
unsigned long timeIntervalData = 5000;// micro seconds, wait to send data
bool SENT = false;
bool TO_GRASP = true;

void print_data(int16_t data_to_send[NUM_Data], int16_t NUM_Data_print) {
//  Serial.print('Data Length:'); //start flag
//  Serial.print(NUM_Data_print);
//  Serial.println(': ');
  for (int i = 0; i < NUM_Data_print; i = i + 1) {
    if (i == NUM_Data_print - 1) {
      Serial.println(data_to_send[i]);
    }
    else {
      Serial.print(data_to_send[i]);
      Serial.print(' ');
    }
  }
  delayMicroseconds(100);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //  Serial.setTimeout(50);
  delay(100);
  // set up mlx90393
  Wire.begin();
//  Wire.setClock(1000000); //at least faster than 1000000, 1000000 is too fast to get correct signal of only two fingers.
  //  //Connect to sensor with I2C address jumpers set: A1 = 1, A0 = 0
  //  //Use DRDY pin connected to A3
  //  //Returns byte containing status bytes
  delay(500);
  activate_finger(bus1);
  activate_finger(bus2);
//  activate_finger(bus3);
//  activate_finger(bus4);
//  activate_finger(bus5);

  delay(100);
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);

  pinMode(S0, OUTPUT);  // sets the pin as output
  pinMode(S1, OUTPUT);  // sets the pin as output
  pinMode(S2, OUTPUT);  // sets the pin as output
  pinMode(S3, OUTPUT);  // sets the pin as output

  delay(100);

  myservo_1.attach(Servo_1);  //the pin for the servo control
  myservo_2.attach(Servo_2);  //the pin for the servo control
  myservo_3.attach(Servo_3);  //the pin for the servo control
  myservo_4.attach(Servo_4);  //the pin for the servo control
  myservo_5.attach(Servo_5);  //the pin for the servo control
  myservo_6.attach(Servo_6);  //the pin for the servo control
  init_motor();// move fingers to initial position
  delay(100);
}

void loop() {
  //  x++;
  //  Servo1.write(x / 90);
  // put your main code here, to run repeatedly:
  //  unsigned long currentMillis = millis();
  unsigned long start = micros();
  if (SENT == true) {
    read_all_data();
    unsigned long end = micros();
    unsigned long delta = end - start;
    data_to_send[38] = myservo_1.read();
    data_to_send[39] = myservo_2.read();
//    data_to_send[287] = myservo_3.read();
//    data_to_send[288] = myservo_4.read();
//    data_to_send[289] = myservo_5.read();
//    data_to_send[290] = myservo_6.read();
    
    data_to_send[NUM_Data - 1] = 1000000 / delta;
    SENT = false;
  }

  // wait for sending data
  unsigned long currentTime = micros();
  if (currentTime - previousTime > timeIntervalData) {
    previousTime = currentTime;
    //print data
   send_data(data_to_send, NUM_Data);
    SENT = true;
  }
  // receive motor command and execute
  move_fingers2();
}

void move_fingers2() {
  // send motor command by "<m1deg1><m2deg2>..."
  bool START_MT = false;
  bool START_DEG = false;
  while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    //    delay(1);
    if (c == '<') {
      START_MT = true;
//      Serial.println("start to read motor");
    }
    if (START_MT == true) {
      char m = Serial.read();
      String motor = m;
      //      delay(1);
      int n = motor.toInt();
//      Serial.print("motor:");
//      Serial.println(n);  //so you can see the captured string
      START_MT = false;
      START_DEG = true;

      String deg = "";
      while (Serial.available() and START_DEG == true) {
        char d = Serial.read();
        //        delay(1);
        if (d == '>') {

          START_DEG = false;
          continue;
        }
        deg += d;
      }
      int degree = deg.toInt();

//      Serial.print("degree:");
//      Serial.println(degree);  //so you can see the captured string
      if (n == 0) {
        init_motor();
      }
      if (n == 1) {
        int dest = myservo_1.read() - degree;
        if (dest >= pos_1_roof && dest <= pos_1_floor) {
          myservo_1.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_1.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_1.read());
        }
      }
      if (n == 2) {
        int dest = myservo_2.read() - degree;
        if (dest >= pos_2_roof && dest <= pos_2_floor) {
          myservo_2.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_2.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_2.read());
        }
      }
      if (n == 3) {
        int dest = myservo_3.read() + degree;
        if (dest <= pos_3_roof && dest >= pos_3_floor) {
          myservo_3.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_3.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_3.read());
        }
      }
      if (n == 4) {
        int dest = myservo_4.read() - degree;
        if (dest >= pos_4_roof && dest <= pos_4_floor) {
          myservo_4.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_4.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_4.read());
        }
      }
      if (n == 5) {
        int dest = myservo_5.read() + degree;
        if (dest <= pos_5_roof && dest >= pos_5_floor) {
          myservo_5.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_5.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_5.read());
        }
      }
      if (n == 6) {
        int dest = myservo_6.read() + degree;
        if (dest <= pos_6_roof && dest >= pos_6_floor) {
          myservo_6.write(dest);
//          Serial.print("current degree:");
//          Serial.println(myservo_6.read());
        }
        else {
//          Serial.println("unable to move, out of range");
//          Serial.print("current degree:");
//          Serial.println(myservo_6.read());
        }
      }
    }
    //    delay(2);  //slow looping to allow buffer to fill with next character
  }
}

void send_data(int16_t data_to_send[NUM_Data], int16_t NUM_Data_print) {
  Serial.write('<'); //start flag
  Serial.write(0x00);
  for (int i = 0; i < NUM_Data_print; i = i + 1) {
    if (i == NUM_Data_print - 1) {
      Serial.write(highByte(data_to_send[i]));
      Serial.write(lowByte(data_to_send[i]));
      Serial.write('>');
    }
    else {
      Serial.write(highByte(data_to_send[i]));
      Serial.write(lowByte(data_to_send[i]));
    }
  }
  delayMicroseconds(100);
}

void init_motor() {
//  Serial.println("initiate position");
  myservo_1.write(pos_1_floor);
  myservo_2.write(pos_2_floor);
  myservo_3.write(pos_3_floor);
  myservo_4.write(pos_4_floor);
  myservo_5.write(pos_5_floor);
  myservo_6.write(pos_6_floor);
}

void pinch_2() {
//  Serial.println("initiate position");
  myservo_1.write(pos_1_floor);
  myservo_2.write(80);
  myservo_3.write(pos_3_floor);
  myservo_4.write(70);
  myservo_5.write(pos_5_floor);
  myservo_6.write(pos_6_floor);
}

void move_thumb_flexion(int8_t deg) {
  int s2_dest = myservo_2.read() - deg;
  if (s2_dest < pos_2_roof) {
    myservo_2.write(pos_2_roof);
  }
  else {
    myservo_2.write(s2_dest);
  }
}

void move_thumb_abd(int8_t deg) {
  int s1_dest = myservo_1.read() - deg;
  if (s1_dest < pos_1_roof) {
    myservo_1.write(pos_1_roof);
  }
  else if (s1_dest > pos_1_floor) {
    myservo_1.write(pos_1_floor);
  }
  else {
    myservo_1.write(s1_dest);
  }
}

void move_index(int8_t deg) {
  int s4_dest = myservo_4.read() - deg;
  if (s4_dest < pos_4_roof) {
    myservo_4.write(pos_4_roof);
  }
  else if (s4_dest > pos_4_floor) {
    myservo_4.write(pos_4_floor);
  }
  else {
    myservo_4.write(s4_dest);
  }
}

void move_mid(int8_t deg) {
  int s3_dest = myservo_3.read() + deg;
  if (s3_dest > pos_3_roof) {
    myservo_3.write(pos_3_roof);
  }
  else if (s3_dest < pos_3_floor) {
    myservo_3.write(pos_3_floor);
  }
  else {
    myservo_3.write(s3_dest);
  }
}

void move_ring(int8_t deg) {
  int s6_dest = myservo_6.read() + deg;
  if (s6_dest > pos_6_roof) {
    myservo_6.write(pos_6_roof);
  }
  else if (s6_dest < pos_6_floor) {
    myservo_6.write(pos_6_floor);
  }
  else {
    myservo_6.write(s6_dest);
  }
}

void move_little(int8_t deg) {
  int s5_dest = myservo_5.read() + deg;
  if (s5_dest > pos_5_roof) {
    myservo_5.write(pos_5_roof);
  }
  else if (s5_dest < pos_5_floor) {
    myservo_5.write(pos_5_floor);
  }
  else {
    myservo_5.write(s5_dest);
  }
}

void pinch(int8_t deg) {
  move_thumb_flexion(deg * 0.5);
  //  move_thumb_abd(deg*0.5);
  move_index(deg);
  //  move_mid(deg);
  //  move_ring(deg);
  //  move_little(deg);
}

void print_all_data(int16_t data_to_send[NUM_Data]) {
  ////print data
  for (byte i = 0; i < NUM_Data; i = i + 1) {
    if (i == NUM_Data - 1) {
      Serial.println(data_to_send[i]);
    }
    else {
      Serial.print(data_to_send[i]);
      Serial.print(' ');
    }
  }
}

void read_all_data() {

  for (uint8_t col = 0; col < 4; col++) {

    //Matrix data
    switch (col) {
      case 0:
        digital_write_COL1();
        n++;
        break;
      case 1:
        digital_write_COL2();
        n++;
        break;
      case 2:
        digital_write_COL3();
        n++;
        break;
      case 3:
        digital_write_COL4();
        n++;
        break;
      case 4:
        digital_write_COL5();
        n++;
        break;
      case 5:
        digital_write_COL6();
        n++;
        break;
      case 6:
        digital_write_COL7();
        n++;
        break;
      case 7:
        digital_write_COL8();
        n++;
        break;
      case 8:
        digital_write_COL9();
        n++;
        break;
      case 9:
        digital_write_COL10();
        n++;
        break;
      case 10:
        digital_write_COL11();
        n++;
        break;
      case 11:
        digital_write_COL12();
        n++;
        break;
    }

    read_resistive_data(&data_to_send[NUM_MAG + 8 * col], &data_to_send[NUM_MAG + 8 * col + 1], &data_to_send[NUM_MAG + 8 * col + 2], &data_to_send[NUM_MAG + 8 * col + 3],
                        &data_to_send[NUM_MAG + 8 * col + 4], &data_to_send[NUM_MAG + 8 * col + 5], &data_to_send[NUM_MAG + 8 * col + 6], &data_to_send[NUM_MAG + 8 * col + 7]);

    //I2C data
    if (col == 3) {
      read_mag_finger(bus1, &data_to_send[0], &data_to_send[1], &data_to_send[2]);
      read_mag_finger(bus2, &data_to_send[3], &data_to_send[4], &data_to_send[5]);
//      read_mag_finger(bus3, &data_to_send[18], &data_to_send[19], &data_to_send[20],
//                      &data_to_send[21], &data_to_send[22], &data_to_send[23],
//                      &data_to_send[24], &data_to_send[25], &data_to_send[26]);
//      read_mag_finger(bus4, &data_to_send[27], &data_to_send[28], &data_to_send[29],
//                      &data_to_send[30], &data_to_send[31], &data_to_send[32],
//                      &data_to_send[33], &data_to_send[34], &data_to_send[35]);
//      read_mag_finger(bus5, &data_to_send[36], &data_to_send[37], &data_to_send[38],
//                      &data_to_send[39], &data_to_send[40], &data_to_send[41],
//                      &data_to_send[42], &data_to_send[43], &data_to_send[44]);
    }
  }
}

void switch_SP4T(byte B_bool, byte A_bool) {
  digitalWrite(A_0, A_bool);
  digitalWrite(B_0, B_bool);
}

void read_resistive_data(int16_t* mat1, int16_t* mat2, int16_t* mat3, int16_t* mat4,
                         int16_t* mat5, int16_t* mat6, int16_t* mat7, int16_t* mat8)
{
  switch_SP4T(LOW, LOW);
  *mat1 = analogRead(A0);
  *mat5 = analogRead(A1);
//  *mat9 = analogRead(A2);
//  *mat13 = analogRead(A3);
//  *mat17 = analogRead(A6);

  switch_SP4T(LOW, HIGH);
  *mat2 = analogRead(A0);
  *mat6 = analogRead(A1);
//  *mat10 = analogRead(A2);
//  *mat14 = analogRead(A3);
//  *mat18 = analogRead(A6);

  switch_SP4T(HIGH, LOW);
  *mat3 = analogRead(A0);
  *mat7 = analogRead(A1);
//  *mat11 = analogRead(A2);
//  *mat15 = analogRead(A3);
//  *mat19 = analogRead(A6);

  switch_SP4T(HIGH, HIGH);
  *mat4 = analogRead(A0);
  *mat8 = analogRead(A1);
//  *mat12 = analogRead(A2);
//  *mat16 = analogRead(A3);
//  *mat20 = analogRead(A6);

  //  int ROW_1 = analogRead(A0);  // read the input pin 0-1023
  //  int ROW_2 = analogRead(A1);  // read the input pin
  //  int ROW_3 = analogRead(A2);  // read the input pin
  //  int ROW_4 = analogRead(A3);  // read the input pin

  //  int read_digital1 = analogRead(A6);
  //  int read_digital2 = analogRead(A7);
  //  int read_digital3 = analogRead(A8);
  //  int read_digital4 = analogRead(A9);

  //  Serial.print(col);      // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_1_0);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_2_0);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_3_0);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_4_0);           // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_1_1);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_2_1);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_3_1);          // debug value
  //  Serial.print(" ");
  //  Serial.print(ROW_4_1);           // debug value
  //  Serial.print(" ");
  //  return;
}

void tcaselect(byte i) {
  if (i > 7) return;
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void activate_finger(byte bus) {
  tcaselect(bus);
//  byte status_1 = mlx.begin(0, 0);
//  delay(200);
//  byte status_2 = mlx_2.begin(0, 1);
//  delay(200);
  byte status_3 = mlx_3.begin(1, 1);
  delay(200);
//  mlx.setGainSel(7);
//  mlx.setResolution(0, 0, 0); //x, y, z
//  mlx.setOverSampling(0);
//  mlx.setDigitalFiltering(0);
//  delay(50);
//
//  mlx_2.setGainSel(7);
//  mlx_2.setResolution(0, 0, 0); //x, y, z
//  mlx_2.setOverSampling(0);
//  mlx_2.setDigitalFiltering(0);
//  delay(50);

  mlx_3.setGainSel(7);
  mlx_3.setResolution(0, 0, 0); //x, y, z
  mlx_3.setOverSampling(0);
  mlx_3.setDigitalFiltering(0);
  delay(100);
}

void read_mag_finger(byte bus, int16_t* mag_x_3, int16_t* mag_y_3, int16_t* mag_z_3) {
  tcaselect(bus);
//  mlx.readData(data); //Read the values from the MXL90393
//  *mag_x = data.x;
//  *mag_y = data.y;
//  *mag_z = data.z;
//  temp = data.t;
//
//  mlx_2.readData(data_2); //Read the values from the MXL90393
//  *mag_x_2 = data_2.x;
//  *mag_y_2 = data_2.y;
//  *mag_z_2 = data_2.z;
//  temp_2 = data_2.t;

  mlx_3.readData(data_3); //Read the values from the MXL90393
  *mag_x_3 = data_3.x;
  *mag_y_3 = data_3.y;
  *mag_z_3 = data_3.z;
  temp_3 = data_3.t;

  return;
}

void digital_write_COL1() {
  //    digitalWrite(IN1, HIGH);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(11);
}

void digital_write_COL2() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, HIGH);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(10);
}

void digital_write_COL3() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, HIGH);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(9);
}

void digital_write_COL4() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, HIGH);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(8);
}
void digital_write_COL5() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, HIGH);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(7);
}
void digital_write_COL6() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, HIGH);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(6);
}
void digital_write_COL7() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, HIGH);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(5);
}
void digital_write_COL8() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, HIGH);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(4);
}
void digital_write_COL9() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, HIGH);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(3);
}
void digital_write_COL10() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, HIGH);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(2);
}
void digital_write_COL11() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, HIGH);
  //    digitalWrite(IN12, LOW);
  my_mux.channel(1);
}
void digital_write_COL12() {
  //    digitalWrite(IN1, LOW);
  //    digitalWrite(IN2, LOW);
  //    digitalWrite(IN3, LOW);
  //    digitalWrite(IN4, LOW);
  //    digitalWrite(IN5, LOW);
  //    digitalWrite(IN6, LOW);
  //    digitalWrite(IN7, LOW);
  //    digitalWrite(IN8, LOW);
  //    digitalWrite(IN9, LOW);
  //    digitalWrite(IN10, LOW);
  //    digitalWrite(IN11, LOW);
  //    digitalWrite(IN12, HIGH);
  my_mux.channel(0);
}
