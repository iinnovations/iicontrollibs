
// Colin Reese, CuPID Controls, Interface Innovations
// UniMote sketch, based on the great example by lowpowerlab

// RFM69 and SPIFlash Library by Felix Rusu - felix@lowpowerlab.com
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

#define INIT 0
#define ACK_TIME      500 // max # of ms to wait for an ack
#define RETRIES 1

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

unsigned int LOOPPERIOD = 100; // ms

// constants
//PROGMEM char ionames[13][3] = { "D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","A7" };
byte iopins[13] = { 3,4,5,6,7,A0,A1,A2,A3,A4,A5,A6,A7 };
byte owpin;

byte serialrfecho;

// user-assigned variables
int8_t ioenabled[13];
int8_t iomode[13];
float iovalue[13];
int8_t ioreportenabled[13];
unsigned long ioreportfreq[13];
unsigned long ioreadfreq[13];

int8_t chanenabled[8] = {1,0,0,0,0,0,0,0};
int8_t chanposfdbk[8] = {0,0,0,0,0,0,0,0};   // -1 is no pos fdbk
int8_t channegfdbk[8] = {-1,0,0,0,0,0,0,0};  // -1 is no neg fdbk
int8_t chanmode[8]; // reserved
int8_t chandeadband[8];
int8_t chanstate[8];
int8_t chanpvindex[8] = {5,0,0,0,0,0,0,0};
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
char charstr1[57];
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
//  Serial.println(looptime);
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
            sendIOMessage(i, iomode[i], iovalue[i]);             
          } // ioreportfreq == 0
        }
        else if (iomode[i] == 1) { // Digital Output
//          Serial.print(F("Digital output configured for pin "));
//          Serial.println(iopins[i]);
          pinMode(iopins[i], OUTPUT);
          digitalWrite(iopins[i],iovalue[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sendIOMessage(i, iomode[i], iovalue[i]);
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
            sendIOMessage(i, iomode[i], iovalue[i]);
          } // ioreportfreq == 0 
        }
        else if (iomode[i] == 3) { // PWM
//          Serial.print(F("PWM Configured for pin"));
//          Serial.print(iopins[i]);
          
          // pwm code goes here
          
        } // If PWM
        // This 1Wire code is not optimized and reads synchronously
        // asynchronous has been written but needs to be squeezed in here
        else if (iomode[i] == 4) { //OneWire
//          Serial.print(F("1Wire configured for pin "));
//          Serial.println(iopins[i]);
          
          // pass ioindex to have the routine handle it
          handleOWIO(i);

        } // If OneWire

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
        sendIOMessage(i,iomode[i],iovalue[i]);
       
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
    int cmdlength =0;
    
    if (Serial.available() > 0)
    {
      Blink(LED,5);
      cmdlength = Serial.readBytes(buff, 60);
      for (i=0; i<cmdlength;i++){
//        Serial.print(buff[i]);
      }
//      Serial.println();
      // Send to gateway
      buff[cmdlength]=0;
      processcmdstring(buff, cmdlength, 0);
      
      // Reset sleepdelay timer
      millistart = millis();
      
    } // Serial available
    // END SERIAL RECEIVE
    
    // RADIO RECEIVE AND PROCESSING
    // Check for any received packets
    if (radio.receiveDone())
    {
      Blink(LED,5);
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
      byte replynode = radio.SENDERID;
      if (radio.ACKRequested())
      {
        radio.sendACK();
        Blink(LED,5);
        Serial.println(F(" - ACK sent"));
      } // ack requested
      if (cmdlength > 0){
        processcmdstring(buff, cmdlength, replynode);
      }

      
      
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
  
//  Blink(LED,3);
   
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
  

//    Serial.println(F("Command character received"));

// we need to prune ~ from first string only
  int strord=1;
  for (i=0;i<cmdlength;i++){
    if ((cmdstring[i] != ';' && cmdstring[i] != '\n' )|| strord == 4){
      if (cmdstring[i] != '\n' && cmdstring[i] != '\0' && cmdstring[i] != '\r' && ! (i==0 && cmdstring[i] == '~')){
        if (strord == 1){
          if (str1len < 56) {
            charstr1[str1len]=cmdstring[i];
          }
          else {
            charstr1[str1len]='#';
            strord++;
          }
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
      } // if not special character
    } // if not ;
    else { // cmdstring is ; or \n
      strord ++;
    }  //cmdstring is ;
  } // for each character 
  // Terminate strings
    
    charstr1[str1len]=0;
    charstr2[str2len]=0;
    charstr3[str3len]=0;
    charstr4[str4len]=0;
    
//    Serial.println(charstr1);
//    Serial.println(charstr2);
//    Serial.println(charstr3);
//    Serial.println(charstr4);
    
  if (cmdstring[0] == '~'){    
    if (strcmp(charstr1,"lp")==0) {
        listparams(charstr2,atoi(charstr3));
//        Serial.println(F("THE REPLYLENGTH"));
//        Serial.println(replylength);
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
    else if (strcmp(charstr1,"mp")==0) {
      
      // modparams sequence
      FLASH_STRING(msgbuffer, "cmd:mp,");
      msgbuffer.copy(&replystring[replylength], 7);
      replylength+=7;
      
//      Serial.println(charstr2);
      if (strcmp(charstr2,"loop")==0) {
        FLASH_STRING(msgbuffer2, "param:loop,sv:");
        msgbuffer2.copy(&replystring[replylength], 14);
        replylength+=14;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
 
        long newvalue = atoi(charstr3)*10;
        if (newvalue > 0 && newvalue < 600000){
          addstatusok(replystring, replylength);
            
          // deliver in seconds, translate to msio
          LOOPPERIOD = newvalue;
          storeparams();
        }
        else {
          addsverror(replystring,replylength);
        }
      } // loopperiod
      else if (strcmp(charstr2,"rfech")==0) {
        FLASH_STRING(msgbuffer2, "param:rfech,sv:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 0 && newvalue <= 1){
          addstatusok(replystring, replylength);
          // deliver in seconds, translate to msio
          serialrfecho = newvalue;
          storeparams();
        }
        else {
          addsverror(replystring,replylength);
        }
      } // loopperiod
      else if (strcmp(charstr2,"slpmd")==0) {
        FLASH_STRING(msgbuffer2, "param:slpmd,sv:");
        msgbuffer2.copy(&replystring[replylength], 15);
        replylength+=15;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        byte newvalue = atoi(charstr3);
        if (newvalue == 0) {
          SLEEPMODE = 0;
          storeparams();
          addstatusok(replystring, replylength);
        }
        else if (newvalue == 1) {
          SLEEPMODE = 1;
          storeparams();
          addstatusok(replystring, replylength);
        }
        else {
          addsverror(replystring,replylength);
        }
      } // sleepmode
      else if (strcmp(charstr2,"slpdly")==0) {
        FLASH_STRING(msgbuffer2, "param:slpdly,sv:");
        msgbuffer2.copy(&replystring[replylength], 16);
        replylength+=16;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
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
      else if (strcmp(charstr2,"node")==0) {
        FLASH_STRING(msgbuffer2, "param:node,sv:");
        msgbuffer2.copy(&replystring[replylength], 14);
        replylength+=14;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 2 && newvalue < 256  && str3len>0){
          addstatusok(replystring, replylength);
          
          // deliver in seconds, translate to ms
          NODEID = newvalue;
          radio.setAddress(NODEID);
          storeparams();
        }
        else {
          addsverror(replystring,replylength);
        }
      } // nodeid
      else if (strcmp(charstr2,"nw")==0) {
        FLASH_STRING(msgbuffer2, "param:nw,sv:");
        msgbuffer2.copy(&replystring[replylength], 12);
        replylength+=12;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;  
        addcomma(replystring,replylength);
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 1 && newvalue < 256  && str3len>0){
          addstatusok(replystring, replylength);
          NETWORKID = newvalue;
          radio.writeReg(REG_SYNCVALUE2, NETWORKID);
          storeparams();
        }
        else {
          addsverror(replystring,replylength);
        }
      } // network
      else if (strcmp(charstr2,"gw")==0) {
        FLASH_STRING(msgbuffer2, "param:gw,sv:");
        msgbuffer2.copy(&replystring[replylength], 12);
        replylength+=12;   
        memcpy(&replystring[replylength], charstr3, str3len);
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        long newvalue = atoi(charstr3);
        if (newvalue >= 1 && newvalue < 256  && str3len>0){
          addstatusok(replystring, replylength);
          GATEWAYID = newvalue;
          storeparams();
        }
        else {
          addsverror(replystring,replylength);
        }
      } // network
      else if (strcmp(charstr2,"iomd")==0) {
        FLASH_STRING(msgbuffer2, "param:iomd,ionum:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          addcomma(replystring,replylength); 
          
          int newvalue = atoi(charstr4);
          if (newvalue >= 0 && newvalue <5  && str4len>0) {
            addstatusok(replystring, replylength);
            
            iomode[ionumber]=newvalue;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      } // iomode
      else if (strcmp(charstr2,"ioen")==0) {
        FLASH_STRING(msgbuffer2, "param:ioen,ionum:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;

        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14 && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          addcomma(replystring,replylength);
          
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            addstatusok(replystring, replylength);
            
            ioenabled[ionumber] = 0;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else if (newvalue == 1) {
            addstatusok(replystring, replylength);
            
            ioenabled[ionumber] = 1;
            ioreadtimer[ionumber] = 9999999; // read now
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
         addindexerror(replystring,replylength);
        }
      } // ioenabled
      else if (strcmp(charstr2,"iordf")==0) {
        FLASH_STRING(msgbuffer2, "param:iordf,ionum:");
        msgbuffer2.copy(&replystring[replylength], 18);
        replylength+=18;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);   
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          addcomma(replystring,replylength); 
          long newvalue = atoi(charstr4)*100;
          if (newvalue >= 0 && newvalue <600000) {
            addstatusok(replystring, replylength);
            ioreadfreq[ionumber]=newvalue;
            storeparams();
          }
          else{
            addsverror(replystring,replylength);;
          }
        }
        else {
         addindexerror(replystring,replylength);
        }
      } // ioreadfreq
      else if (strcmp(charstr2,"iorpe")==0) {
        FLASH_STRING(msgbuffer2, "param:iorpe,ionumber:");
        msgbuffer2.copy(&replystring[replylength], 21);
        replylength+=21;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          addcomma(replystring,replylength); 
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            addstatusok(replystring, replylength);
            ioreportenabled[ionumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            addstatusok(replystring, replylength);
            ioreportenabled[ionumber] = 1;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
            addindexerror(replystring,replylength);
        }
      } // ioreport enabled
      else if (strcmp(charstr2,"iorpf")==0) {
        FLASH_STRING(msgbuffer2, "param:iorpf,ionum:");
        msgbuffer2.copy(&replystring[replylength], 18);
        replylength+=18;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          long newvalue = atoi(charstr4)*1000;
          if (newvalue >= 0 && newvalue <600000) {
            addstatusok(replystring, replylength);
            ioreportfreq[ionumber]=newvalue;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      } // ioreportfreq
      else if (strcmp(charstr2,"iov")==0) {
        FLASH_STRING(msgbuffer2, "param:iov,ionum:");
        msgbuffer2.copy(&replystring[replylength], 16);
        replylength+=16;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        addcomma(replystring,replylength);
        
        int ionumber = atoi(charstr3);
        if (ionumber >=0 && ionumber <14  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr4, str4len );
          replylength+=str4len;
          addcomma(replystring,replylength);
          int newvalue = atoi(charstr4);
          if (newvalue >= 0) {
            addstatusok(replystring, replylength);
            iovalue[ionumber]=newvalue;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      } // iovalues
      else if (strcmp(charstr2,"chansv")==0) {
        FLASH_STRING(msgbuffer2, "param:chansv,chnum:");
        msgbuffer2.copy(&replystring[replylength], 24);
        replylength+=24;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8  && str3len>0) {

          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          
          addcomma(replystring,replylength);
        
          // need to allow for floats
          int newvalue = atoi(charstr4);      
          addstatusok(replystring, replylength);
          chansv[channumber]=newvalue;
          storeparams();
        }
        else {
          addindexerror(replystring,replylength);
        }
      }// chansv
      else if (strcmp(charstr2,"chpvind")==0) {
        FLASH_STRING(msgbuffer2, "param:chanpvind,ionum:");
        msgbuffer2.copy(&replystring[replylength], 22);
        replylength+=22;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          
          addcomma(replystring,replylength);
          
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13){     
            addstatusok(replystring, replylength);
            chanpvindex[channumber]=newvalue;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      }// chanpvindex
      else if (strcmp(charstr2,"chpf")==0) {
        FLASH_STRING(msgbuffer2, "param:chpf,ionum:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8  && str3len>0) {
          addsv(replystring,replylength);
          
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          
          addcomma(replystring,replylength);
          
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13  && str3len>0){     
            addstatusok(replystring, replylength);
            chanposfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      }// chanposfdbk
      else if (strcmp(charstr2,"chnf")==0) {
        FLASH_STRING(msgbuffer2, "param:chnf,ionum:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          
          addcomma(replystring,replylength);
          
          int newvalue = atoi(charstr4);
          if (newvalue >=0 and newvalue <13  && str4len>0){     
            addstatusok(replystring, replylength);
            channegfdbk[channumber]=newvalue;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      }// channegfdbk
      else if (strcmp(charstr2,"chen")==0) {
        FLASH_STRING(msgbuffer2, "param:chen,ionum:");
        msgbuffer2.copy(&replystring[replylength], 17);
        replylength+=17;
        
        memcpy(&replystring[replylength], charstr3, str3len );
        replylength+=str3len;
        
        addcomma(replystring,replylength);
        
        int channumber = atoi(charstr3);
        if (channumber >=0 && channumber <=8  && str3len>0) {
          addsv(replystring,replylength);
          memcpy(&replystring[replylength], charstr3, str3len );
          replylength+=str3len;
          
          addcomma(replystring,replylength);
          
          int newvalue = atoi(charstr4);
          if (newvalue == 0) {
            addstatusok(replystring, replylength);
            chanenabled[channumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            addstatusok(replystring, replylength);
            chanenabled[channumber] = 1;
            storeparams();
          }
          else {
            addsverror(replystring,replylength);
          }
        }
        else {
          addindexerror(replystring,replylength);
        }
      } // chanenabled
      else {
        FLASH_STRING(msgbuffer, "unknown");
        msgbuffer.copy(&replystring[replylength], 7);
        replylength+=7;
      } // unknown
    } // modparams
    else if (strcmp(charstr1,"sendmsg")==0){
      FLASH_STRING(msgbuffer, "cmd:sendmsg,destid:");
      msgbuffer.copy(&replystring[replylength], 19);
      replylength+=19;   
      
      memcpy(&replystring[replylength], charstr2, 7);
      replylength+=str2len;  
      
      FLASH_STRING(msgbuffer2, ",rfech:");
      msgbuffer2.copy(&replystring[replylength], 7);
      replylength+=7;
      
      itoa(serialrfecho,&replystring[replylength],10);
      replylength+=1;
      
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
      Serial.println(charstr2);
      if (atoi(charstr2) > 0) {
        sendWithSerialNotify(atoi(charstr2), charstr4, str4len, atoi(charstr3));
      }
      // THis is the easiest way to send a message to serial:
      // specify a destination of zero
      else if (atoi(charstr2) == 0) {
        Serial.println(charstr4);
      }
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
  else {
    // This just echoes everything received on serial over rf
    if (serialrfecho) {
      Serial.println(F("we are in serialrf echo"));
      Serial.println(charstr1);
      Serial.println(str1len);
      
      FLASH_STRING(msgbuffer, "ser:");
      msgbuffer.copy(&replystring[replylength], 4);
      memcpy(&replystring[4], charstr1, str1len);
      replylength = 4 + str1len;
      
      // we actually don't want serial notify here, since a device on serial
      // might respond strangely. 
      sendWithSerialNotify(GATEWAYID,replystring,replylength, 0);

    }
    FLASH_STRING(msgbuffer, "cmd:unknown");
    msgbuffer.copy(&replystring[replylength], 31);
    replylength+=31;
  }
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
//  Serial.print(F("REPLYSTRING - "));
//  Serial.println(replylength);  
  replystring[replylength]=0;
  Serial.println(replystring);
//  Serial.println(replynode);
  if (replynode > 0 && replylength > 0) {
    Serial.print(F("Sending message to replynode -  "));
    Serial.println(replynode);

    sendWithSerialNotify(int(replynode),replystring , replylength, ~serialrfecho);
  }
//  Serial.print(F("Free memory: "));
//  Serial.println(freeRam());
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
void initparams() {
    NODEID = 10;
    NETWORKID  = 105;
    GATEWAYID = 1;
    LOOPPERIOD = 10;
    SLEEPMODE = 0;
    SLEEPDELAY = 1000;
    serialrfecho = 0;
    storeparams();
    int i;
    for (i=0;i<13;i++){
      iomode[i] = 0;
      ioenabled[i] = 0;
      ioreadfreq[i] = 1000;
      ioreportenabled[i]=0;
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
  // in 10ms increments, this is 2.5s
  if (LOOPPERIOD/10 > 256){
    EEPROM.write(3,256);
  }
  else {
    EEPROM.write(3,LOOPPERIOD/10);
  }
  
  EEPROM.write(4,SLEEPMODE);
  EEPROM.write(5,SLEEPDELAY);
  EEPROM.write(6,serialrfecho);
  
  int i;
  for (i=0;i<16;i++) {
//      EEPROM.write(i+10,ENCRYPTKEY[i]);
  }
  byte mybyte;
  for (i=0;i<13;i++){    
    EEPROM.write(i+30,iomode[i]);
    EEPROM.write(i+43,ioenabled[i]);
    EEPROM.write(i+69,ioreportenabled[i]);
    if (ioreadfreq[i]/1000 > 256){
      EEPROM.write(i+56,256);
    }
    else {
      mybyte = ioreadfreq[i] / 1000;
      EEPROM.write(i+56,mybyte);
    }
  } // for num io
  
  // channels data
  for (i=0;i<8;i++) {
    EEPROM.write(i+82,chanenabled[i]);
    EEPROM.write(i+90,chanmode[i]);
    EEPROM.write(i+98,chanposfdbk[i]);
    EEPROM.write(i+106,channegfdbk[i]);
    EEPROM.write(i+114,chandeadband[i]);
    EEPROM.write(i+122,chanpvindex[i]);
    EEPROM.write(i+130,chansv[i]);
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
    
    LOOPPERIOD = EEPROM.read(3) * 10;
    SLEEPMODE = EEPROM.read(4);
    SLEEPDELAY = EEPROM.read(5);
    serialrfecho = EEPROM.read(6);
 
    // io
    int i;
    for (i=0;i<13;i++){
      iomode[i] = EEPROM.read(i+30);
      ioenabled[i] = EEPROM.read(i+43);
      ioreadfreq[i] = EEPROM.read(i+56)*1000;  
      ioreportenabled[i] = EEPROM.read(i+69);    
    } // for io 
    
    //channels
    for (i=0;i<8;i++) {
      chanenabled[i] = EEPROM.read(i+82);
      chanmode[i] = EEPROM.read(i+90);
      chanposfdbk[i] = EEPROM.read(i+98);
      channegfdbk[i] = EEPROM.read(i+106);
      chandeadband[i] = EEPROM.read(i+114);
      chanpvindex[i] = EEPROM.read(i+122);
      chansv[i] = EEPROM.read(i+130);
    } // for channels
}
void listparams(char* mode, byte dest) {
  int i;
  replylength=0;
  replystring[0]=0;
  if (strcmp(mode,"cfg")==0){
    FLASH_STRING(msgbuffer, "cmd:lp,node:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
  
    itoa(NODEID,&replystring[replylength],10);
    replylength+=log10(NODEID)+1;
    
    FLASH_STRING(msgbuffer2, ",gw:");
    msgbuffer2.copy(&replystring[replylength], 4);
    replylength+=4;
    
    itoa(GATEWAYID,&replystring[replylength],10);
    replylength+=1;
    
    FLASH_STRING(msgbuffer3, ",nw:");
    msgbuffer3.copy(&replystring[replylength], 4);
    replylength+=4;
    
    itoa(NETWORKID,&replystring[replylength],10);
    replylength+=3;
    
    FLASH_STRING(msgbuffer4, ",loop:");
    msgbuffer4.copy(&replystring[replylength], 6);
    replylength+=6;
    
    itoa(LOOPPERIOD/10,&replystring[replylength],10);
    replylength+=log10(LOOPPERIOD/10)+1;
    
    FLASH_STRING(msgbuffer5, ",rfech:");
    msgbuffer5.copy(&replystring[replylength], 7);
    replylength+=7;
    
    itoa(serialrfecho,&replystring[replylength],10);
    replylength+=1;
    
    FLASH_STRING(msgbuffer6, ",slpmd:");
    msgbuffer6.copy(&replystring[replylength], 7);
    replylength+=7;
    
    itoa(SLEEPMODE,&replystring[replylength],10);
    replylength+=1;
    
    FLASH_STRING(msgbuffer7, ",slpdly:");
    msgbuffer7.copy(&replystring[replylength], 8);
    replylength+=8;
    
    itoa(SLEEPDELAY/100,&replystring[replylength],10);
    replylength+=log10(SLEEPDELAY/100);
    
//    Serial.println(freeRam());
  }
  else if (strcmp(mode,"iomd")==0) {     
    FLASH_STRING(msgbuffer, "cmd:lp,iomd:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    adddigitarraytostring(replystring, iomode, replylength, 13); 
  }
  else if (strcmp(mode,"ioen")==0) {
    FLASH_STRING(msgbuffer2, "cmd:lp,ioen:"); 
    msgbuffer2.copy(&replystring[replylength], 12);
    replylength+=12; 
    adddigitarraytostring(replystring, ioenabled, replylength, 13); 
  }
  else if (strcmp(mode,"iorpe")==0) {
    FLASH_STRING(msgbuffer2, "cmd:lp,iorpe:"); 
    msgbuffer2.copy(&replystring[replylength], 13);
    replylength+=13; 
    adddigitarraytostring(replystring, ioreportenabled, replylength, 13); 
  }
  else if (strcmp(mode,"iov")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=11;
    addfloatarraytostring(replystring, iovalue, replylength, 0, 4); 
  }
  else if (strcmp(mode,"iov2")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov2:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    addfloatarraytostring(replystring, iovalue, replylength, 5, 8); 
  }
  else if (strcmp(mode,"iov3")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,iov3:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    addfloatarraytostring(replystring, iovalue, replylength, 9, 12); 
  }
  else if (strcmp(mode,"iordf")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,iordf:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;
    addulongdigitarraytostring(replystring, ioreadfreq, replylength, 13, 100); 
    Serial.println(freeRam());
  }
  else if (strcmp(mode,"iorpf")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,iorpf:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;
    addulongdigitarraytostring(replystring, ioreportfreq, replylength, 13, 100); 
  }
  else if (strcmp(mode,"chen")==0) {     
    FLASH_STRING(msgbuffer, "cmd:lp,chen:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12; 
    adddigitarraytostring(replystring, chanenabled, replylength, 8); 
  }
  else if (strcmp(mode,"iorpe")==0) {     
    FLASH_STRING(msgbuffer, "cmd:lp,iorpe:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13; 
    adddigitarraytostring(replystring, ioreportenabled, replylength, 13); 
  }
  else if (strcmp(mode,"chmd")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chmd:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;    
    adddigitarraytostring(replystring, chanmode, replylength, 8); 
  }
  else if (strcmp(mode,"chpf")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chpf:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;    
    adddigitarraytostring(replystring, chanposfdbk, replylength, 8);
  }
  else if (strcmp(mode,"chnf")==0) {
    FLASH_STRING(msgbuffer, "cmd:lp,chnf:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    adddigitarraytostring(replystring, channegfdbk, replylength, 8);
  }
  else if (strcmp(mode,"chdb")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chdb:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;
    adddigitarraytostring(replystring, chandeadband, replylength, 8);  
  }
  else if (strcmp(mode,"chpv")==0) {      
    FLASH_STRING(msgbuffer, "cmd:lp,chpv:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;  
    addfloatarraytostring(replystring, chanpv, replylength, 0, 3);
  }
  else if (strcmp(mode,"chpv2")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,chpv2:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;  
    addfloatarraytostring(replystring, chanpv, replylength, 4, 7);
  }
  else if (strcmp(mode,"chsv")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,chsv:");
    msgbuffer.copy(&replystring[replylength], 12);
    replylength+=12;    
    addfloatarraytostring(replystring, chansv, replylength, 0, 3);
  }
  else if (strcmp(mode,"chsv2")==0) {  
    FLASH_STRING(msgbuffer, "cmd:lp,chsv2:");
    msgbuffer.copy(&replystring[replylength], 13);
    replylength+=13;
    addfloatarraytostring(replystring, chansv, replylength, 4, 7);
  }
  else if (strcmp(mode,"chpvind")==0) {       
    FLASH_STRING(msgbuffer, "cmd:lp,chpvind:");
    msgbuffer.copy(&replystring[replylength], 15);
    replylength+=15;
    adddigitarraytostring(replystring, chanpvindex, replylength, 8);
  }
  else {
    FLASH_STRING(msgbuffer, "cmd:lp,unknown");
    msgbuffer.copy(&replystring[replylength], 15);
    replylength+=14;
  }
  if (dest > 0){
    // echo locally unless we are in rf serialecho, as this may produce
    // strange results with attached devices.
    sendWithSerialNotify(dest, replystring, replylength, ~serialrfecho);
  }
} // function def

void addcomma(char *replystring, byte &replylength) {
  FLASH_STRING(msgbuffer, ",");
  msgbuffer.copy(&replystring[replylength], 1);
  replylength+=1;
}
void addsv(char *replystring, byte &replylength) {
  FLASH_STRING(msgbuffer4, "sv:");
  msgbuffer4.copy(&replystring[replylength], 3);
  replylength+=3;
}
int addsverror(char *replystring, byte replylength){
  FLASH_STRING(msgbuffer4, "status:1,err:sv");
  msgbuffer4.copy(&replystring[replylength], 15);
  replylength+=15;
}
int addindexerror(char *replystring, byte &replylength){
  FLASH_STRING(msgbuffer4, "status:1,err:index");
  msgbuffer4.copy(&replystring[replylength], 18);
  replylength+=18;
}
int addstatusok(char *replystring, byte &replylength) {
  FLASH_STRING(msgbuffer4, "status:0");
  msgbuffer4.copy(&replystring[replylength], 8);
  replylength+=8;
}  
void adddigitarraytostring(char *replystring, int8_t *array, byte &replylength, byte entries){
  FLASH_STRING(msgbuffer2, "|");
  for (int i=0;i<entries;i++) {
    itoa(array[i],&replystring[replylength],10);
    if (array[i] == 0){
      replylength+=1;
    }
    else if (array[i]<0){
      replylength+=log10(-1*array[i])+2;
    }
    else {
      replylength+=log10(array[i])+1;
    }  
    msgbuffer2.copy(&replystring[replylength], 1);
    replylength+=1;
  }
  replylength-=1;
  replystring[replylength]=0;
}
void addulongdigitarraytostring(char *replystring, unsigned long *array, byte &replylength, byte entries, byte scale){
  FLASH_STRING(msgbuffer2, "|");
  for (int i=0;i<entries;i++) {
    itoa(array[i]/scale,&replystring[replylength],10);
    if (array[i]/scale == 0){
      replylength+=1;
    }
    else if (array[i]<0){
      replylength+=log10(-1*array[i]/scale)+2;
    }
    else {
      replylength+=log10(array[i]/scale)+1;
    }
    msgbuffer2.copy(&replystring[replylength], 1);
    replylength+=1;
  }
  replylength-=1;
  replystring[replylength]=0;
}
void addfloatarraytostring(char *replystring, float *array, byte &replylength, byte startindex, byte endindex){    
    for (int i=startindex;i<endindex+1;i++) {
        int wholePart = array[i];
        long fractPart = (array[i] - wholePart) * 10000;
        sprintf(&replystring[replylength], "%04d.%04d|",wholePart, fractPart);
        replylength+=10;
    }
    replylength-=1;
    replystring[replylength]=0;
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
  
  delay(800);     // maybe 750ms is enough, maybe not
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

  celsius=calctemp(data);

  fahrenheit = celsius * 1.8 + 32.0;
  //Serial.print('Celsius:');
  //Serial.println(celsius);
  return celsius;
}

float calctemp(byte data[]) {
  float celsius;
  
  unsigned int TReading = (data[1] << 8) + data[0];
  unsigned int SignBit = TReading & 0x8000;  // test most sig bit
  if (SignBit) // negative
  {
    TReading = (TReading ^ 0xffff) + 1; // 2's comp
  }
  celsius = float(TReading)/16;
  
  if (SignBit){
    celsius = celsius * -1;
  }
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
void sendIOMessage(byte ionum, byte mode, float value) {
  // Initialize send string

  int sendlength = 61;  // default
  if (mode == 0 || mode == 1 ) { // for integer values
    sendlength = 30;
//    char sendstring[sendlength];
    sprintf(buff, "ionum:%02d,iomode:%02d,ioval:%04d", ionum, mode, value);         
    sendWithSerialNotify(GATEWAYID, buff, sendlength,~serialrfecho);
  }
  else if (mode == 2){ // for float values
    int wholePart = value;
    long fractPart = (value - wholePart) * 10000;
    sendlength = 34; 
//    char sendstring[sendlength];
    sprintf(buff, "ionum:%02d,iomode:%02d,ioval:%03d.%04d", ionum,mode,wholePart, fractPart);
    sendWithSerialNotify(GATEWAYID, buff, sendlength,~serialrfecho); 
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
//  int j;
//  for (j=0;j<8;j++) {
//    if (dsaddr[j] < 16) {
////      Serial.print('0');
//    }
////    Serial.print(dsaddr[j], HEX);
//  }
//  sprintf(dscharaddr,"%02x%02x%02x%02x%02x%02x%02x%02x",dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
//  Serial.println(',');
  
  // Data
//  Serial.print(F("temperature:"));
  iovalue[ioindex] = getdstemp(myds, dsaddr);
//  Serial.println(iovalue[ioindex]);
  
  if ((ioreportenabled[ioindex]) && (ioreportfreq[ioindex] == 0)){

    // This is reporting of onewire data regardless of other stuff
    // it is unnecessary
//    byte sendlength = 61;
//    char sendstring[sendlength];
//    int wholePart = iovalue[ioindex];
//    long fractPart = (iovalue[ioindex] - wholePart) * 10000;
//    sprintf(sendstring, "owtmpasc:%03d.%04d,owdev:ds18x,owrom:%0xx%02x%02x%02x%02x%02x%02x%02x%02x", wholePart, fractPart, dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]); 
//    sendWithSerialNotify(GATEWAYID, sendstring, sendlength,1);
    
    sendIOMessage(ioindex, iomode[ioindex], iovalue[ioindex]);
  } // reportenabled and ioreportfreq
} // run OW sequence

