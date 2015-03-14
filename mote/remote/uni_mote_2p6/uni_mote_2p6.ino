// UniMote sketch, based on the great example 

// Colin Reese, CuPID Controls, Interface Innovations

// Library and code by Felix Rusu - felix@lowpowerlab.com
// Get the RFM69 and SPIFlash library at: https://github.com/LowPowerLab/
#include <RFM69.h>
//#include <RFM69registers.h>
#include <SPI.h>
#include <SPIFlash.h>
#include <OneWire.h>
#include <LowPower.h>
#include <EEPROM.h>
#include <Flash.h>
//#include <LedControl.h>

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
#define IS_RFM69HW    //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define REG_SYNCVALUE2 0x30

//#ifdef __AVR_ATmega1284P__
//  #define LED           15 // Moteino MEGAs have LEDs on D15
//  #define FLASH_SS      23 // and FLASH SS on D23
//#else
  #define LED           9 // Moteinos have LEDs on D9
  #define FLASH_SS      8 // and FLASH SS on D8
//#endif

#define SERIAL_BAUD   115200

#define DEBUG 1

#define INIT 1
#define ACK_TIME      30 // max # of ms to wait for an ack

// These values are either initialized or retrieved from Flash
byte NODEID;
byte NETWORKID;
byte GATEWAYID;
 
#define ENCRYPTKEY    "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!

byte SLEEPMODE;
unsigned int SLEEPDELAY; // ms
unsigned int SLEEPDELAYTIMER; // ms

//int TRANSMITPERIOD = 300; //transmit a packet to gateway so often (in ms)

boolean requestACK = false;
SPIFlash flash(FLASH_SS, 0xEF30); //EF30 for 4mbit  Windbond chip (W25X40CL)
RFM69 radio;

unsigned int LOOPPERIOD = 1000; // ms

// constants
//PROGMEM char ionames[13][3] = { "D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","A7" };
byte iopins[13] = { 3,4,5,6,7,A0,A1,A2,A3,A4,A5,A6,A7 };
byte owpin;

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

//LedControl lc=LedControl(17,18,19,1);

unsigned long ioreporttimer[13];
unsigned long ioreadtimer[13];
unsigned long chanreporttimer[8];

unsigned long prevtime = 0;
unsigned long looptime = 0;

char buff[61];

// make these global to allow subroutines without crazy pointers
char charstr1[12];
char charstr2[12];
char charstr3[25];
char charstr4[40];
  
byte str1len;
byte str2len;
byte str3len;
byte str4len;
  
char replystring[62];
byte replylength=0;

