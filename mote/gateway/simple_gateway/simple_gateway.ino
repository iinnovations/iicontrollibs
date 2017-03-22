// Colin Reese, CuPID Controls, Interface Innovations
// UniMote sketch, based on the great example by lowpowerlab

// Standards
#include <LowPower.h>
#include <EEPROM.h>

// **********************************************************************************
#include <RFM69.h>         //get it here: https://github.com/lowpowerlab/RFM69
#include <RFM69_ATC.h>     //get it here: https://github.com/lowpowerlab/RFM69
#include <RFM69_OTA.h>     //get it here: https://github.com/lowpowerlab/RFM69
#include <SPIFlash.h>      //get it here: https://github.com/lowpowerlab/spiflash
#include <SPI.h>           //included with Arduino IDE install (www.arduino.cc)

//****** BASIC CONFIG OPTIONS ****
byte DEBUG = 1;
byte RF = 0;

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
//#define IS_RFM69HW  //uncomment only for RFM69HW! Leave out if you have RFM69W!
//*****************************************************************************************************************************
#define ENABLE_ATC    //comment out this line to disable AUTO TRANSMISSION CONTROL
#define ATC_RSSI      -75


//*****************************************************************************************************************************
//#define BR_300KBPS             //run radio at max rate of 300kbps!
//*****************************************************************************************************************************

#define SERIAL_BAUD 115200
byte NODEID = 1;
byte NETWORKID = 1;
byte GATEWAYID = 1;
#define serialrfecho 1
#define RETRIES 10
#define ACK_TIME 100
#define ENCRYPTKEY    "SomeBrewCryption"


#define BLINKPERIOD 500

#ifdef __AVR_ATmega1284P__
  #define LED           15 // Moteino MEGAs have LEDs on D15
  #define FLASH_SS      23 // and FLASH SS on D23
#else
  #define LED           9 // Moteinos hsave LEDs on D9
  #define FLASH_SS      8 // and FLASH SS on D8
#endif

#ifdef ENABLE_ATC
  RFM69_ATC radio;
#else
  RFM69 radio;
#endif

//char input = 0;
long lastPeriod = -1;

//*****************************************************************************************************************************
// flash(SPI_CS, MANUFACTURER_ID)
// SPI_CS          - CS pin attached to SPI flash chip (8 in case of Moteino)
// MANUFACTURER_ID - OPTIONAL, 0x1F44 for adesto(ex atmel) 4mbit flash
//                             0xEF30 for windbond 4mbit flash
//                             0xEF40 for windbond 16/64mbit flash
//*****************************************************************************************************************************
SPIFlash flash(FLASH_SS, 0xEF30); //EF30 for windbond 4mbit flash

#define REG_SYNCVALUE2 0x30

///////////////////////////////////////////////////

// Basic command structure items

#define serialrfecho 1
#define PRINTPERIOD 3000
#define RFREPORTPERIOD 10000

char buff[61];
int i = 0;
int cmdlength;

unsigned long NOW=0;
int powerstate = 0;


void setup() {
  if (DEBUG) {
    Serial.println(F("DEBUG IS ON"));
  }
    
  pinMode(LED, OUTPUT);
  
  Serial.begin(SERIAL_BAUD);
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
  radio.encrypt(ENCRYPTKEY); //OPTIONAL
  #ifdef FREQUENCY_EXACT
  radio.setFrequency(FREQUENCY_EXACT); //set frequency to some custom frequency
  #endif
  
  #ifdef ENABLE_ATC
    radio.enableAutoPower(ATC_RSSI);
  #endif
  
  #ifdef IS_RFM69HW
    radio.setHighPower(); //only for RFM69HW!
  #endif
    Serial.print(F("Start node..."));
    Serial.print(F("Node ID = "));
    Serial.println(NODEID);
  
    if (flash.initialize())
      Serial.println(F("SPI Flash Init OK!"));
    else
      Serial.println(F("SPI Flash Init FAIL!"));
  
  #ifdef BR_300KBPS
    radio.writeReg(0x03, 0x00);  //REG_BITRATEMSB: 300kbps (0x006B, see DS p20)
    radio.writeReg(0x04, 0x6B);  //REG_BITRATELSB: 300kbps (0x006B, see DS p20)
    radio.writeReg(0x19, 0x40);  //REG_RXBW: 500kHz
    radio.writeReg(0x1A, 0x80);  //REG_AFCBW: 500kHz
    radio.writeReg(0x05, 0x13);  //REG_FDEVMSB: 300khz (0x1333)
    radio.writeReg(0x06, 0x33);  //REG_FDEVLSB: 300khz (0x1333)
    radio.writeReg(0x29, 240);   //set REG_RSSITHRESH to -120dBm
  #endif
 
}

