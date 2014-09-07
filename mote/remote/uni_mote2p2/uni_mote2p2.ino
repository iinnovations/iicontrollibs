// Sample RFM69 sender/node sketch, with ACK and optional encryption
// Sends periodic messages of increasing length to gateway (id=1)
// It also looks for an onboard FLASH chip, if present
// Library and code by Felix Rusu - felix@lowpowerlab.com
// Get the RFM69 and SPIFlash library at: https://github.com/LowPowerLab/
#include <RFM69.h>
#include <RFM69registers.h>
#include <SPI.h>
#include <SPIFlash.h>
//#include <Time.h>
#include <OneWire.h>
#include <LowPower.h>
#include <EEPROM.h>
//#include <pgmspace.h>

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
//#define IS_RFM69HW    //uncomment only for RFM69HW! Leave out if you have RFM69W!

#ifdef __AVR_ATmega1284P__
  #define LED           15 // Moteino MEGAs have LEDs on D15
  #define FLASH_SS      23 // and FLASH SS on D23
#else
  #define LED           9 // Moteinos have LEDs on D9
  #define FLASH_SS      8 // and FLASH SS on D8
#endif

#define SERIAL_BAUD   115200

#define DEBUG 1

#define INIT 0
#define ACK_TIME      30 // max # of ms to wait for an ack

byte NODEID = 2;
byte NETWORKID = 100;
byte GATEWAYID = 1;

#define ENCRYPTKEY    "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!

byte SLEEPMODE;
unsigned int SLEEPDELAY; // ms
unsigned int SLEEPDELAYTIMER; // ms

//int TRANSMITPERIOD = 300; //transmit a packet to gateway so often (in ms)
char buff[20];
boolean requestACK = false;
SPIFlash flash(FLASH_SS, 0xEF30); //EF30 for 4mbit  Windbond chip (W25X40CL)
RFM69 radio;

unsigned int LOOPPERIOD = 2000; // ms

// constants
//PROGMEM char ionames[13][3] = { "D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","A7" };
int iopins[13] = { 3,4,5,6,7,A0,A1,A2,A3,A4,A5,A6,A7 };
int owpin;

// user-assigned variables
byte ioenabled[13];
byte iomode[13];
float iovalue[13];
byte ioreportenabled[13];
unsigned long ioreportfreq[13];
unsigned long ioreadfreq[13];

byte chanenabled[8] = {1,0,0,0,0,0,0,0};
int8_t chanposfdbk[8] = {0,0,0,0,0,0,0,0};   // -1 is no pos fdbk
int8_t channegfdbk[8] = {-1,0,0,0,0,0,0,0};  // -1 is no neg fdbk
byte chanmode[8]; // reserved
byte chandeadband[8];
int8_t chanstate[8];
byte chanpvindex[8] = {5,0,0,0,0,0,0,0};
float chanpv[8];
float chansv[8] = {15,0,0,0,0,0,0,0};

unsigned long ioreporttimer[13];
unsigned long ioreadtimer[13];
unsigned long chanreporttimer[8];

unsigned long prevtime = 0;
unsigned long looptime = 0;
  