void setup() {
  
  Serial.begin(SERIAL_BAUD);
  
  // Initialize variables to/from EEPROM
  if (INIT) {
    Serial.println(F("Running init"));
    initparams();
    storeparams();
  } // INIT
  else { // not init
    Serial.println(F("Not running init"));
  } // not INIT
  getparams();
  
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  
  if (flash.initialize())
  {
    Serial.println(F("SPI Flash Init OK"));
//    Serial.print(F("UniqueID (MAC): "));
//    flash.readUniqueId();
//    for (byte i=0;i<8;i++)
//    {
//      Serial.print(flash.UNIQUEID[i], HEX);
//      Serial.print(' ');
//    }
//    Serial.println();
  }
  else {
    Serial.println(F("SPI Flash Init FAIL)"));
  }
  
  // These are values that are not ever stored permanently
  int i;
  for (i=0;i<13;i++) {
     ioreportenabled[i] = ioenabled[i];
     ioreportfreq[i] = 0; // 0 means report when read
     ioreporttimer[i] = 9999999;
     ioreadtimer[i] = 9999999;
  }
  radio.encrypt(ENCRYPTKEY);
  sendInitMessage();
  
//  lc.shutdown(0,false);
  /* Set the brightness to a medium values */
//  lc.setIntensity(0,8);
  /* and clear the display */
//  lc.clearDisplay(0);
  
}
void loop() {
  
//  Serial.print(F("Free memory: "));
//  Serial.println(freeRam());
  
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

//        Serial.print(F("Time to check data for pin "));
//        Serial.print(iopins[i]);
//        Serial.print(F(", io number "));
//        Serial.println(i);
        
        ioreadtimer[i] = 0;

        // Determine mode and what to read
        if (iomode[i] == 0) { // Digital Input
//          Serial.print(F("Digital input configured for pin "));
//          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = digitalRead(iopins[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sendIOMessage(iopins[i], iomode[i], iovalue[i]);             
          } // ioreportfreq == 0
        }
        else if (iomode[i] == 1) { // Digital Output
//          Serial.print(F("Digital output configured for pin "));
//          Serial.println(iopins[i]);
          pinMode(iopins[i], OUTPUT);
          digitalWrite(iopins[i],iovalue[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sendIOMessage(iopins[i], iomode[i], iovalue[i]);
          } // ioreportfreq == 0
        }
        else if (iomode[i] == 2) { // Analog Input
//          Serial.print(F("Analog input configured for pin "));
//          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = analogRead(iopins[i]);
//          Serial.print(F("Value: "));
//          Serial.println(iovalue[i]);
//          int wholePart = iovalue[i];
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sendIOMessage(iopins[i], iomode[i], iovalue[i]);
          } // ioreportfreq == 0 
        }
        else if (iomode[i] == 4) { //OneWire
//          Serial.print(F("1Wire configured for pin "));
//          Serial.println(iopins[i]);
          
          // pass ioindex to have the routine handle it
          handleOWIO(i);

        } // If OneWire
        else if (iomode[i] == 3) { // PWM
//          Serial.print(F("PWM Configured for pin"));
//          Serial.print(iopins[i]);
          
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
        
        // Initialize send stringsend
        sendIOMessage(iopins[i],iomode[i],iovalue[i]);
       
    } // time to report
  }
  // END REPORTING
  
  
  // PROCESS CHANNELS
  for (i=0;i<8;i++) {
    if (chanenabled[i]) {
//      Serial.print(F("Channel "));
//      Serial.print(i);
//      Serial.println(F(" value: "));
      chanpv[i]=iovalue[chanpvindex[i]];
//      Serial.println(chanpv[i]);
//      Serial.println(F("Setpoint value: "));
//      Serial.println(chansv[i]);
      if ((chanpv[i] - chansv[i]) > chandeadband[i]) {
//        Serial.println(F("Setting negative action"));
        chanstate[i]=-1;
//        Serial.print(F("Neg feedback: "));
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
//        Serial.println(channegfdbk[i]);
      }
      else if ((chansv[i] - chanpv[i]) > chandeadband[i]) {
//        Serial.println(F("Setting positive action"));
        chanstate[i]=1;
//        Serial.print(F("Pos feedback: "));
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
//        Serial.println(chanposfdbk[i]);
      }
      else {
//        Serial.println(F("Setting no action"));
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
    Serial.println(F("Entering Sleep Seq."));
  }
  // failsafe. must listen.
  if (SLEEPDELAY < 1000){
   SLEEPDELAY = 1000;
  }
  
  while (SLEEPDELAYTIMER < SLEEPDELAY){
    
    // SERIAL RECEIVE AND PROCESSING
    // Check for any received packets
    int cmdlength;
    if (Serial.available() > 0)
    {
      cmdlength = Serial.readBytes(buff, 60);
      for (i=0; i<cmdlength;i++){
        Serial.print(buff[i]);
      }
      Serial.println();
      processcmdstring(buff, cmdlength, 0);
      
      // Reset sleepdelay timer
      millistart = millis();
      
    } // Serial available
    // END SERIAL RECEIVE
    
    // RADIO RECEIVE AND PROCESSING
    // Check for any received packets
    if (radio.receiveDone())
    {
      Serial.println(F("BEGIN RECEIVED"));
      Serial.print(F("nodeid:"));Serial.print(radio.SENDERID, DEC);Serial.print(F(","));
      cmdlength=0;
      for (byte i = 0; i < radio.DATALEN; i++) {
        Serial.print((char)radio.DATA[i]);
        buff[i] = (char)radio.DATA[i];
        cmdlength+=1;
      }
      Serial.print(F(",RX_RSSI:"));
      Serial.println(radio.RSSI);
      Serial.println(F("END RECEIVED"));
      
      if (cmdlength > 0){
        processcmdstring(buff, cmdlength, radio.SENDERID);
      }
      if (radio.ACKRequested())
      {
        radio.sendACK();
        Serial.println(F(" - ACK sent"));
      } // ack requested
      Blink(LED,5);
      
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
   Serial.println(F("Exit Sleep"));
  } 
  
  Blink(LED,3);
   
  // Do our sleep or delay
  if (SLEEPMODE) {
//    Serial.println(F("Going to sleep for "));
//    Serial.println(LOOPPERIOD);
    // Set cutoffs to optimize number of times we have to wake
    // vs. accuracy of sleep time. We'll use 10x as rule of thumb
    period_t sleepperiod;
    unsigned int sleepremaining = LOOPPERIOD;
    
    while (sleepremaining > 0) {
      if (sleepremaining > 8000) {
        // Use 8s interval
        sleepperiod = SLEEP_8S;
        sleepremaining -= 8000;
      }
      else if (sleepremaining >= 4000) {
        // Use 4s interval
        sleepremaining-=4000;
        sleepperiod = SLEEP_4S;
      }
      else if (sleepremaining >= 2000) {
        // Use 2s interval
        sleepremaining-=2000;
        sleepperiod = SLEEP_2S;
      }
      else if (sleepremaining >= 1000) {
        // Use 1s interval
       sleepremaining-=1000;
        sleepperiod = SLEEP_1S;
      }
      else if (sleepremaining >= 500) {
        // Use 500ms interval
        sleepremaining-=500;
        sleepperiod = SLEEP_500MS;
      }
      else if (sleepremaining >= 250) {
        // Use 250ms interval
       sleepremaining-=250;
        sleepperiod = SLEEP_250MS;
      }
      else if (sleepremaining >= 120) {
        // Use 120ms interval
        sleepremaining-=120;
        sleepperiod = SLEEP_120MS;
      }
      else if (sleepremaining >= 60) {
        // Use 60ms interval
        sleepremaining-=60;
        sleepperiod = SLEEP_60MS;
      }
      else if (sleepremaining >= 30) {
        // Use 30ms interval
        sleepremaining-=30;
        sleepperiod = SLEEP_30MS;
      }
      else {
        // Use 15ms interval
        sleepperiod = SLEEP_15Ms;
        sleepremaining = 0;
      }
      Serial.flush();
      radio.sleep();
      LowPower.powerDown(sleepperiod, ADC_OFF, BOD_OFF);

//      Serial.print(F("Sleep remaining: "));
//      Serial.println(sleepremaining);
    }
    // Sleeptime eludes millis()
    looptime += LOOPPERIOD;
  }
  else {
    delay(LOOPPERIOD);
  }
} // end main loop

void processcmdstring(String cmdstring, int cmdlength, byte replynode){
//  Serial.print(F("Free memory: "));
//  Serial.println(freeRam());
  
//  Serial.println(F("processing cmdstring"));
//  Serial.println(cmdstring);
  
//  String //replystring="";

  int i;
  // this is as effective as clearing charstrings, since we'll just not
  // send what we haven't already written
  str1len=0;
  str2len=0;
  str3len=0;
  str4len=0;
  
  replylength=0;
  replystring[0]=0;
  
  if (cmdstring[0] == '~'){
//    Serial.println(F("Command character received"));
    int strord=1;
    for (i=1;i<cmdlength;i++){
      if (cmdstring[i] != ';' || strord == 4){
        if (cmdstring[i] != '\n' && cmdstring[i] != '\0' && cmdstring[i] != '\r'){
          if (strord == 1){
            charstr1[str1len]=cmdstring[i];
            str1len++;
          }
          else if (strord == 2){
            charstr2[str2len]=cmdstring[i];
            str2len++;
          }
          else if (strord == 3){
            charstr3[str3len]=cmdstring[i];
            str3len++;
          }
          else if (strord == 4){
            charstr4[str4len]=cmdstring[i];
            str4len++;
          }
          else {
            Serial.println(F("Error in parse"));
          }
        }
      } // cmdstring is not ;
      
      else { // cmdstring is ;
        strord ++;
      }  //cmdstring is ;
    } // for each character 
    // Terminate strings
    
    charstr1[str1len]=0;
    charstr2[str2len]=0;
    charstr3[str3len]=0;
    charstr4[str4len]=0;
    
    Serial.println(charstr1);
    Serial.println(charstr2);
    Serial.println(charstr3);
    Serial.println(charstr4);

      
    if (strcmp(charstr1,"lp")==0) {
        listparams(charstr2,atoi(charstr3));
        Serial.println(F("THE REPLYLENGTH"));
        Serial.println(replylength);
    }
    else if (strcmp(charstr1,"reset")==0) {
        FLASH_STRING(msgbuffer, "cmd:reset");
        msgbuffer.copy(&replystring[replylength], 9);
        replylength+=9;
//      resetMote();
    }
    else if (strcmp(charstr1,"gosleep")==0) {
      SLEEPDELAYTIMER=65535;  // send mote to sleep
    }
    else if (strcmp(charstr1,"modparam")==0) {
      FLASH_STRING(msgbuffer, "cmd:mp,");
      msgbuffer.copy(&replystring[replylength], 7);
      replylength+=7;
      
      Serial.println(charstr2);
      if (strcmp(charstr2,"loopperiod")==0) {
        FLASH_STRING(msgbuffer2, "param:loopperiod,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 26);
        replylength+=26;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        long newvalue = atoi(charstr3)*100;
        if (newvalue >= 0 && newvalue < 600000){
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
          // deliver in seconds, translate to ms
          LOOPPERIOD = newvalue;
          storeparams();
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:out of range");
          msgbuffer4.copy(&replystring[replylength], 27);
          replylength+=27;
        }
      } // loopperiod
      if (strcmp(charstr2,"sleepmode")==0) {
        FLASH_STRING(msgbuffer2, "param:sleepmode,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 26);
        replylength+=26;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 26);
        replylength+=1;
        
        byte newvalue = atoi(charstr3);
        if (newvalue == 0) {
          SLEEPMODE = 0;
          storeparams();
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
        }
        else if (newvalue == 1) {
          SLEEPMODE = 1;
          storeparams();
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:out of range");
          msgbuffer4.copy(&replystring[replylength], 27);
          replylength+=27;
        }
      } // sleepmode
      else if (strcmp(charstr2,"sleepdelay")==0) {
        FLASH_STRING(msgbuffer2, "param:sleepdelay,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 26);
        replylength+=26;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        long newvalue = atoi(charstr3)*100;
        if (newvalue >= 300 && newvalue < 60000){

          // deliver in 100s ms, translate to ms
          SLEEPDELAY = newvalue;
          storeparams();
        }
        else {
          //replystring+="Sleepdelay value out of range";
        }
      } // sleepdelay
      else if (strcmp(charstr2,"nodeid")==0) {
        FLASH_STRING(msgbuffer2, "param:nodeid,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 22);
        replylength+=22;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 2 && newvalue < 256){
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
          
          // deliver in seconds, translate to ms
          NODEID = newvalue;
          radio.setAddress(NODEID);
          storeparams();
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:out of range");
          msgbuffer4.copy(&replystring[replylength], 27);
          replylength+=27;
        }
      } // nodeid
      else if (strcmp(charstr2,"networkid")==0) {
        FLASH_STRING(msgbuffer2, "param:networkid,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 25);
        replylength+=25;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 1 && newvalue < 256){
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
          NETWORKID = newvalue;
          radio.writeReg(REG_SYNCVALUE2, NETWORKID);
          storeparams();
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:out of range");
          msgbuffer4.copy(&replystring[replylength], 27);
          replylength+=27;
        }
      } // network
      else if (strcmp(charstr2,"gatewayid")==0) {
        FLASH_STRING(msgbuffer2, "param:gatewayid,setvalue:");
        msgbuffer2.copy(&replystring[replylength], 25);
        replylength+=25;
        
        memcpy(&replystring[replylength], charstr3, str3len);
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 1 && newvalue < 256){
          FLASH_STRING(msgbuffer4, "status:0");
          msgbuffer4.copy(&replystring[replylength], 8);
          replylength+=8;
          GATEWAYID = newvalue;
          storeparams();
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:out of range");
          msgbuffer4.copy(&replystring[replylength], 27);
          replylength+=27;
        }
      } // network
      else if (strcmp(charstr2,"iomode")==0) {
        FLASH_STRING(msgbuffer2, "param:iomode,ionum:");
        msgbuffer2.copy(&replystring[replylength], 19);
        replylength+=19;

        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "iomode:");
          msgbuffer4.copy(&replystring[replylength], 6);
          replylength+=6;
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          
          int newvalue = atoi(charstr4);
          if (newvalue >= 0 && newvalue <5) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            replylength+=6;
            
            iomode[ionumber]=newvalue;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:iomode out of range");
            msgbuffer5.copy(&replystring[replylength], 34);
            replylength+=34;
          }
        }
        else {
          FLASH_STRING(msgbuffer4, "status:1,error:ionum out of range");
          msgbuffer4.copy(&replystring[replylength], 33);
          replylength+=33;
        }
      } // iomode
      else if (strcmp(charstr2,"ioenabled")==0) {
        FLASH_STRING(msgbuffer2, "param:ioenabled,ionum:");
        msgbuffer2.copy(&replystring[replylength], 25);
        replylength+=25;

        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "iomode:");
          msgbuffer4.copy(&replystring[replylength], 6);
          replylength+=6;
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            replylength+=6;
            
            ioenabled[ionumber] = 0;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else if (newvalue == 1) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            replylength+=6;
            
            ioenabled[ionumber] = 1;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:iomode out of range");
            msgbuffer5.copy(&replystring[replylength], 34);
            replylength+=34;
          }
        }
        else {
         FLASH_STRING(msgbuffer5, "status:1,error:ionumber out of range");
         msgbuffer5.copy(&replystring[replylength], 34);
         replylength+=34;
        }
      } // ioenabled
      else if (strcmp(charstr2,"ioreadfreq")==0) {
        FLASH_STRING(msgbuffer2, "param:ioreadfreq,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 26);
        replylength+=26;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;    
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          long newvalue = atoi(charstr4)*100;
          if (newvalue >= 0 && newvalue <600000) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            replylength+=6;
            ioreadfreq[ionumber]=newvalue;
            storeparams();
          }
          else{
            FLASH_STRING(msgbuffer5, "status:1,error:iovalue out of range");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
          }
        }
        else {
          Serial.println(F("ionumber out of range"));
        }
      } // ioreadfreq
      else if (strcmp(charstr2,"ioreportenabled")==0) {
        FLASH_STRING(msgbuffer2, "param:ioreportenabled,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 31);
        replylength+=31;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            ioreportenabled[ionumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            replylength+=8;
            ioreportenabled[ionumber] = 1;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:value out of range");
            msgbuffer5.copy(&replystring[replylength], 33);
            replylength+=33;
          }
        }
        else {
            FLASH_STRING(msgbuffer5, "status:1,error:ionumber out of range");
            msgbuffer5.copy(&replystring[replylength], 36);
            replylength+=36;
          }
      } // ioreport enabled
      else if (strcmp(charstr2,"ioreportfreq")==0) {
        FLASH_STRING(msgbuffer2, "param:ioreportfreq,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 31);
        replylength+=31;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          long newvalue = atoi(charstr4)*1000;
          if (newvalue >= 0 && newvalue <600000) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 6);
            ioreportfreq[ionumber]=newvalue;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:value out of range");
            msgbuffer5.copy(&replystring[replylength], 6);
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:ionumber out of range");
            msgbuffer5.copy(&replystring[replylength], 33);
            replylength+=33;
        }
      } // ioreportfreq
      else if (strcmp(charstr2,"iovalue")==0) {
        FLASH_STRING(msgbuffer2, "param:iovalue,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 23);
        replylength+=23;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          
          int newvalue = atoi(charstr4);
          if (newvalue >= 0) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            iovalue[ionumber]=newvalue;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:iovalue out of range");
            msgbuffer5.copy(&replystring[replylength], 6);
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:ionumber out of range");
            msgbuffer5.copy(&replystring[replylength], 33);
            replylength+=33;
        }
      } // iovalues
      else if (strcmp(charstr2,"chansv")==0) {
        FLASH_STRING(msgbuffer2, "param:chansv,channumber:");
        msgbuffer2.copy(&replystring[replylength], 24);
        replylength+=24;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          FLASH_STRING(msgbuffer3, ",");
          msgbuffer3.copy(&replystring[replylength], 1);
          replylength+=1;
        
          // need to allow for floats
          int newvalue = atoi(charstr4);      
          FLASH_STRING(msgbuffer5, "status:0");
          msgbuffer5.copy(&replystring[replylength], 8);
          replylength+=8;
          chansv[channumber]=newvalue;
          storeparams();
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:channumber out of range");
            msgbuffer5.copy(&replystring[replylength], 35);
            replylength+=35;
        }
      }// chansv
      else if (strcmp(charstr2,"chanpvindex")==0) {
        FLASH_STRING(msgbuffer2, "param:chanpvindex,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 27);
        replylength+=27;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          FLASH_STRING(msgbuffer3, ",");
          msgbuffer3.copy(&replystring[replylength], 1);
          replylength+=1;
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13){     
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            chanpvindex[channumber]=newvalue;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:setvalue out of range");
            msgbuffer5.copy(&replystring[replylength], 36);
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:channumber out of range");
          msgbuffer5.copy(&replystring[replylength], 35);
          replylength+=35;
        }
      }// chanpvindex
      else if (strcmp(charstr2,"chanposfdbk")==0) {
        FLASH_STRING(msgbuffer2, "param:chanposfdbk,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 27);
        replylength+=27;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          FLASH_STRING(msgbuffer3, ",");
          msgbuffer3.copy(&replystring[replylength], 1);
          replylength+=1;
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13){     
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            chanposfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:setvalue out of range");
            msgbuffer5.copy(&replystring[replylength], 36);
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:channumber out of range");
          msgbuffer5.copy(&replystring[replylength], 35);
          replylength+=35;
        }
      }// chanposfdbk
      else if (strcmp(charstr2,"channegfdbk")==0) {
        FLASH_STRING(msgbuffer2, "param:channegfdbk,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 27);
        replylength+=27;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          FLASH_STRING(msgbuffer3, ",");
          msgbuffer3.copy(&replystring[replylength], 1);
          replylength+=1;
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13){     
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            channegfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:setvalue out of range");
            msgbuffer5.copy(&replystring[replylength], 36);
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:channumber out of range");
            msgbuffer5.copy(&replystring[replylength], 35);
            replylength+=35;
        }
      }// channegfdbk
      else if (strcmp(charstr2,"chanenabled")==0) {
        FLASH_STRING(msgbuffer2, "param:chanenabled,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 27);
        replylength+=27;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        FLASH_STRING(msgbuffer3, ",");
        msgbuffer3.copy(&replystring[replylength], 1);
        replylength+=1;
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8) {
          FLASH_STRING(msgbuffer4, "setvalue:");
          msgbuffer4.copy(&replystring[replylength], 9);
          replylength+=9;
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          FLASH_STRING(msgbuffer3, ",");
          msgbuffer3.copy(&replystring[replylength], 1);
          replylength+=1;
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            chanenabled[channumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            FLASH_STRING(msgbuffer5, "status:0");
            msgbuffer5.copy(&replystring[replylength], 8);
            replylength+=8;
            chanenabled[channumber] = 1;
            storeparams();
          }
          else {
            FLASH_STRING(msgbuffer5, "status:1,error:setvalue out of range");
            msgbuffer5.copy(&replystring[replylength], 36);
            replylength+=36;
          }
        }
        else {
          FLASH_STRING(msgbuffer5, "status:1,error:channumber out of range");
            msgbuffer5.copy(&replystring[replylength], 35);
            replylength+=35;
        }
      } // chanenabled
    } // modparams
    else if (strcmp(charstr1,"sendmsg")==0){
      FLASH_STRING(msgbuffer, "cmd:sendmsg,destid:");
      msgbuffer.copy(&replystring[replylength], 19);
      replylength+=19;   
      
      memcpy(&replystring[replylength], charstr2, 7);
      replylength+=str2len;  
      
      FLASH_STRING(msgbuffer2, ",rp:");
      msgbuffer2.copy(&replystring[replylength], 4);
      replylength+=4;
      
      memcpy(&replystring[replylength], charstr3, str3len);
      replylength+=str3len;
      
      FLASH_STRING(msgbuffer3, ",msg:");
      msgbuffer3.copy(&replystring[replylength], 5);
      replylength+=5;
      
//      Serial.println(F("prereplylength"));
//      Serial.println(replylength);
//      Serial.println("str4len");
//      Serial.println(str4len);
      
      // If the message is too long, truncate it and add a termchar
      // to indicate the message was truncated
      byte reportmsglength=str4len;
      byte termchar=0;
      if (replylength+str4len<=61){
        reportmsglength=str4len;
      }
      else {
        reportmsglength=61-replylength-1;
        termchar=1;
      }
//      Serial.println("reportlen");
//      Serial.println(reportmsglength);
      memcpy(&replystring[replylength], charstr4, reportmsglength);
      replylength+=reportmsglength;
      if (termchar == 1) {
        memcpy(&replystring[replylength], "#", 1);
        replylength+=1;
      }
//      Serial.println(replylength);

      sendWithSerialNotify(atoi(charstr2), charstr4, str4len);
    }
    else if (strcmp(charstr1,"flashid")==0){
//      memcpy(&replystring[replylength], "cmd:flashid,flashid:", 19);
//      replylength+=19;
      for (i=0;i<8;i++){
        Serial.print(flash.UNIQUEID[i],HEX);
      }
    }
    else{
      FLASH_STRING(msgbuffer, "cmd:unknown,status:1,cmdstring:");
      msgbuffer.copy(&replystring[replylength], 31);
      replylength+=31;
      
      memcpy(&replystring[replylength], charstr1, str1len);
      replylength+=str1len;
    }
  } // first character indicates command sequence 
  // This is actually pretty unused and deprecated
  