void loop() {
  
  // Check for existing RF data, potentially for a new sketch wireless upload
  // For this to work this check has to be done often enough to be
  // picked up when a GATEWAY is trying hard to reach this node for a new sketch wireless upload
  if (RF) {
    if (radio.receiveDone())
    {
      Serial.print(F("Got ["));
      Serial.print(radio.SENDERID);
      Serial.print(F(":"));
      Serial.print(radio.DATALEN);
      Serial.print(F("] > "));
      for (byte i = 0; i < radio.DATALEN; i++)
        Serial.print((char)radio.DATA[i], HEX);
      Serial.println();
      CheckForWirelessHEX(radio, flash, false);
      Serial.println();
    }
  } // IF RF

  // handle Serial commands and stuff
   if (Serial.available() > 0)
  {
    if (DEBUG) {
      Serial.println(F("reading characters"));
    }
    String cmdstring = Serial.readStringUntil('\n');
    if (DEBUG) {
      Serial.println(F("Serial cmd buffer is: "));
      Serial.println(cmdstring);
      Serial.println(F("Of length"));
      Serial.println(cmdstring.length());
    }
    processcmdstring(cmdstring); 
  }// comnand sequence

} // loop

void pulsedledwait(int PIN, long timedelay){
  // Do some delay stuff
  long thetime = millis();
  float in, out;
  int reportintegral = 500;
  int period = 0;
  while (millis() - thetime < timedelay) {
    if (DEBUG && period != millis() / reportintegral) {
      period = millis()/reportintegral;
//      Serial.print(millis()-thetime);Serial.print(F("/"));Serial.println(timedelay);
    }
    if (in > 6.283) in = 0;
    in += .00628;
    
    out = sin(in) * 127.5 + 127.5;
    analogWrite(PIN,out);
    delayMicroseconds(1500);
  } // while waiting
}

void Blink(byte PIN, int DELAY_MS, int ntimes)
{
  for (int i=0;i<ntimes;i++) {
    pinMode(PIN, OUTPUT);
    digitalWrite(PIN,HIGH);
    delay(DELAY_MS);
    digitalWrite(PIN,LOW);
    delay(DELAY_MS);
  }
}

void sendWithSerialNotify(byte destination, char* sendstring, byte sendlength, byte notify) {
  if (notify==1) {
    Serial.print(F("SENDING TO "));
    Serial.println(destination);
    sendstring[sendlength]=0;
    Serial.println(sendstring);
//    Serial.println(sendlength);
  }

  radio.sendWithRetry(destination, sendstring, sendlength, RETRIES, ACK_TIME);
  if (notify==1) {
    Serial.println(F("SEND COMPLETE"));  
  }
}



///////////////////////////////////////////////////