void setup() {
  Serial.begin(SERIAL_BAUD);
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  
  if (flash.initialize())
  {
    Serial.println(F("SPI Flash Init OK"));
    Serial.print(F("UniqueID (MAC): "));
    flash.readUniqueId();
    for (byte i=0;i<8;i++)
    {
      Serial.print(flash.UNIQUEID[i], HEX);
      Serial.print(' ');
    }
    Serial.println();
  }
  else {
    Serial.println("SPI Flash Init FAIL! (is chip present?)");
  }
  
  // Initialize variables to/from EEPROM
  if (INIT) {
    initparams();
    storeparams();
  } // INIT
  else { // not init
    getparams();
  } // not INIT
  
  // These are values that are not ever stored permanently
  int i;
  for (i=0;i<13;i++) {
     ioreportenabled[i] = ioenabled[i];
     ioreportfreq[i] = 0; // 0 means report when read
     ioreporttimer[i] = 9999999;
     ioreadtimer[i] = 9999999;
  }
  radio.encrypt(ENCRYPTKEY);
  char buff[61];
  sprintf(buff, "\nTransmitting at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
  sprintf(buff, "I am node id: %d",NODEID);
  Serial.println(buff);
  
}
void loop() {
  
  // READ IO
  looptime += millis() - prevtime; // includes time taken to process
  int i;
  for (i=0;i<13;i++) {
    ioreporttimer[i] += looptime;
    ioreadtimer[i] += looptime;
  }
  prevtime = millis();
  looptime = 0; // we keep this around to add time that isn't counted (sleeptime)
  
  // for each io
  for (i=0;i<13;i++){
    if (ioenabled[i]) {
  
      if (ioreadtimer[i] > ioreadfreq[i]) {

        Serial.print(F("Time to check data for pin "));
        Serial.print(iopins[i]);
        Serial.print(F(", io number "));
        Serial.println(i);
        
        ioreadtimer[i] = 0;
        
        // Initialize send string
        char sendstring[61];
        int sendlength = 61;  // default
      
        // Determine mode and what to read
        if (iomode[i] == 0) { // Digital Input
          Serial.print(F("Digital input configured for pin "));
          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = digitalRead(iopins[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sprintf(sendstring, "iopin:%02d,iomode:%02d,iovalue:%d", iopins[i], iomode[i], iovalue[i]);
            sendlength = 28; 
            sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
              
          } // ioreportfreq == 0
        }
        else if (iomode[i] == 1) { // Digital Output
          Serial.print(F("Digital output configured for pin "));
          Serial.println(iopins[i]);
          pinMode(iopins[i], OUTPUT);
          digitalWrite(iopins[i],iovalue[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sprintf(sendstring, "iopin:%02d,iomode:%02d,iovalue:%d", iopins[i], iomode[i], iovalue[i]);
            sendlength = 28; 
            sendWithSerialNotify(GATEWAYID, sendstring, sendlength);   
          } // ioreportfreq == 0
        }
        else if (iomode[i] == 2) { // Analog Input
          Serial.print(F("Analog input configured for pin "));
          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = analogRead(iopins[i]);
          Serial.print(F("Value: "));
          Serial.println(iovalue[i]);
          int wholePart = iovalue[i];
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sprintf(sendstring, "iopin:%02d,iomode:%02d,iovalue:%04d", iopins[i], iomode[i], wholePart);
            sendlength = 31; 
            sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
          } // ioreportfreq == 0 
        }
        else if (iomode[i] == 4) { //OneWire
          Serial.print(F("1Wire configured for pin "));
          Serial.println(iopins[i]);
          
          owpin = iopins[i];
          
          // Device identifier
          byte dsaddr[8];
          char dscharaddr[16];
          OneWire myds(owpin);
          getfirstdsadd(myds,dsaddr);
          
          Serial.print(F("dsaddress:"));
          int j;
          for (j=0;j<8;j++) {
            if (dsaddr[j] < 16) {
              Serial.print('0');
            }
            Serial.print(dsaddr[j], HEX);
          }
          sprintf(dscharaddr,"%02x%02x%02x%02x%02x%02x%02x%02x",dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
          Serial.println(',');
        
          // Data
          Serial.print(F("temperature:"));
          iovalue[i] = getdstemp(myds, dsaddr);
          Serial.println(iovalue[i]);
    
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            int wholePart = iovalue[i];
            long fractPart = (iovalue[i] - wholePart) * 10000;
            sprintf(sendstring, "owtmpasc:%03d.%04d,owdev:ds18x,owrom:%0xx%02x%02x%02x%02x%02x%02x%02x%02x", wholePart, fractPart, dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
            sendlength = 54; 
            sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
          } // reportenabled and ioreportfreq
        } // If OneWire
        else if (iomode[i] == 3) { // PWM
          Serial.print(F("PWM Configured for pin"));
          Serial.print(iopins[i]);
          
          // pwm code goes here
          
        } // If PWM
      } // If timer   
    } // If enabled
    else { // not enabled
    } // not enabled
  } // for i=0 --> 13
  // END READ IO
  
  
  // REPORTING 
  for (i=0;i<13;i++){
    // remember that ioreportfreq=0 means report when read
    if (ioreportenabled[i] && ioreportfreq[i] > 0 && ioreporttimer[i] > ioreportfreq[i]){
        
        // this is a bit more general than the on-the-fly reporting
        // most notably, no onewire address or type
        
        // Initialize send string
        char sendstring[61];
        int sendlength = 61;  // default
        
        int wholePart = iovalue[i];
        long fractPart = (iovalue[i] - wholePart) * 10000;
        sprintf(sendstring, "iopin:%02d,iomode:%02d,ioval:%03d.%04d", iopins[i],iomode[i],wholePart, fractPart);
        sendlength = 34; 
        sendWithSerialNotify(GATEWAYID, sendstring, sendlength); 
    } // time to report
  }
  // END REPORTING
  
  
  // PROCESS CHANNELS
  for (i=0;i<8;i++) {
    if (chanenabled[i]) {
      Serial.print(F("Channel "));
      Serial.print(i);
      Serial.println(F(" value: "));
      chanpv[i]=iovalue[chanpvindex[i]];
      Serial.println(chanpv[i]);
      Serial.println("Setpoint value: ");
      Serial.println(chansv[i]);
      if ((chanpv[i] - chansv[i]) > chandeadband[i]) {
        Serial.println(F("Setting negative action"));
        chanstate[i]=-1;
        Serial.print(F("Neg feedback: "));
        // set opposing feedback to zero first
        if (chanposfdbk[i] >=0){
          iovalue[chanposfdbk[i]]=0;
          // update now
          ioreadtimer[chanposfdbk[i]]=999999;
        }
        // Then set desired feedback
        if (channegfdbk[i] >=0){
          iovalue[channegfdbk[i]]=1;
          // update now
          ioreadtimer[channegfdbk[i]]=999999;
        }
        Serial.println(channegfdbk[i]);
      }
      else if ((chansv[i] - chanpv[i]) > chandeadband[i]) {
        Serial.println("Setting positive action");
        chanstate[i]=1;
        Serial.print(F("Pos feedback: "));
        // set opposing feedback to zero first
        if (channegfdbk[i] >=0){
          iovalue[channegfdbk[i]]=0;
          // update now
          ioreadtimer[channegfdbk[i]]=999999;
        }
        // Then set desired feedback
        if (chanposfdbk[i] >=0){
          iovalue[chanposfdbk[i]]=1;
          // update now
          ioreadtimer[chanposfdbk[i]]=999999;
        }
        Serial.println(chanposfdbk[i]);
      }
      else {
        Serial.println("Setting no action");
        chanstate[i]=0;
      }
    } // channel enabled
  } // for channels
  // END PROCESS CHANNELS
  
  
   // If we're in SLEEPMODE, we wait for a set period to receive packets on serial and radio
   
  int millistart;
  SLEEPDELAYTIMER = 0;
  if (SLEEPMODE) {
    millistart = millis();
    Serial.println(F("Entering receive sequence"));
  }
  // failsafe. must listen.
  if (SLEEPDELAY < 1000){
   SLEEPDELAY = 1000;
  }
  
  while (SLEEPDELAYTIMER < SLEEPDELAY){
    
    // SERIAL RECEIVE AND PROCESSING
    // Check for any received packets
    
    if (Serial.available() > 0)
    {
      String cmdstring = Serial.readStringUntil('\n');
      Serial.println(cmdstring);
      processcmdstring(cmdstring);
      
      // Reset sleepdelay timer
      millistart = millis();
      
    } // Serial available
    // END SERIAL RECEIVE
    
    // RADIO RECEIVE AND PROCESSING
    // Check for any received packets
    if (radio.receiveDone())
    {
      Serial.println(F("BEGIN RECEIVED"));
      Serial.print(F("nodeid:"));Serial.print(radio.SENDERID, DEC);Serial.print(F(", "));
      String cmdstring = "";
      for (byte i = 0; i < radio.DATALEN; i++) {
        Serial.print((char)radio.DATA[i]);
        cmdstring+=(char)radio.DATA[i];
      }
      Serial.print(F(",RX_RSSI:"));Serial.print(radio.RSSI);Serial.print(F(""));
      Serial.println();
      Serial.println(F("END RECEIVED"));
      processcmdstring(cmdstring);
      if (radio.ACKRequested())
      {
        radio.sendACK();
        Serial.print(F(" - ACK sent"));
      } // ack requested
      Blink(LED,5);
      Serial.println();
      
      // Reset sleepdelay timer
      millistart = millis();
    } // Radio Receive
    // END RADIO RECEIVE
    
    if (SLEEPMODE) {
      if (SLEEPDELAYTIMER < 65535){
        // if timer is at 65535, means we are intentionally exiting
        SLEEPDELAYTIMER = millis() - millistart;
      }
    }
    else { // exit loop after one iteration if not in sleep mode
      SLEEPDELAYTIMER = 65535;
    } 
//    Serial.println(SLEEPDELAYTIMER);
  } // SLEEPDELAY while
  
  if (SLEEPMODE){
   Serial.println(F("Exiting receive sequence"));
  } 
  
  Blink(LED,3);
   
  // Do our sleep or delay
  if (SLEEPMODE) {
    Serial.println(F("Going to sleep for "));
    Serial.println(LOOPPERIOD);
    // Set cutoffs to optimize number of times we have to wake
    // vs. accuracy of sleep time. We'll use 10x as rule of thumb
    period_t sleepperiod;
    int numloops;
    if (LOOPPERIOD > 80000 || LOOPPERIOD == 8000){
      // Use 8s interval
      numloops = LOOPPERIOD / 1000 / 8;
      sleepperiod = SLEEP_8S;
    }
    else if (LOOPPERIOD > 40000 || LOOPPERIOD == 4000) {
      // Use 4s interval
      numloops = LOOPPERIOD / 1000 / 4;
      sleepperiod = SLEEP_4S;
    }
    else if (LOOPPERIOD > 20000 || LOOPPERIOD == 2000) {
      // Use 2s interval
      numloops = LOOPPERIOD / 1000 / 2;
      sleepperiod = SLEEP_2S;
    }
    else if (LOOPPERIOD > 10000 || LOOPPERIOD == 1000) {
      // Use 1s interval
      numloops = LOOPPERIOD / 1000;
      sleepperiod = SLEEP_1S;
    }
    else if (LOOPPERIOD > 5000 || LOOPPERIOD == 500) {
      // Use 500ms interval
      numloops = LOOPPERIOD / 500;
      sleepperiod = SLEEP_500MS;
    }
    else if (LOOPPERIOD > 2500 || LOOPPERIOD == 250) {
      // Use 250ms interval
      numloops = LOOPPERIOD / 250;
      sleepperiod = SLEEP_250MS;
    }
    else if (LOOPPERIOD > 1200 || LOOPPERIOD == 120) {
      // Use 120ms interval
      numloops = LOOPPERIOD / 120;
      sleepperiod = SLEEP_120MS;
    }
    else if (LOOPPERIOD > 600 || LOOPPERIOD == 60) {
      // Use 60ms interval
      numloops = LOOPPERIOD / 60;
      sleepperiod = SLEEP_60MS;
    }
    else if (LOOPPERIOD > 300 || LOOPPERIOD == 30) {
      // Use 30ms interval
      numloops = LOOPPERIOD / 30;
      sleepperiod = SLEEP_30MS;
    }
    else {
      // Use 15ms interval
      numloops = LOOPPERIOD / 15;
      sleepperiod = SLEEP_15Ms;
    }
    Serial.print(F("numloops"));
    Serial.println(numloops);
    Serial.flush();
    radio.sleep();

    for (i=0;i<numloops;i++) {
      LowPower.powerDown(sleepperiod, ADC_OFF, BOD_OFF);
    }
    // Sleeptime eludes millis()
    looptime += LOOPPERIOD;
  }
  else {
    delay(LOOPPERIOD);
  }
} // end main loop

void processcmdstring(String cmdstring){
  Serial.println(F("processing cmdstring"));
  Serial.println(cmdstring);
    
  int i;
  String str1="";
  String str2="";
  String str3="";
  String str4="";
  if (cmdstring[0] == '~'){
    Serial.println(F("Command character received"));
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
      listparams(0,0);
    }
    else if (str1 == "rlistparams") {
      listparams(1,str2.toInt());
    }
    else if (str1 == "reset") {
//      resetMote();
    }
    else if (str1 == "gosleep") {
      SLEEPDELAYTIMER=65535;  // send mote to sleep
    }
    else if (str1 == "modparam") {
      Serial.println(str2);
      if (str2 == "loopperiod") {
        long newvalue = str3.toInt()*1000;
        if (newvalue >= 0 && newvalue < 600000){
          Serial.print(F("Modifying loopperiod to "));
          Serial.println(newvalue);
          // deliver in seconds, translate to ms
          LOOPPERIOD = newvalue;
          storeparams();
        }
        else {
          Serial.println("Value out of range");
        }
      } // loopperiod
      if (str2 == "sleepmode") {
        byte newvalue = str3.toInt();
        if (newvalue == 0) {
          Serial.println(F("Disabling sleepmode."));
          SLEEPMODE = 0;
          storeparams();
        }
        else if (newvalue == 1) {
          Serial.println(F("Enabling sleepmode."));
          SLEEPMODE = 1;
          storeparams();
        }
        else {
          Serial.print(F("Value out of range: "));
          Serial.println(newvalue);
        }
      } // sleepmode
      else if (str2 == "sleepdelay") {
        long newvalue = str3.toInt()*100;
        if (newvalue >= 300 && newvalue < 60000){
          Serial.print(F("Modifying sleepdelay to "));
          Serial.println(newvalue);
          // deliver in 100s ms, translate to ms
          SLEEPDELAY = newvalue;
          storeparams();
        }
        else {
          Serial.println("Value out of range");
        }
      } // sleepdelay
      else if (str2 == "nodeid") {
        long newvalue = str3.toInt();
        if (newvalue >= 2 && newvalue < 256){
          Serial.print(F("Modifying nodeid to "));
          Serial.println(newvalue);
          // deliver in seconds, translate to ms
          NODEID = newvalue;
          radio.setAddress(NODEID);
          storeparams();
        }
        else {
          Serial.println("Value out of range");
        }
      } // nodeid
      else if (str2 == "networkid") {
        long newvalue = str3.toInt();
        if (newvalue >= 1 && newvalue < 256){
          Serial.print(F("Modifying networkid to "));
          Serial.println(newvalue);
          // deliver in ~seconds, translate to ms
          NETWORKID = newvalue;
          radio.writeReg(REG_SYNCVALUE2, NETWORKID);
          storeparams();
        }
        else {
          Serial.println("Value out of range");
        }
      } // network
      else if (str2 == "gatewayid") {
        long newvalue = str3.toInt();
        if (newvalue >= 1 && newvalue < 256){
          Serial.print(F("Modifying gatewayid to "));
          Serial.println(newvalue);
          // deliver in seconds, translate to ms
          GATEWAYID = newvalue;
          storeparams();
        }
        else {
          Serial.println("Value out of range");
        }
      } // network
      else if (str2 == "iomode") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying iomode: "));
          Serial.println(ionumber);
          int newvalue = str4.toInt();
          if (newvalue >= 0 && newvalue <5) {
            Serial.print(F("Changing iomode to: "));
            Serial.println(newvalue);
            iomode[ionumber]=newvalue;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            Serial.print(F("Value out of range: "));
            Serial.println(newvalue);
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // iomode
      else if (str2 == "ioenabled") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying ioenabled: "));
          Serial.println(ionumber);
          int newvalue = str4.toInt();
          if (newvalue == 0) {
            Serial.println(F("Disabling io."));
            ioenabled[ionumber] = 0;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else if (newvalue == 1) {
            Serial.println(F("Enabling io."));
            ioenabled[ionumber] = 1;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            Serial.print(F("Value out of range: "));
            Serial.println(newvalue);
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // ioenabled
      else if (str2 == "ioreadfreq") {
        Serial.print(str3);
        int ionumber = str3.toInt();
        Serial.println(ionumber);
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying io: "));
          Serial.println(ionumber);
          long newvalue = str4.toInt()*1000;
          if (newvalue >= 0 && newvalue <600000) {
            Serial.print(F("Changing io readfreq to"));
            Serial.println(newvalue);
            ioreadfreq[ionumber]=newvalue;
            storeparams();
          }
          else{
            Serial.print(F("Value out of range: "));
            Serial.println(newvalue);
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // ioreadfreq
      else if (str2 == "ioreportenabled") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying io: "));
          Serial.println(ionumber);
          int newvalue = str4.toInt();
          if (newvalue = 0) {
            Serial.print(F("Disabling ioreporting."));
            ioreportenabled[ionumber] = 0;
            storeparams();
          }
          else if (newvalue == 0) {
            Serial.print(F("Enabling ioreporting."));
            ioreportenabled[ionumber] = 1;
            storeparams();
          }
          else {
            Serial.println(F("Value out of range"));
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // ioreport enabled
      else if (str2 == "ioreportfreq") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying io: "));
          Serial.println(ionumber);
          long newvalue = str4.toInt()*1000;
          if (newvalue >= 0 && newvalue <600000) {
            Serial.print(F("Changing io reportfreq to: "));
            Serial.println(newvalue);
            ioreportfreq[ionumber]=newvalue;
            storeparams();
          }
          else {
            Serial.println(F("Value out of range"));
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // ioreportfreq
      else if (str2 == "iovalue") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <14) {
          Serial.print(F("Modifying iovalue: "));
          Serial.println(ionumber);
          
          int newvalue = str4.toInt();
          if (newvalue >= 0) {
            Serial.print(F("Changing io value to: "));
            Serial.println(newvalue);
            iovalue[ionumber]=newvalue;
            storeparams();
          }
          else {
            Serial.print(F("Value out of range: "));
            Serial.println(newvalue);
          }
        }
        else {
          Serial.println(F("IO number out of range"));
        }
      } // iovalues
      else if (str2 == "chansv") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          // need to allow for floats
          int newvalue = str4.toInt();      
          Serial.print(F("Changing sv to "));
          Serial.println(newvalue);
          chansv[channumber]=newvalue;
          storeparams();
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// chansv
      else if (str2 == "chanpvindex") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue >=0 and newvalue <13){     
            Serial.print(F("Changing pvindex to"));
            Serial.println(newvalue);
            chanpvindex[channumber]=newvalue;
            storeparams();
          }
          else {
            Serial.println(F("pvindex out of range"));
          }
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// chanpvindex
      else if (str2 == "chanposfdbk") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue >=0 and newvalue <13){     
            Serial.print(F("Changing posfdbk to "));
            Serial.println(newvalue);
            chanposfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            Serial.println(F("posfdbk out of range"));
          }
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// chanposfdbk
      else if (str2 == "channegfdbk") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue >=0 and newvalue <13){     
            Serial.print(F("Changing posfdbk to "));
            Serial.println(newvalue);
            channegfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            Serial.println(F("negfdbk out of range"));
          }
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// channegfdbk
      else if (str2 == "chanenabled") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue == 0) {
            Serial.println(F("Disabling channel."));
            chanenabled[channumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            Serial.println(F("Enabling channel."));
            chanenabled[channumber] = 1;
            storeparams();
          }
          else {
            Serial.println(F("Value out of range"));
          }
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      } // chanenabled
    } // modparams
    else if (str1 =="sendmsg"){
      Serial.println(F("sending message: "));
      Serial.print(F("to dest id: "));
      Serial.println(str2.toInt());
      Serial.print(F("Reserved parameter is: "));
      Serial.println(str3);
      Serial.print(F("Message is: "));
      Serial.println(str4);
      Serial.print(F("Length: "));
      Serial.println(str4.length());
      str4.toCharArray(buff,str4.length()+1);
      radio.sendWithRetry(str2.toInt(), buff, str4.length()+1);
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
  else { // first character is not command
    if (cmdstring[0] == 'r') //d=dump register values
      radio.readAllRegs();
      //if (input == 'E') //E=enable encryption
      //  radio.encrypt(KEY);
      //if (input == 'e') //e=disable encryption
      //  radio.encrypt(null);

    if (cmdstring[0] == 'd') //d=dump flash area
    {
      Serial.println("Flash content:");
      uint16_t counter = 0;

      Serial.print(F("0-256: "));
      while(counter<=256){
        Serial.print(flash.readByte(counter++), HEX);
        Serial.print('.');
      }
      while(flash.busy());
      Serial.println();
    }
    if (cmdstring[0] == 'e')
    {
      Serial.print(F("Erasing Flash chip ... "));
      flash.chipErase();
      while(flash.busy());
      Serial.println(F("DONE"));
    }
    if (cmdstring[0] == 'i')
    {
      Serial.print(F("DeviceID: "));
      word jedecid = flash.readDeviceId();
      Serial.println(jedecid, HEX);
    }
  }
}
void sendWithSerialNotify(byte destination, char* sendstring, byte sendlength) {
  Serial.print(F("SENDING TO "));
  Serial.println(destination);
  Serial.println(sendstring);
  radio.sendWithRetry(destination, sendstring, sendlength);
  Serial.println(F("SEND COMPLETE"));  
}
void initparams() {
    NODEID = 5;
    NETWORKID  = 100;
    GATEWAYID = 1;
    LOOPPERIOD = 1000;
    SLEEPMODE = 0;
    SLEEPDELAY = 1000;
    storeparams();
    int i;
    for (i=0;i<13;i++){
      iomode[i] = 0;
      ioenabled[i] = 0;
      ioreadfreq[i] = 10000;
    }
    for (i=0;i<7;i++) {
      chanenabled[i]=0;
    }
}
void storeparams() {
  EEPROM.write(0,NODEID);
  EEPROM.write(1,NETWORKID);
  EEPROM.write(2,GATEWAYID);
  
   // update object
    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
    radio.setAddress(NODEID);
    
  // maximum initialized loop period is 256
  if (LOOPPERIOD/1000 > 256){
    EEPROM.write(58,256);
  }
  else {
    EEPROM.write(58,LOOPPERIOD/1000);
  }
  
  EEPROM.write(59,SLEEPMODE);
  EEPROM.write(60,SLEEPDELAY);
  
  int i;
  for (i=0;i<16;i++) {
//      EEPROM.write(i+3,ENCRYPTKEY[i]);
  }
  byte mybyte;
  for (i=0;i<13;i++){    
    EEPROM.write(i+19,iomode[i]);
    EEPROM.write(i+32,ioenabled[i]);
    if (ioreadfreq[i]/1000 > 256){
      EEPROM.write(i+45,256);
    }
    else {
      mybyte = ioreadfreq[i] / 1000;
      EEPROM.write(i+45,mybyte);
    }
  } // for num io
  
  // channels data
  for (i=0;i<8;i++) {
    EEPROM.write(i+70,chanenabled[i]);
    EEPROM.write(i+78,chanmode[i]);
    EEPROM.write(i+86,chanposfdbk[i]);
    EEPROM.write(i+94,channegfdbk[i]);
    EEPROM.write(i+102,chandeadband[i]);
    EEPROM.write(i+110,chanpvindex[i]);
    EEPROM.write(i+118,chansv[i]);
  } // for channels
}
void getparams() {

    NODEID = EEPROM.read(0);
    NETWORKID = EEPROM.read(1);
    GATEWAYID = EEPROM.read(2);    
    
    // update object
    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
    radio.setAddress(NODEID);
    
    LOOPPERIOD = EEPROM.read(58) * 1000;
    SLEEPMODE = EEPROM.read(59);
    SLEEPDELAY = EEPROM.read(60);
 
    // io
    int i;
    for (i=0;i<13;i++){
      iomode[i] = EEPROM.read(i+19);
      ioenabled[i] = EEPROM.read(i+32);
      ioreadfreq[i] = EEPROM.read(i+45)*1000;      
    } // for io 
    
    //channels
    for (i=0;i<8;i++) {
      chanenabled[i] = EEPROM.read(i+70);
      chanmode[i] = EEPROM.read(i+78);
      chanposfdbk[i] = EEPROM.read(i+86);
      channegfdbk[i] = EEPROM.read(i+94);
      chandeadband[i] = EEPROM.read(i+102);
      chanpvindex[i] = EEPROM.read(i+110);
      chansv[i] = EEPROM.read(i+118);
    } // for channels
}
void listparams(byte mode, byte dest) {
  int i;
  if (mode == 0){
    Serial.print(F("NODEID:"));
    Serial.print(NODEID);
    Serial.println(F(","));
    Serial.print(F("GATEWAYID:"));
    Serial.print(GATEWAYID);
    Serial.println(F(","));
    Serial.print(F("NETWORKID:"));
    Serial.print(NETWORKID);
    Serial.println(F(","));
    Serial.print(F("LOOPPERIOD:"));
    Serial.print(LOOPPERIOD);
    Serial.println(F(","));
    Serial.print(F("SLEEPMODE:"));
    Serial.print(SLEEPMODE);
    Serial.println(F(","));
    Serial.print(F("SLEEPDELAY:"));
    Serial.print(SLEEPDELAY);
    Serial.println(F(","));
    
    Serial.print(F("iomode:["));
    for (i=0;i<13;i++) {
      Serial.print(iomode[i]);
      if (i<12){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioenabled:["));
    for (i=0;i<13;i++) {
      Serial.print(ioenabled[i]);
      if (i<12){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("iovalue:["));
    for (i=0;i<13;i++) {
      Serial.print(iovalue[i]);
      if (i<12){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreadfreq:["));
    for (i=0;i<13;i++) {
      Serial.print(ioreadfreq[i]);
      if (i<12){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreportenabled:["));
    for (i=0;i<13;i++) {
      Serial.print(ioreportenabled[i]);
      if (i<12){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreportfreq:["));
    for (i=0;i<13;i++) {
      Serial.print(ioreportfreq[i]);
      if (i<12){
        Serial.print(F(","));
      }
    } // for io
    Serial.println(F("],"));
    
    // Channel parameters
    Serial.print(F("chanenabled:["));
    for (i=0;i<8;i++) {
      Serial.print(chanenabled[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chanmode:["));
    for (i=0;i<8;i++) {
      Serial.print(chanmode[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chanposfdbk:["));
    for (i=0;i<8;i++) {
      Serial.print(chanposfdbk[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("channegfdbk:["));
    for (i=0;i<8;i++) {
      Serial.print(channegfdbk[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chandeadband:["));
    for (i=0;i<8;i++) {
      Serial.print(chandeadband[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chanpvindex:["));
    for (i=0;i<8;i++) {
      Serial.print(chanpvindex[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chansv:["));
    for (i=0;i<8;i++) {
      Serial.print(chansv[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("]"));
  } // serial mode
  else if (mode == 1) {
    Serial.println(F("I am sending radio params"));
    radio.sendWithRetry(dest, "I send some params", 10);  
  }
} // function def

void getfirstdsadd(OneWire myds, byte firstadd[]){
  byte i;
  byte present = 0;
  byte addr[8];
  float celsius, fahrenheit;
  
  int length = 8;
  
  //Serial.print("Looking for 1-Wire devices...\n\r");
  while(myds.search(addr)) {
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

float getdstemp(OneWire myds, byte addr[8]) {
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
  
  myds.reset();
  myds.select(addr);
  myds.write(0x44,1);         // start conversion, with parasite power on at the end
  
  delay(1000);     // maybe 750ms is enough, maybe not
  // we might do a ds.depower() here, but the reset will take care of it.
  
  present = myds.reset();
  myds.select(addr);    
  myds.write(0xBE);         // Read Scratchpad

  //Serial.print("  Data = ");
  //Serial.print(present,HEX);
  //Serial.print(" ");
  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = myds.read();
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

void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