//  else { // first character is not command
//    if (cmdstring[0] == 'r') //d=dump register values
//      radio.readAllRegs();
//      //if (input == 'E') //E=enable encryption
//      //  radio.encrypt(KEY);
//      //if (input == 'e') //e=disable encryption
//      //  radio.encrypt(null);
//
//    if (cmdstring[0] == 'd') //d=dump flash area
//    {
//      Serial.println(F("Flash content:"));
//      uint16_t counter = 0;
//
//      Serial.print(F("0-256: "));
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
    // Here is where we send a mesage
  Serial.print(F("REPLYSTRING - "));
  Serial.println(replylength);  
  replystring[replylength]=0;
  Serial.println(replystring);
  if (replynode > 0 && replylength>0) {
    Serial.print(F("Sending message to replynode: "));
    Serial.println(replynode);
    //replystring.toCharArray(buff,replystring.length()+1);
    radio.sendWithRetry(int(replynode),replystring , replylength);
  }
  Serial.print(F("Free memory: "));
  Serial.println(freeRam());
}
void sendWithSerialNotify(byte destination, char* sendstring, byte sendlength) {
  Serial.print(F("SENDING TO "));
  Serial.println(destination);
  Serial.println(sendstring);
  Serial.println(sendlength);
  radio.sendWithRetry(destination, sendstring, sendlength, 3, 300);
  Serial.println(F("SEND COMPLETE"));  
}
void initparams() {
    NODEID = 10;
    NETWORKID  = 105;
    GATEWAYID = 1;
    LOOPPERIOD = 1000;
    SLEEPMODE = 0;
    SLEEPDELAY = 1000;
    storeparams();
    int i;
    for (i=0;i<13;i++){
      iomode[i] = 0;
      ioenabled[i] = 0;
      ioreadfreq[i] = 1000;
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
//    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
//    radio.setAddress(NODEID);
    
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
    Serial.println(F("Getting parameters"));
    NODEID = EEPROM.read(0);
    NETWORKID = EEPROM.read(1);
    GATEWAYID = EEPROM.read(2);    
    
    // update object
    // We DON'T do this because it may not be instantiated yet.
    
//    Serial.println(REG_SYNCVALUE2);
//    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
//    radio.setAddress(NODEID);
    
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
void listparams(char* mode, byte dest) {
  int i;
  replylength=0;
  replystring[0]=0;
  if (strcmp(mode,"cfg")==0){
    Serial.println("CONFIG");
    FLASH_STRING(msgbuffer, "cmd:lp,node:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
  
    itoa(NODEID,&replystring[replylength],10);
    replylength+=2;
    
    FLASH_STRING(msgbuffer2, ",gw:");
    msgbuffer2.copy(&replystring[replylength], 4);
    replylength+=4;
    
    itoa(GATEWAYID,&replystring[replylength],10);
    replylength+=1;
    
    FLASH_STRING(msgbuffer3, ",nw:");
    msgbuffer3.copy(&replystring[replylength], 4);
    replylength+=4;
    
    itoa(NETWORKID,&replystring[replylength],10);
    replylength+=2;
    
    FLASH_STRING(msgbuffer4, ",loop:");
    msgbuffer4.copy(&replystring[replylength], 6);
    replylength+=6;
    
    itoa(LOOPPERIOD,&replystring[replylength],10);
    replylength+=log10(LOOPPERIOD)+1;
    
    FLASH_STRING(msgbuffer5, ",slpmd:");
    msgbuffer5.copy(&replystring[replylength], 7);
    replylength+=7;
    
    itoa(SLEEPMODE,&replystring[replylength],10);
    replylength+=1;
    
    FLASH_STRING(msgbuffer6, ",slpdly:");
    msgbuffer6.copy(&replystring[replylength], 8);
    replylength+=8;
    
    itoa(SLEEPDELAY,&replystring[replylength],10);
    replylength+=log(SLEEPDELAY);
    
    Serial.println(replylength);
  }
  else if (strcmp(mode,"iomd")==0) {     
    FLASH_STRING(msgbuffer, "cmd:lp,iomd:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    replylength = adddigitarraytostring(replystring, iomode, replylength, 13); 
  }
  else if (strcmp(mode,"ioen")==0) {
    FLASH_STRING(msgbuffer2, "cmd:lp,ioen:"); 
    msgbuffer2.copy(&replystring[replylength], 12);
    replylength+=12; 
    replylength = adddigitarraytostring(replystring, ioenabled, replylength, 13); 
  }
  else if (strcmp(mode,"iov")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=11;
    replylength=addfloatarraytostring(replystring, iovalue, replylength, 0, 4); 
  }
  else if (strcmp(mode,"iov2")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov2:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    replylength=addfloatarraytostring(replystring, iovalue, replylength, 5, 8); 
  }
  else if (strcmp(mode,"iov3")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov3:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    replylength=addfloatarraytostring(replystring, iovalue, replylength, 9, 12); 
  }
  else if (strcmp(mode,"iordf")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,iordf:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;
     
    for (i=0;i<13;i++) {
      itoa(ioreadfreq[i]/100,&replystring[replylength],10);
      replylength+=log10(ioreadfreq[i]/100)+1;
      FLASH_STRING(msgbuffer2, ",");
      msgbuffer2.copy(&replystring[replylength], 1);
      replylength+=1;
    }
    replystring[replylength-1]=0;
    replylength-=1;
//    Serial.println(replylength);
  }
  else if (strcmp(mode,"irpf")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,iorpf:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
     
    for (i=0;i<13;i++) {
      itoa(ioreportfreq[i]/100,&replystring[replylength],10);
      replylength+=log10(ioreportfreq[i]/100)+1;
      FLASH_STRING(msgbuffer2, ",");
      msgbuffer2.copy(&replystring[replylength], 1);
      replylength+=1;
    }
    replystring[replylength-1]=0;
    replylength-=1;
  }
  else if (strcmp(mode,"chen")==0) {     
    FLASH_STRING(msgbuffer, "cmd:lp,chen:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12; 
    replylength = adddigitarraytostring(replystring, chanenabled, replylength, 8); 
  }
  else if (strcmp(mode,"chmd")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chmd:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;    
    replylength = adddigitarraytostring(replystring, chanmode, replylength, 8); 
  }
  else if (strcmp(mode,"chpf")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chpf:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
     
    for (i=0;i<8;i++) {
        sprintf(&replystring[replylength], "%02d,",chanposfdbk[i]);
        replylength+=3;
    }
    replystring[replylength-1]=0;
  }
  else if (strcmp(mode,"chnf")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,chnf:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
     
    for (i=0;i<8;i++) {
        sprintf(&replystring[replylength], "%02d,",channegfdbk[i]);
        replylength+=3;
    }
    replystring[replylength-1]=0;
  }
  else if (strcmp(mode,"chdb")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chdb:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
     
    for (i=0;i<8;i++) {
        sprintf(&replystring[replylength], "%02d,",chandeadband[i]);
        replylength+=3;
    }
    replystring[replylength-1]=0;
  }
  else if (strcmp(mode,"chpv")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chpv:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;  
    replylength=addfloatarraytostring(replystring, chanpv, replylength, 0, 3);
  }
  else if (strcmp(mode,"chpv2")==0) {       
    sprintf(&replystring[replylength], "cmd:lp,chpv2:");
    replylength+=13;
    replylength=addfloatarraytostring(replystring, chanpv, replylength, 4, 7);
  }
  else if (strcmp(mode,"chsv")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,chsv:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;    
    replylength=addfloatarraytostring(replystring, chansv, replylength, 0, 3);
  }
  else if (strcmp(mode,"chsv2")==0) {  
    FLASH_STRING(msgbuffer, "cmd:lp,chsv2:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;
    replylength=addfloatarraytostring(replystring, chansv, replylength, 4, 7);
  }
  if (dest > 0){
    sendWithSerialNotify(dest, replystring, replylength);
  }
} // function def

int adddigitarraytostring(char *replystring, byte *array, byte replylength, byte entries){
         
    for (int i=0;i<entries;i++) {
        itoa(array[i],&replystring[replylength],10);
        replylength+=1;
        FLASH_STRING(msgbuffer2, ",");
        msgbuffer2.copy(&replystring[replylength], 1);
        replylength+=1;
    }
    replylength-=1;
    replystring[replylength]=0;
    return replylength;
}

int addfloatarraytostring(char *replystring, float *array, byte replylength, byte startindex, byte endindex){
         
    for (int i=startindex;i<endindex+1;i++) {
        int wholePart = array[i];
        long fractPart = (array[i] - wholePart) * 10000;
        sprintf(&replystring[replylength], "%04d.%04d,",wholePart, fractPart);
        replylength+=10;
    }
    replylength-=1;
    replystring[replylength]=0;
    return replylength;
}
    
void getfirstdsadd(OneWire myds, byte firstadd[]){
  byte i;
  byte present = 0;
  byte addr[8];
  float celsius, fahrenheit;
  
  int length = 8;
  
  //Serial.print("Looking for 1-Wire devices...\n\r");
  while(myds.search(addr)) {
    //Serial.print("\n\rFound \'1-Wire\' device with address:\n\r");
//    for( i = 0; i < 8; i++) {
//      firstadd[i]=addr[i];
//      //Serial.print("0x");
//      if (addr[i] < 16) {
//        Serial.print('0');
//      }
//      Serial.print(addr[i], HEX);
//      if (i < 7) {
//        Serial.print(", ");
//      }
//    }
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
  byte type_s=0;
  float celsius;
  float fahrenheit;
  
//  switch (addr[0]) {
//    case 0x10:
//      //Serial.println(F("  Chip = DS18S20"));  // or old DS1820
//      type_s = 1;
//      break;
//    case 0x28:
//      //Serial.println(F("  Chip = DS18B20"));
//      type_s = 0;
//      break;
//    case 0x22:
//      //Serial.println(F("  Chip = DS1822"));
//      type_s = 0;
//      break;
////    default:
////      Serial.println(F("Device is not a DS18x20 family device."));
//  } 
  
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
int freeRam ()
{
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}
void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
void sendInitMessage(){
//  sprintf(buff, "\nXmitting at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
//  Serial.println(buff);
//  sprintf(buff, "I am node: %d",NODEID);
  Serial.print(F("NODEID: "));
  Serial.println(NODEID);
}
void sendIOMessage(byte pin, byte mode, float value) {
  // Initialize send string

  int sendlength = 61;  // default
  if (mode == 0 || mode == 1 ) { // for integer values
    sendlength = 32;
//    char sendstring[sendlength];
    sprintf(buff, "iopin:%02d,iomode:%02d,iovalue:%04d", pin, mode, value);         
    sendWithSerialNotify(GATEWAYID, buff, sendlength);
  }
  else if (mode == 2){ // for float values
    int wholePart = value;
    long fractPart = (value - wholePart) * 10000;
    sendlength = 34; 
//    char sendstring[sendlength];
    sprintf(buff, "iopin:%02d,iomode:%02d,ioval:%03d.%04d", pin,mode,wholePart, fractPart);
    sendWithSerialNotify(GATEWAYID, buff, sendlength); 
  }
}
void handleOWIO(byte ioindex) {
  owpin = iopins[ioindex];
  
  // Device identifier
  byte dsaddr[8];
  char dscharaddr[16];
  OneWire myds(owpin);
  getfirstdsadd(myds,dsaddr);
  
//  Serial.print(F("dsaddress:"));
  int j;
  for (j=0;j<8;j++) {
    if (dsaddr[j] < 16) {
//      Serial.print('0');
    }
//    Serial.print(dsaddr[j], HEX);
  }
//  sprintf(dscharaddr,"%02x%02x%02x%02x%02x%02x%02x%02x",dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
//  Serial.println(',');
  
  // Data
//  Serial.print(F("temperature:"));
  iovalue[ioindex] = getdstemp(myds, dsaddr);
//  Serial.println(iovalue[ioindex]);
  
  if ((ioreportenabled[ioindex]) && (ioreportfreq[ioindex] == 0)){
    byte sendlength = 61;
    char sendstring[sendlength];
    
//    int wholePart = iovalue[ioindex];
//    long fractPart = (iovalue[ioindex] - wholePart) * 10000;
//    sprintf(sendstring, "owtmpasc:%03d.%04d,owdev:ds18x,owrom:%0xx%02x%02x%02x%02x%02x%02x%02x%02x", wholePart, fractPart, dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]); 
    sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
    
    sendIOMessage(iopins[ioindex], iomode[ioindex], iovalue[ioindex]);
  } // reportenabled and ioreportfreq
} // run OW sequence