void processcmdstring(String cmdstring){
  if (DEBUG) {
    Serial.println(F("processing cmdstring"));
    Serial.println(cmdstring);
  }
  
  int i;
  String str1="";
  String str2="";
  String str3="";
  String str4="";
  if (cmdstring[0] == '~'){
    if (DEBUG) {
      Serial.println(F("Command character received"));
    }
    int strord=1;
    for (i=1;i<cmdstring.length();i++){
      if (cmdstring[i] != ';' || strord == 4){
        if (cmdstring[i] != '\n' && cmdstring[i] != '\0' && cmdstring[i] != '\r'){
          if (strord == 1){
            str1+=cmdstring[i];
          }
          else if (strord == 2){
            str2+=cmdstring[i];
          }
          else if (strord == 3){
            str3+=cmdstring[i];
          }
          else if (strord == 4){
            str4+=cmdstring[i];
          }
          else {
            Serial.println(F("Error in argument string parse"));
          }
        }
      } // cmdstring is not ;
      else { // cmdstring is ;
        strord ++;
      }  //cmdstring is ;
    } // for each character  
     
    if (str1 == "listparams") {
      //listparams(0,0);
    }
    else if (str1 == "versions") {
       Serial.println("2p1_OTA");
    }
    else if (str1 == "lconfig") {
      Serial.print(F("rfen:"));Serial.print(RF);Serial.print(F(",freq:"));Serial.println(FREQUENCY);
    }
    else if (str1 == "rlistparams") {
      //listparams(1,str2.toInt());
    }
    else if (str1 == "reset") {
//      resetMote();
    }
    else if (str1 == "tdb") {
      if (DEBUG) {
        DEBUG = 0;
        Serial.println("DISABLING DEBUG");
      }
      else {
        DEBUG = 1;
        Serial.println("ENABLING DEBUG");
      }
    }
    else if (str1 == "sdb") {
      if (str2 == "1") {
        DEBUG = 1;
        Serial.println("ENABLING DEBUG");
      }
      else if (str2 == "0") {
        DEBUG = 0;
        Serial.println("DISABLING DEBUG");
      }
    }
    else if (str1 =="sendmsg"){
      //Serial.println("SENDING MESSAGE");
      if (DEBUG) {
        Serial.println(F("sending message: "));
        Serial.print(F("to dest id: "));
        Serial.println(str2.toInt());
        Serial.print(F("Reserved parameter is: "));
        Serial.println(str3);
        Serial.print(F("Message is: "));
        Serial.println(str4);
        Serial.print(F("Length: "));
        Serial.println(str4.length());
      }
      str4.toCharArray(buff,str4.length()+1);
      radio.sendWithRetry(str2.toInt(), buff, str4.length()+1, RETRIES, ACK_TIME);
    }
    else if (str1 =="setsv"){
      if (DEBUG) {
        Serial.println(F("setsv: "));
        Serial.print(F("of channel: "));
        Serial.println(str2.toInt());
        Serial.print(F("To value: "));
        Serial.println(str3);
        Serial.println(F("AND here is where I send the message"));
      }
      // not included in this sketch
//      sendsvcmd(str2.toInt(), str3.toFloat());
    }
    else if (str1 =="setrun"){
      Serial.println(F("setrun: "));
      Serial.print(F("of channel: "));
      Serial.println(str2.toInt());
      Serial.print(F("To value: "));
      Serial.println(str3);
      Serial.println(F("Setrun message"));
      //not included in this sketch
//      sendruncmd(str2.toInt(), str3.toFloat());
    }
    else if (str1 == "flashid"){
      Serial.println(F("Flash ID: "));
      for (i=0;i<8;i++){
        Serial.print(flash.UNIQUEID[i],HEX);
      }
    }
    else{
      Serial.println(F("unrecognized command"));
      Serial.println(str1);
      Serial.print(F("of length: "));
      Serial.println(str1.length());
      for (i=0;i<str1.length();i++){
        Serial.println(str1[i]);
      }
    }
  } // first character indicates command sequence 
  
  // I DON'T USE THESE. BUT YOU CAN
  
//  else { // first character is not command
//    if (cmdstring[0] == 'r') //d=dump register values
//      radio.readAllRegs();
//      //if (input == 'E') //E=enable encryption
//      //  radio.encrypt(KEY);
//      //if (input == 'e') //e=disable encryption
//      //  radio.encrypt(null);

//    if (cmdstring[0] == 'd') //d=dump flash area
//    {
//      Serial.println("Flash content:");
//      uint16_t counter = 0;
//
//      Serial.print("0-256: ");
//      while(counter<=256){
//        Serial.print(flash.readByte(counter++), HEX);
//        Serial.print('.');
//      }
//      while(flash.busy());
//      Serial.println();
//    }
//    if (cmdstring[0] == 'e')
//    {
//      Serial.print(F("Erasing Flash chip ... "));
//      flash.chipErase();
//      while(flash.busy());
//      Serial.println(F("DONE"));
//    }
//    if (cmdstring[0] == 'i')
//    {
//      Serial.print(F("DeviceID: "));
//      word jedecid = flash.readDeviceId();
//      Serial.println(jedecid, HEX);
//    }
//  }
}

