
// for (i = 0; i < 9; i = i + 1) {, with ACK and optional encryption
// Sends periodic messages of increasing length to gateway (id=1)
// It also looks for an onboard FLASH chip, if present
// Library and code by Felix Rusu - felix@lowpowerlab.com
// Get the RFM69 and SPIFlash library at: https://github.com/LowPowerLab/

#include <RFM69.h>
#include <SPI.h>
#include <SPIFlash.h>
#include <Time.h>
#include <OneWire.h>
#include <LowPower.h>


#define NODEID 87 //unique for each node on same network
#define NETWORKID 100 //the same on all nodes that talk to each other
#define GATEWAYID 1
//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY RF69_433MHZ
//#define FREQUENCY RF69_868MHZ
//#define FREQUENCY RF69_915MHZ
#define ENCRYPTKEY "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!
#define IS_RFM69HW //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define SERIAL_BAUD 115200
#define LED 9 // Moteinos have LEDs on D9

//////////////////////////////////////////////////////////
// All of the parameters below are fair game to be reprogrammed during execution

int ACK_TIME = 30; // max # of ms to wait for an ack

int MESSAGETYPE=1;         // xmit data message
long TRANSMITPERIOD=10000;  //transmit a packet to gateway so often (in ms)
int ACKRETRYPERIOD=1000;  // 
int ACKRETRIES=5; 
  
int ANODE = 3;
int SEGONE = 4;
int SEGTWO = 5;
int SEGTHREE = 6;
int SEGFOUR = 7;
boolean requestACK = false;

long prevtime = millis();
long looptime;
long elapsedtime = 0;

////////////////////////////////////////

OneWire  ds(14);  // Connect your 1-wire device to pin 14

char payload[] = "123 ABCDEFGHIJKLMNOPQRSTUVWXYZ";
char buff[20];
byte sendSize=0;

SPIFlash flash(8, 0xEF30); //EF40 for 16mbit windbond chip
RFM69 radio;

void setup() {
  Serial.begin(SERIAL_BAUD);
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
//#ifdef IS_RFM69HW
//  radio.setHighPower(); //uncomment only for RFM69HW!
//#endif
  radio.encrypt(ENCRYPTKEY);
  char buff[50];
  sprintf(buff, "\nTransmitting at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
  
  if (flash.initialize())
    Serial.println("SPI Flash Init OK!");
  else
    Serial.println("SPI Flash Init FAIL! (is chip present?)");
}

long lastPeriod = -1;
void loop() {
  
  radio.sleep();
  
  // Everything defined in this loop is permanent
  
  long SOURCEID=87;
  long DESTID=1;
  
  //process any serial input
  if (Serial.available() > 0)
  {
    char input = Serial.read();
    if (input >= 48 && input <= 57) //[0,9]
    {
      TRANSMITPERIOD = 100 * (input-48);
      if (TRANSMITPERIOD == 0) TRANSMITPERIOD = 1000;
      Serial.print("\nChanging delay to ");
      Serial.print(TRANSMITPERIOD);
      Serial.println("ms\n");
    }
    
    if (input == 'r') //d=dump register values
      radio.readAllRegs();
    //if (input == 'E') //E=enable encryption
    // radio.encrypt(KEY);
    //if (input == 'e') //e=disable encryption
    // radio.encrypt(null);
    
    if (input == 'd') //d=dump flash area
    {
      Serial.println("Flash content:");
      int counter = 0;

      while(counter<=256){
        Serial.print(flash.readByte(counter++), HEX);
        Serial.print('.');
      }
      while(flash.busy());
      Serial.println();
    }
    if (input == 'e')
    {
      Serial.print("Erasing Flash chip ... ");
      flash.chipErase();
      while(flash.busy());
      Serial.println("DONE");
    }
    if (input == 'i')
    {
      Serial.print("DeviceID: ");
      word jedecid = flash.readDeviceId();
      Serial.println(jedecid, HEX);
    }
  }

  //check for any received packets
  if (radio.receiveDone())
  {
    Serial.println('BEGIN RECEIVED');
    Serial.print('[');Serial.print(radio.SENDERID, DEC);Serial.print("] ");
    for (byte i = 0; i < radio.DATALEN; i++)
      Serial.print((char)radio.DATA[i]);
    Serial.print(" [RX_RSSI:");Serial.print(radio.RSSI);Serial.print("]");
    Serial.println();
    Serial.println('END RECEIVED');

    if (radio.ACK_REQUESTED)
    {
      radio.sendACK();
      Serial.print(" - ACK sent");
      delay(10);
    }
    Blink(LED,5);
    
  }
  
  //send FLASH id
  if(sendSize==0)
  {
    sprintf(buff, "FLASH_MEM_ID:0x%X", flash.readDeviceId());
    byte buffLen=strlen(buff);
    radio.sendWithRetry(GATEWAYID, buff, buffLen);
    radio.sleep();
  }

  looptime = millis() - prevtime;
  elapsedtime = elapsedtime + looptime;
  prevtime = millis();
  Serial.println("elapsedtime");
  Serial.println(elapsedtime);
//  int currPeriod = millis()/TRANSMITPERIOD;
  if (elapsedtime > TRANSMITPERIOD)
  {
    elapsedtime=0;
    Serial.println("Time to take data");
    

    sendSize = (sendSize + 1) % 31;
    Serial.println();
    Blink(LED,3);
    pinMode(ANODE, OUTPUT);
    digitalWrite(ANODE,HIGH);
    
    RotateFirstDigit(100);
    
    // Message Type 
    Serial.print("msgtype:");
    Serial.print(MESSAGETYPE);
    Serial.println(",");
    
    // Message Source ID 
    Serial.print("sourceid:");
    Serial.print(NODEID);
    Serial.println(",");
    
    // Message Dest ID 
    Serial.print("destid:");
    Serial.print(DESTID);
    Serial.println(",");
    
    // Device identifier
    byte dsaddr[8];
    char dscharaddr[16];
    getfirstdsadd(dsaddr);
    
    Serial.print("dsaddress:");
    int i;
    for (i=0;i<8;i++) {
      if (dsaddr[i] < 16) {
        Serial.print('0');
      }
      Serial.print(dsaddr[i], HEX);
    }

    sprintf(dscharaddr,"%02x%02x%02x%02x%02x%02x%02x%02x",dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
    Serial.println(',');
//    Serial.println(dscharaddr);
    
    // Data
    Serial.print("temperature:");
    float temp = getdstemp(dsaddr);
    Serial.println(temp);
//    Serial.println(',');
    
    char sendstring[61];
    int sendlength = 61;  // default
    int wholePart = temp;
    long fractPart = (temp - wholePart) * 10000;
    sprintf(sendstring, "tempasc:%3d.%04d,tempdev:ds18x,temprom:%0xx%02x%02x%02x%02x%02x%02x%02x%02x", wholePart, fractPart, dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
    sendlength = 57; 
    Serial.println("SENDING");
    Serial.println(sendstring);
    radio.sendWithRetry(GATEWAYID, sendstring, sendlength);
    Serial.println("SEND COMPLETE");
  }
  else {
      Serial.println("Not time to take data");
  }
  radio.sleep();
  Serial.flush();

  LowPower.powerDown(SLEEP_2S, ADC_OFF, BOD_OFF);
  elapsedtime=elapsedtime+2000;
//  delay(1000);
  Blink(LED,3);
}

void RotateFirstDigit(int ROTATEDELAY)
{
    pinMode(SEGONE, OUTPUT);
    digitalWrite(SEGONE,LOW);
    delay(ROTATEDELAY);
    digitalWrite(SEGONE,HIGH);
    pinMode(SEGTWO, OUTPUT);
    digitalWrite(SEGTWO,LOW);
    delay(ROTATEDELAY);
    digitalWrite(SEGTWO,HIGH);
    pinMode(SEGTHREE, OUTPUT);
    digitalWrite(SEGTHREE,LOW);
    delay(ROTATEDELAY);
    digitalWrite(SEGTHREE,HIGH);
    pinMode(SEGFOUR, OUTPUT);
    digitalWrite(SEGFOUR,LOW);
    delay(ROTATEDELAY);
    digitalWrite(SEGFOUR,HIGH);
}
void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
void discoverOneWireDevices(void) {
  byte i;
  byte present = 0;
  byte type_s;
  byte data[12];
  byte addr[8];
  float celsius, fahrenheit;
  
  Serial.print("Looking for 1-Wire devices...\n\r");
  while(ds.search(addr)) {
    Serial.print("\n\rFound \'1-Wire\' device with address:\n\r");
    for( i = 0; i < 8; i++) {
      Serial.print("0x");
      if (addr[i] < 16) {
        Serial.print('0');
      }
      Serial.print(addr[i], HEX);
      if (i < 7) {
        Serial.print(", ");
      }
    }
    if ( OneWire::crc8( addr, 7) != addr[7]) {
        Serial.print("CRC is not valid!\n");
        return;
    }
     // the first ROM byte indicates which chip

    Serial.print("\n\raddress:");
    Serial.print(addr[0]);
    switch (addr[0]) {
    
    case 0x10:
      Serial.println("  Chip = DS18S20");  // or old DS1820
      type_s = 1;
      break;
    case 0x28:
      Serial.println("  Chip = DS18B20");
      type_s = 0;
      break;
    case 0x22:
      Serial.println("  Chip = DS1822");
      type_s = 0;
      break;
    default:
      Serial.println("Device is not a DS18x20 family device.");
      return;
  } 

  ds.reset();
  ds.select(addr);
  ds.write(0x44,1);         // start conversion, with parasite power on at the end
  
  delay(1000);     // maybe 750ms is enough, maybe not
  // we might do a ds.depower() here, but the reset will take care of it.
  
  present = ds.reset();
  ds.select(addr);    
  ds.write(0xBE);         // Read Scratchpad

  Serial.print("  Data = ");
  Serial.print(present,HEX);
  Serial.print(" ");
  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = ds.read();
    Serial.print(data[i], HEX);
    Serial.print(" ");
  }
  Serial.print(" CRC=");
  Serial.print(OneWire::crc8(data, 8), HEX);
  Serial.println();

  // convert the data to actual temperature

  unsigned int raw = (data[1] << 8) | data[0];
  if (type_s) {
    raw = raw << 3; // 9 bit resolution default
    if (data[7] == 0x10) {
      // count remain gives full 12 bit resolution
      raw = (raw & 0xFFF0) + 12 - data[6];
    }
    } else {
      byte cfg = (data[4] & 0x60);
      if (cfg == 0x00) raw = raw << 3;  // 9 bit resolution, 93.75 ms
        else if (cfg == 0x20) raw = raw << 2; // 10 bit res, 187.5 ms
        else if (cfg == 0x40) raw = raw << 1; // 11 bit res, 375 ms
        // default is 12 bit resolution, 750 ms conversion time
    }
    celsius = (float)raw / 16.0;
    fahrenheit = celsius * 1.8 + 32.0;
    Serial.print("  Temperature = ");
    Serial.print(celsius);
    Serial.print(" Celsius, ");
    Serial.print(fahrenheit);
    Serial.println(" Fahrenheit");
  }
  Serial.print("\n\r\n\rSearch Complete.\r\n");
  ds.reset_search();
  return;
}
void getfirstdsadd(byte firstadd[]){
  byte i;
  byte present = 0;
  byte addr[8];
  float celsius, fahrenheit;
  
  int length = 8;
  
  //Serial.print("Looking for 1-Wire devices...\n\r");
  while(ds.search(addr)) {
    //Serial.print("\n\rFound \'1-Wire\' device with address:\n\r");
    for( i = 0; i < 8; i++) {
      firstadd[i]=addr[i];
      //Serial.print("0x");
      if (addr[i] < 16) {
        //Serial.print('0');
      }
      //Serial.print(addr[i], HEX);
      if (i < 7) {
        //Serial.print(", ");
      }
    }
    if ( OneWire::crc8( addr, 7) != addr[7]) {
        //Serial.print("CRC is not valid!\n");
        return;
    }
     // the first ROM byte indicates which chip

    //Serial.print("\n\raddress:");
    //Serial.print(addr[0]);
    
    return;
  } 

}

float getdstemp(byte addr[8]) {
  byte present = 0;
  int i;
  byte data[12];
  byte type_s;
  float celsius;
  float fahrenheit;
  
  switch (addr[0]) {
    case 0x10:
      //Serial.println("  Chip = DS18S20");  // or old DS1820
      type_s = 1;
      break;
    case 0x28:
      //Serial.println("  Chip = DS18B20");
      type_s = 0;
      break;
    case 0x22:
      //Serial.println("  Chip = DS1822");
      type_s = 0;
      break;
    default:
      Serial.println("Device is not a DS18x20 family device.");
  } 
  
  ds.reset();
  ds.select(addr);
  ds.write(0x44,1);         // start conversion, with parasite power on at the end
  
  delay(1000);     // maybe 750ms is enough, maybe not
  // we might do a ds.depower() here, but the reset will take care of it.
  
  present = ds.reset();
  ds.select(addr);    
  ds.write(0xBE);         // Read Scratchpad

  //Serial.print("  Data = ");
  //Serial.print(present,HEX);
  //Serial.print(" ");
  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = ds.read();
    //Serial.print(data[i], HEX);
    //Serial.print(" ");
  }
  //Serial.print(" CRC=");
  //Serial.print(OneWire::crc8(data, 8), HEX);
  //Serial.println();

  // convert the data to actual temperature

  unsigned int raw = (data[1] << 8) | data[0];
  if (type_s) {
    raw = raw << 3; // 9 bit resolution default
    if (data[7] == 0x10) {
      // count remain gives full 12 bit resolution
      raw = (raw & 0xFFF0) + 12 - data[6];
    } else {
      byte cfg = (data[4] & 0x60);
      if (cfg == 0x00) raw = raw << 3;  // 9 bit resolution, 93.75 ms
        else if (cfg == 0x20) raw = raw << 2; // 10 bit res, 187.5 ms
        else if (cfg == 0x40) raw = raw << 1; // 11 bit res, 375 ms
        // default is 12 bit resolution, 750 ms conversion time
    }
  }
  celsius = (float)raw / 16.0;
  fahrenheit = celsius * 1.8 + 32.0;
  //Serial.print('Celsius:');
  //Serial.println(celsius);
  return celsius;
}
