// Sample RFM69 sender/node sketch, with ACK and optional encryption
// Sends periodic messages of increasing length to gateway (id=1)
// It also looks for an onboard FLASH chip, if present
// Library and code by Felix Rusu - felix@lowpowerlab.com
// Get the RFM69 and SPIFlash library at: https://github.com/LowPowerLab/
#include <RFM69.h>
//#include <RFM69registers.h>
#include <SPI.h>
#include <SPIFlash.h>
#include <OneWire.h>
#include <EEPROM.h>
#include <Encoder.h>
#include <LedControl.h>

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
#define IS_RFM69HW    //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define REG_SYNCVALUE2 0x30


#ifdef __AVR_ATmega1284P__
  #define LED           15 // Moteino MEGAs have LEDs on D15
  #define FLASH_SS      23 // and FLASH SS on D23
#else
  #define LED           9 // Moteinos have LEDs on D9
  #define FLASH_SS      8 // and FLASH SS on D8
#endif

#define SERIAL_BAUD   115200

#define DEBUG 1
#define OWRES 12
#define numio 25
#define INIT 0
#define ACK_TIME      30 // max # of ms to wait for an ack

byte NODEID = 15;
byte NETWORKID = 100;
byte GATEWAYID = 1;
 
#define ENCRYPTKEY    "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!

byte SLEEPMODE;
unsigned int SLEEPDELAY; // ms
unsigned int SLEEPDELAYTIMER; // ms

//int TRANSMITPERIOD = 300; //transmit a packet to gateway so often (in ms)
//char buff[20];
boolean requestACK = false;
SPIFlash flash(FLASH_SS, 0xEF30); //EF30 for 4mbit  Windbond chip (W25X40CL)
RFM69 radio;

unsigned int LOOPPERIOD = 20; // ms

// constants
byte iopins[25] = { 0,1,3,8,9,10,11,12,13,14,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31 };
byte owpin;

// user-assigned variables
byte ioenabled[numio];
byte iomode[numio];
float iovalue[numio];
byte ioreportenabled[numio];
unsigned long ioreportfreq[numio];
unsigned long ioreadfreq[numio];

byte chanenabled[8] = {1,0,0,0,0,0,0,0};
int8_t chanposfdbk[8] = {0,0,0,0,0,0,0,0};   // -1 is no pos fdbk
int8_t channegfdbk[8] = {-1,0,0,0,0,0,0,0};  // -1 is no neg fdbk
byte chanmode[8]; // reserved for different feedback types
byte chandeadband[8]; // tentbs of units
long chandelay[8] = {30000,0,0,0,0,0,0,0};
unsigned long chantimer[8];
byte chanstate[8];
byte chanpvindex[8] = {5,0,0,0,0,0,0,0};
float chanpv[8];
float chansv[8] = {15,0,0,0,0,0,0,0};
float chanactreset[8] = {0,0,0,0,0,0,0,0};


// Set up LCD display
// data, clock, load
LedControl lc=LedControl(18,16,17,1);
unsigned long lcdvalue = 28;
unsigned long lastlcdvalue;
byte lcdbrightness = 8;

// menu setup
int menux = 0;
int menuy = 0;
byte blinky = 1;
byte barblinky = 1;
byte displayon = 1;
char tempmode = 'F'; // C or F
unsigned long lastactivity = 0;
unsigned long activityspacing = 300;
unsigned long inactivitydelay = 60000;

// Set pins on encoder
byte encoderButtonPin = 10;
Encoder knob(11,12);
long knobPos=0;
int knobIncrement;
byte buttondown = 0;

// Set up bar display pins
byte barlatchPin = 20;
byte barclockPin = 21;
byte bardataPin = 19;
  
unsigned long ioreporttimer[numio];
unsigned long ioreadtimer[numio];
unsigned long chanreporttimer[8];

unsigned long prevtime = 0;
unsigned long looptime = 0;
unsigned long loopcount;
  
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
    Serial.println(F("SPI Flash Init FAIL! (is chip present?)"));
  }
  
  // Initialize variables to/from EEPROM
  if (INIT) {
    Serial.println("Initializing variables to default values");
    initparams();
    storeparams();
  } // INIT
  else { // not init
    Serial.println(F("Restoring Parameters from memory"));
  } // not INIT
  
  getparams();
  // These are values that are not ever stored permanently
  int i;
  for (i=0;i<numio;i++) {
     ioreportenabled[i] = ioenabled[i];
     ioreportfreq[i] = 0; // 0 means report when read
     ioreporttimer[i] = 9999999;
     ioreadtimer[i] = 9999999;
  }
  radio.encrypt(ENCRYPTKEY);
  sendInitMessage();
  
  // Set up bar display
  pinMode(barlatchPin, OUTPUT);
  pinMode(barclockPin, OUTPUT);
  pinMode(bardataPin, OUTPUT);
  
  // Set up encoder
//  pinMode (encoderPinA,INPUT_PULLUP);
//  pinMode (encoderPinB,INPUT_PULLUP);
  pinMode (encoderButtonPin,INPUT_PULLUP);
  attachInterrupt (0,doButton,FALLING);
//  attachInterrupt(1, doEncoder, RISING);
  
  /*
  The MAX72XX is in power-saving mode on startup,
  we have to do a wakeup call 
  */
  lc.shutdown(0,false);
  /* Set the brightness to a medium values */
  lc.setIntensity(0,lcdbrightness);
  /* and clear the display */
  lc.clearDisplay(0);
  
  // Set some parameters for temporary
  // This is a 1Wire sensor and the channel that runs on it
  chanpvindex[0] = 23;
  ioenabled[23]=1;
  iomode[23]=4;
  
}

void loop() { 
  
  loopcount++;
  if (loopcount>100){
    loopcount = 0;
    Serial.print(F("Free RAM: "));
    Serial.println(freeRam());
  }
  
//  Serial.println();
//  thetime=4294967292;
//  thenewtime=5;
//  Serial.println(thenewtime-thetime);
  
  long newKnobPos;
 
  // sign is reversed here, due to the sign convention of interrupts
  // built into the encoder library
  
  newKnobPos = knob.read();
  if (newKnobPos != knobPos) {
    lastactivity = millis();
    knobIncrement+=(newKnobPos-knobPos);
    if (knobIncrement>3){
      handleEncoderCommand(-1);
//      printMenuInfo();
      knobIncrement=0;
    }
    else if (knobIncrement<-3){
      handleEncoderCommand(1);
//      printMenuInfo();
      knobIncrement=0;
    }
    knobPos=newKnobPos;
  }
  if (millis() - lastactivity > inactivitydelay) {
    menux = 0;
    menuy = 0;
  }
  
  // READ IO
  looptime += millis() - prevtime; // includes time taken to process
  int i;
  for (i=0;i<numio;i++) {
    // We use the values 9999999 and 9999998 for special meaning
    if (ioreporttimer[i] < 9999998){
      ioreporttimer[i] += looptime;
    }
    if (ioreadtimer[i] < 9999998){
      ioreadtimer[i] += looptime;
    }
  }
  prevtime = millis();
  looptime = 0; // we keep this around to add time that isn't counted (sleeptime)
  
  // for each io
  for (i=0;i<numio;i++){
    if (ioenabled[i]) {
  
      if (ioreadtimer[i] > ioreadfreq[i]) {
        
        // Determine mode and what to read
        if (iomode[i] == 0) { // Digital Input
          Serial.print(F("Digital input configured for pin "));
          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = digitalRead(iopins[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
//            sendIOMessage(iopins[i], iomode[i], iovalue[i]);             
          } // ioreportfreq == 0
          ioreadtimer[i] = 0;
        }
        else if (iomode[i] == 1) { // Digital Output
//          Serial.print(F("Digital output configured for pin "));
//          Serial.println(iopins[i]);
          pinMode(iopins[i], OUTPUT);
          digitalWrite(iopins[i],iovalue[i]);
          
          // send/broadcast if enabled and freq is 0
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
//            sendIOMessage(iopins[i], iomode[i], iovalue[i]);
          } // ioreportfreq == 0
          ioreadtimer[i] = 0;
        }
        else if (iomode[i] == 2) { // Analog Input
          Serial.print(F("Analog input configured for pin "));
          Serial.println(iopins[i]);
          pinMode(iopins[i], INPUT);      // sets the digital pin 7 as input
          iovalue[i] = analogRead(iopins[i]);
          Serial.print(F("Value: "));
//          Serial.println(iovalue[i]);
//          int wholePart = iovalue[i];
          if ((ioreportenabled[i]) && (ioreportfreq[i] == 0)){
            sendIOMessage(iopins[i], iomode[i], iovalue[i]);
          } // ioreportfreq == 0 
          ioreadtimer[i] = 0;
        }
        else if (iomode[i] == 4 || iomode[i] == 5) { //OneWire
          // iomode 5 is reading scratchpad. iomode 4 is issuing
          // a conversion
          
          // Set ioreadtimer based on conversion time. 
          // We take ioreadfreq, subtract our conversion time, and set ioreadtimer
          // to the correct value to instigate a read after conversion
          // We change the iomode for scratchpad read on next time
          
          if (iomode[i] == 4) {
            Serial.print(F("1Wire configured for pin: "));
            Serial.println(iopins[i]);
            // returns conversion time in ms
            int converttime = dsconvertfromioindex(i);
//            Serial.print(F("converttime: "));
//            Serial.println(converttime);
            ioreadtimer[i] = ioreadfreq[i] - converttime;

//            Serial.print(F("setting readtimer to "));
//            Serial.println(ioreadtimer[i]);
            
            iomode[i] = 5;
          }
          else if (iomode[i] == 5){
//            Serial.println("Reading Scratchpad");
            handleOWIO(i);
            iomode[i] = 4;
            ioreadtimer[i] = 0;

          }
        } // If OneWire
        else if (iomode[i] == 3) { // PWM
          Serial.print(F("PWM Configured for pin"));
          Serial.print(iopins[i]);
          
          // pwm code goes here
          ioreadtimer[i] = 0;
          
        } // If PWM
      } // If timer   
    } // If enabled
    else { // not enabled
    } // not enabled
  } // for i=0 --> numio
  // END READ IO
  
  
  // REPORTING 
  for (i=0;i<numio;i++){
    // remember that ioreportfreq=0 means report when read
    if (ioreportenabled[i] && ioreportfreq[i] > 0 && ioreporttimer[i] > ioreportfreq[i]){
        
        // this is a bit more general than the on-the-fly reporting
        // most notably, no onewire address or type
        
        // Initialize send string
        char sendstring[61];
        int sendlength = 61;  // default
        sendIOMessage(iopins[i],iomode[i],iovalue[i]);
       
    } // time to report
  }
  // END REPORTING
  
  
  // PROCESS CHANNELS
  for (i=0;i<8;i++) {
    // we moved this to assign even when not enabled
    
    chanpv[i]=iovalue[chanpvindex[i]];
    if (chanenabled[i]) {
//      Serial.print(F("Channel "));
//      Serial.print(i);
//      Serial.println(F(" value: "));
        byte chancondition = chanstate[i] / 10;
        byte chanaction = chanstate[i] % 10;
        
//      Serial.println(chanpv[i]);
//      Serial.println(F("Setpoint value: "));
//      Serial.println(chansv[i]);
      if ((chanpv[i] - chansv[i]) * 10 > chandeadband[i]) {
        
        // If condition has changed, set timer
        if (chancondition != 1) {
           chantimer[i] = millis();
           chancondition = 1;
        }
        // check to ensure we are ready
        if (millis() - chantimer[i] > chandelay[i]) {
          if (chanaction != 1 ){
            Serial.println(F("Setting negative action"));
          }
          chanaction = 1;
  //        Serial.print(F("Neg feedback: "));
          // set opposing feedback to zero first
          if (chanposfdbk[i] >=0){
            iovalue[chanposfdbk[i]]=0;
            // update now if we are changing the value
            if (iovalue[chanposfdbk[i]]!=0) {
              ioreadtimer[chanposfdbk[i]]=999999;
            }
          } 
        }
        // Then set desired feedback
        if (channegfdbk[i] >=0){
          iovalue[channegfdbk[i]]=1;
          // update now if we are changing the value
          if (iovalue[channegfdbk[i]]!=1) {
            ioreadtimer[channegfdbk[i]]=999999;
          }
        } // chandelay reached
        else {
//          Serial.println("Channel delay not reached for neg fdbk");
        }
      }
      else if ((chansv[i] - chanpv[i]) * 10 > chandeadband[i]) {
        
        // If condition has changed, set timer
        if (chancondition != 2) {
           chantimer[i] = millis();
           chancondition = 2;
        }
        // check to ensure we are ready
        if (millis() - chantimer[i] > chandelay[i] || chanaction == 2) {
          if (chanaction != 2) {
            Serial.println(F("Setting positive action"));
          }
          chanaction=2;
  //        Serial.print(F("Pos feedback: "));
          // set opposing feedback to zero first
          if (channegfdbk[i] >=0){
            iovalue[channegfdbk[i]]=0;
            // update now if we are changing the value
            if (iovalue[channegfdbk[i]]!=0) {
              ioreadtimer[channegfdbk[i]]=999999;
            }
          }
          // Then set desired feedback
          if (chanposfdbk[i] >=0){
            iovalue[chanposfdbk[i]]=1;
            // update now if we are changing the value
            if (iovalue[chanposfdbk[i]]!=1) {
              ioreadtimer[chanposfdbk[i]]=999999;
            }
          }
        } // chandelay reached
        else {
//          Serial.println("Channel delay not reached for pos fdbk");
        }
      }
      else {
        // If condition has changed, set timer
        if (chancondition != 0) {
           chantimer[i] = millis();
           chancondition = 0;
        }
        // check to ensure we are ready
        if (millis() - chantimer[i] > chandelay[i] || chanaction == 0) {
          chanaction = 0;
          
          // set positive and negative action to none   
          if (channegfdbk[i] >=0){
            iovalue[channegfdbk[i]]=0;
          }
          if (chanposfdbk[i] >=0){
            iovalue[chanposfdbk[i]]=0;
          }
        }// timer reached
        else {
          Serial.println("Channel delay not reached for disable");
        }
      }
      chanstate[i] = chancondition * 10 + chanaction;
//      Serial.println("Chanstate");
//      Serial.println(chanstate[i]);
    } // channel enabled
    else if (chanactreset[i]) {
      // We need to consider that there are 8 channels, and inactive channels
      // could interfere with active ones if we don't set placeholders in inactive
      // channels to ensure they don't. Filling them with -1s would work ... or 
      // disabling on chanenabled state change
      Serial.println("active reset!");
      iovalue[chanposfdbk[i]]=0;
      iovalue[channegfdbk[i]]=0;
    }   
  } // for channels
  // END PROCESS CHANNELS
  
  // SERIAL RECEIVE AND PROCESSING
  // Check for any received packets
  if (Serial.available() > 0)
  {
    String cmdstring = Serial.readStringUntil('\n');
    Serial.println(cmdstring);
    processcmdstring(cmdstring);
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
    
  } // Radio Receive
  // END RADIO RECEIVE

  // DISPLAY HANDLING
 
  handledisplay();
  
//  delay(LOOPPERIOD);
  
  handleBarDisplay(LOOPPERIOD);
  
  Blink(LED,3);
  
} // end main loop

void handleEncoderCommand(int menuInc) {
    
    // Menu navigation
    if (menuy == 1) {
      if (menuInc == 1 and menux < 3){
        menux++;
        Serial.println("direction 1");
      }
      else if (menuInc == -1 && menux > -3){
        menux--;
        Serial.println("direction 0");
      }
    } // menuy = 1
    
    // Set menus
    else if (menuy == 2){

      if (menux == 1) { // setpoint menu
        Serial.println("setpoint menu");
        
        if (menuInc == 1) {
          if (tempmode == 'F'){
            // Round to nearest 0.1 in F, increment in F
            // then convert back
            Serial.println("SV: ");
            Serial.println(chansv[0]);
            Serial.println((int)(chansv[0]*1.8*2.0 +0.5));
            Serial.println(((float)((int)(chansv[0]*1.8*2.0))*5.0));
            Serial.println(((float)((int)(chansv[0]*1.8*2.0))*5.0+5.0));
            Serial.println(((float)((int)(chansv[0]*1.8*2.0))*5.0+5.0)/(18.0));
            Serial.println("New SV: ");
            Serial.println(((float)((int)(chansv[0]*1.8*2.0 + 0.5))*5.0+5.0)/(18.0));
            chansv[0]=((float)((int)(chansv[0]*1.8*2.0 +0.5))*5.0+5.0)/(18.0);
          }
          else {
            chansv[0]=(float)((int)(chansv[0]*10))/10.0+0.1;
          }
        }
        else if (menuInc == -1){
          if (tempmode == 'F') {
            // Round to nearest 0.5 in F, decrement in F
            // then convert back
            Serial.println((chansv[0]*18.0));
            Serial.println((int)(chansv[0]*18.0));
            chansv[0]=((float)((int)(chansv[0]*1.8*2.0 +0.5))*5.0-5.0)/(18.0);
          }
          else {
            chansv[0]=(float)((int)(chansv[0]*10))/10.0-0.1;
          }
        }
      } // SV menu
      else if (menux == 2) { // deadband menu
        Serial.println("deadband menu");
        if (menuInc == 1) {
          chandeadband[0]+=1;
        }
        else if (menuInc == -1){
          chandeadband[0]-=1;
        }
      } // deadband menu
      else if (menux == 3) { // chandelay menu
        Serial.println("chandelay menu");
        if (menuInc == 1) {
          chandelay[0]+=1000;
        }
        else if (menuInc == -1){
          chandelay[0]-=1000;
        }
      } // chan delay menu

      
      else if (menux == -1) { // enabled
        if (chanenabled[0]) {
          chanenabled[0]=0;
        }
        else { 
          chanenabled[0] = 1;
        }
      } // Enabled menu
      else if (menux == -2) { // temperature mode
        if (tempmode == 'F') {
          tempmode = 'C';
        }
        else { 
         tempmode = 'F';
        }
      } // temperature mode menu
      else if (menux == -3) { // led brightness
        if (menuInc == 1 && lcdbrightness < 15) {
          lcdbrightness++;
          lc.setIntensity(0,lcdbrightness);
        }
        else if (menuInc == -1 && lcdbrightness > 0) { 
          lcdbrightness--;
          lc.setIntensity(0,lcdbrightness);
        }
      } // Enabled menu
    } 
}
void doButton() {
//  No serial debug in interrupts
//  make sure we are not duplicating events.
  if (millis()-lastactivity > activityspacing){
    lastactivity = millis();
    if (menux == 0) {  // program entry menu
      if (menuy == 1){    // menu is not at root
        menuy = 0;
      }
      else {                   // menu is at root
        menuy = 1;
      }
    } // menux = 0
    else {
      if (menuy == 1) {
        menuy = 2;
      }
      else {
        menuy = 1;
        storeparams();
      }
    } // menux != 0
  } 
}
void printMenuInfo(){
  Serial.print("menux: ");
  Serial.print(menux);
  Serial.print(" menuy: ");
  Serial.println(menuy);
}
void handleBarDisplay(int period) {
  
  byte sendColors[12]={0,0,0,0,0,0,0,0,0,0,0,0};
  byte bardisplayon = 1;
  byte actchannel = 0;
  byte indcolor = 2;
  
  // Channel condition is second bit of chanstate
  // It describes comparison of setpoint to control value
  byte chancondition = chanstate[0] / 10;
  
  // Chanaction is first bit
  // It describes whether the control output has been activated
  byte chanaction = chanstate[0] % 10;
  
  // If they are not the same, an action is pending but not
  // yet enacted
  if (chanaction != chancondition) {
    barblinky = 1;
  }
  else {
    barblinky = 0;
  }
  
  if (barblinky) {
    byte blinkinterval = (millis()/200) % 2;
    if (!blinkinterval) {
      bardisplayon = 1;
//      Serial.println("bar on");
    }
    else {
      bardisplayon = 0;
//      Serial.println("bar off");
    }
  }
  if (chanenabled[actchannel] && bardisplayon){
    int err;
    if (tempmode == 'F'){
      err = (chanpv[actchannel]-chansv[actchannel])*1.8;
    }
    else {
      err = chanpv[actchannel]-chansv[actchannel];
    }
//    Serial.print("Err: ");
//    Serial.println(err);


    // if channel state is on, indicator is red
    if (chanaction > 0) {
      indcolor = 1;
    }
    else {
      indcolor = 2;
    }
    
    // Set bar locations based on error
    if (err == 0) {
      sendColors[5]=indcolor;
      sendColors[6]=indcolor;
    }
    else if (err < 7 && err > 0) {
      sendColors[5+err]=indcolor;
    }
    else if (err > 6) {
      sendColors[11] = 3;
    }
    else if (err > -7 && err < 0) {
      sendColors[6+err]=indcolor;
    }
    else if (err <-6){
      sendColors[0] = 3;
    }
    byte barColors[12]={sendColors[11],sendColors[10],sendColors[9],sendColors[8],sendColors[3],sendColors[2],sendColors[1],sendColors[0],sendColors[7],sendColors[6],sendColors[5],sendColors[4]};
//    byte barColors[12]={1,1,2,3,1,1,2,3,1,1,2,3};
    setBarDigits(barColors,period);
  } // display on
  else {
    // display off
//    Serial.println("Display Off");
    setBarDisplay(0,0);
  }
  
  

}
void handledisplay(){
  
//  Serial.println(millis()-lastactivity);
  byte displaymode = 0;
  byte char1;
  byte char2;
  byte char3;
  byte char4;
  unsigned long newlcdvalue;
  
  if (menuy > 1) {
    blinky = 1;
  }
  else {
    blinky = 0;
  }
  
  //  Serial.println(testvalue);
  if (blinky) {
    byte blinkinterval = (millis()/200) % 2;
    if (!blinkinterval) {
      displayon = 1;
    }
    else {
      displayon = 0;
    }
  }
  else {
    displayon = 1;
  }
  
  // menux == 0 is either temp display or entry into program mode
  if (menux == 0){ 
    if (menuy == 0){
      if (tempmode == 'F'){
        newlcdvalue = CtoF(chanpv[0]) * 100 + 20000; // dotpoint @2
      }
      else{
        newlcdvalue = chanpv[0] * 100 + 20000;
      }
    }
    else if (menuy == 1) { // entry into program mode
      displaymode = 1;  // display characters
      char1 = 'P';
      char2 = 'R';
      char3 = 'O';
      char4 = 'G';
      
      // this generates a unique value. We could use this to send the value later
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);    
    }
  }
  else if (menux == 1) { // Setpoint temperature
    if (menuy == 1) {
      displaymode = 1;  // display characters
      char1 = 'S';
      char2 = 'P';
      char3 = '-';
      char4 = '-';
      
      // this generates a unique value. We could use this to send the value later
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);    
    }
    else if (menuy == 2) {
      if (tempmode == 'F'){
        newlcdvalue = CtoF(chansv[0]) *100 + 20000;
      }
      else {
        newlcdvalue = chansv[0] *100 + 20000;
      }
    }
  }
  else if (menux == -1) { // enable/disable controller
    displaymode = 1;  // display characters
    if (menuy == 1) {
      char1 = 'E';
      char2 = 'N';
      char3 = 'B';
      char4 = 'L';
      
      // this generates a unique value. We could use this to send the value later
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);    
    }
    else if (menuy == 2) {
      if (chanenabled[0]){
        char1 = '-';
        char2 = '-';
        char3 = 'O';
        char4 = 'N';
      }
      else {
        char1 = '-';
        char2 = 'O';
        char3 = 'F';
        char4 = 'F';
      }
    }
  }
  else if (menux == -2) { // configure celsius/fahrenheit display
    displaymode = 1;  // display characters
    if (menuy == 1) {
      char1 = 'C';
      char2 = 'O';
      char3 = 'R';
      char4 = 'F';
    }
    else if (menuy ==2) {
      if (tempmode == 'F'){
        char1 = '-';
        char2 = '-';
        char3 = '-';
        char4 = 'F';
      }
      else {
        char1 = '-';
        char2 = '-';
        char3 = '-';
        char4 = 'C';
      }
    }    
    // this generates a unique value. We could use this to send the value later
    newlcdvalue = fourcharstovalue(char1, char2, char3, char4);
  }
  else if (menux == -3) { // configure celsius/fahrenheit display
    if (menuy == 1) {
      displaymode = 1;  // display characters
      char1 = 'B';
      char2 = 'R';
      char3 = 'I';
      char4 = 'T';
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);
    }
    else if (menuy ==2) {
      newlcdvalue = lcdbrightness; 
    }    
  }
  else if (menux == 2) { // channel deadband
    if (menuy == 1) {
      displaymode = 1;  // display characters
      char1 = 'D';
      char2 = 'B';
      char3 = 'N';
      char4 = 'D';
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);
    }
    else  if (menuy == 2){
      newlcdvalue = chandeadband[0] + 30000;
    }   
  }
  else if (menux == 3) { // delay (ms)
    if (menuy ==1) {
      displaymode = 1;  // display characters
      char1 = 'D';
      char2 = 'E';
      char3 = 'L';
      char4 = 'Y';
      newlcdvalue = fourcharstovalue(char1, char2, char3, char4);  
    }  
    else if (menuy == 2) {
      newlcdvalue = chandelay[0]/1000;
    }
  }
  
  if (displayon){
    if (newlcdvalue != lcdvalue) {
      lcdvalue = newlcdvalue;
      if (displaymode == 0){
        setdigits(newlcdvalue);
      }
      else if (displaymode == 1){
        setchars(char1,char2,char3,char4);
      }
    }
  }
  else {
    lc.clearDisplay(0);
    lcdvalue = -9999; // ensure refresh
  }
}
long fourcharstovalue(char char1, char char2, char char3, char char4){
  return chartoint(char1)*16777216 + chartoint(char2)*65536 + chartoint(char3)*16 + chartoint(char4);
}
float CtoF(float celsius){
  float fahrenheit = celsius*1.8 + 32;
  return fahrenheit;
}
void setchars(char char1, char char2, char char3, char char4){
  lc.clearDisplay(0);
  lc.setRow(0,0,chartoint(char1));
  lc.setRow(0,1,chartoint(char2));
  lc.setRow(0,2,chartoint(char3));
  lc.setRow(0,3,chartoint(char4));
}
byte chartoint(char mychar){
  byte charbyte = 62;
  switch (mychar) {
    case '-':
      charbyte = 0;
      break;    
    case 'B':
      charbyte = 31;
      break;
    case 'C':
      charbyte = 78;
      break;
    case 'D':
      charbyte = 61;
      break;
    case 'E':
      charbyte = 79;
      break;
    case 'F':
      charbyte = 71;
      break;
    case 'G':
      charbyte = 123;
      break;
    case 'I':
      charbyte = 48;
      break;
    case 'L':
      charbyte = 14;
      break;
    case 'N':
      charbyte = 21;
      break;
    case 'O':
      charbyte = 126;
      break;
    case 'P':
      charbyte = 103;
      break;
    case 'R':
      charbyte = 5;
      break;
    case 'S':
      charbyte = 91;
      break;
    case 'T':
      charbyte = 15;
      break;
    case 'V':
      charbyte = 62;
      break;
    case 'Y':
      charbyte = 59;
      break;
    
    

  }
  return charbyte;
}
void setdigits(long lcdvalue) {
  
  // we now pass this in as an integer so we can set resolution externally
  // we'll also pass format codes into this integer.
  // long range is +/-2147483648
  
  // ?XXXXYDDDD
  // ? - determines whether digits are manually or automatically set.
  //     0 is auto. 1 is manual
  // XXXX - when ? is set to 1, values of 0 or 1 determine whether the digit
  //     is displayed or not
  // Y is where to put the dot. 0 is no dot.
  // DDDD - four-digit display value
  
  // by default, only digits for values to the right of leftmost significant digit
  // will be shown.
  
  // default will fill left with spaces
  
  
  int manualdisplay = lcdvalue / 1000000000;
  lcdvalue = lcdvalue % 1000000000;
  
  int displaydigits = lcdvalue / 100000;
  lcdvalue = lcdvalue % 100000;
  
  byte dotposition = lcdvalue / 10000;
  lcdvalue = lcdvalue % 10000;
  
  byte showdig1 = 0;
  byte showdig2 = 0;
  byte showdig3 = 0;
  byte showdig4 = 0;
  if (manualdisplay) {
    showdig1 = displaydigits / 1000;
    displaydigits = displaydigits % 1000;
    showdig2 = displaydigits / 100;
    displaydigits = displaydigits % 100;
    showdig3 = displaydigits / 10;
    showdig4 = displaydigits % 10;
  }
  else {
    showdig1 = 0;
    showdig2 = 0;
    showdig3 = 0;
    showdig4 = 0;
  }
  
  byte dot4 = dotposition / 4;
  dotposition = dotposition % 4;
  byte dot3 = dotposition / 3;
  dotposition = dotposition % 3;
  byte dot2 = dotposition / 2;
  dotposition = dotposition % 2;
  byte dot1 = dotposition;
  
  int dig1 = lcdvalue / 1000;
  if ((dig1 > 0 || dot1 ) && !manualdisplay) {
    showdig1 = 1;
    showdig2 = 1;
    showdig3 = 1;
    showdig4 = 1;
  }
  int leftovers = lcdvalue - (dig1 * 1000);
  int dig2 = leftovers / 100;
  if ((dig2 > 0 || dot2) && !manualdisplay) {
    showdig2 = 1;
    showdig3 = 1;
    showdig4 = 1;
  }
  leftovers -= dig2 * 100;
  int dig3 = leftovers / 10;
  if ((dig3 > 0 || dot3) && !manualdisplay) {
    showdig3 = 1;
    showdig4 = 1;
  }
  leftovers -= dig3 * 10;
  int dig4 = leftovers;
  if (!manualdisplay) {
    showdig4 = 1;
  }
    
  if (lcdvalue < 0) {
    
    // display value
    lc.clearDisplay(0);
      
    // this should work for the negative sign
    lc.setRow(0,0,dot1);
    lc.setDigit(0,1,dig2,dot2);
    lc.setDigit(0,2,dig3,dot3);
    lc.setDigit(0,3,dig4,dot4);
  }
  else {
    // display value
    lc.clearDisplay(0);
    if (showdig1){
      lc.setDigit(0,0,dig1,dot1); 
    }
    if (showdig2){
      lc.setDigit(0,1,dig2,dot2);
    }
    if (showdig3){
      lc.setDigit(0,2,dig3,dot3);
    }
    if (showdig4){
      lc.setDigit(0,3,dig4,dot4);
    }
  }
}

void processcmdstring(String cmdstring){
  Serial.print(F("Free memory: "));
  Serial.println(freeRam());
  
  Serial.println(F("processing cmdstring"));
  Serial.println(cmdstring);
  
  char buff[61];
  int i;
  String str1="";
//  str1.reserve(10);
  String str2="";
//  str2.reserve(10);
  String str3="";
//  str3.reserve(10);
  String str4="";
//  str4.reserve(10);
  
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
        long newvalue = str3.toInt();
        if (newvalue >= 0 && newvalue < 600000){
          Serial.print(F("Modifying loopperiod to "));
          Serial.println(newvalue);
          // deliver in seconds, translate to ms
          LOOPPERIOD = newvalue;
          storeparams();
        }
        else {
          Serial.println(F("Value out of range"));
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
          Serial.println(F("Value out of range"));
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
          Serial.println(F("Value out of range"));
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
          Serial.println(F("Value out of range"));
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
          Serial.println(F("Value out of range"));
        }
      } // network
      else if (str2 == "iomode") {
        int ionumber = str3.toInt();
        if (ionumber >=0 && ionumber <numio+1) {
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
        if (ionumber >=0 && ionumber <numio+1) {
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
      else if (str2 == "ioreadfreq") { // Entered in 100ms
        Serial.print(str3);
        int ionumber = str3.toInt();
        Serial.println(ionumber);
        if (ionumber >=0 && ionumber <numio+1) {
          Serial.print(F("Modifying io: "));
          Serial.println(ionumber);
          long newvalue = str4.toInt()*100;
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
        if (ionumber >=0 && ionumber <numio+1) {
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
        if (ionumber >=0 && ionumber <numio+1) {
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
        if (ionumber >=0 && ionumber <numio+1) {
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
          if (newvalue >=0 and newvalue <numio){     
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
          if (newvalue >=0 and newvalue <numio){     
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
          if (newvalue >=0 and newvalue <numio){     
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
      else if (str2 == "chandeadband") { // tenths
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue >=0 and newvalue <50){     
            Serial.print(F("Changing deadband to "));
            Serial.println(newvalue);
            chandeadband[channumber]=newvalue;
            storeparams();
          }
          else {
            Serial.println(F("deadband out of range"));
          }
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// chandeadband
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
    else if (str1 == "sendiovals"){
      Serial.println(F("Sending iovals"));
//      sendiovals();
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
      Serial.println(F("Flash content:"));
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
   Serial.print(F("Free memory: "));
  Serial.println(freeRam());
}
void sendWithSerialNotify(byte destination, char* sendstring, byte sendlength) {
  Serial.print(F("SENDING TO "));
  Serial.println(destination);
  Serial.println(sendstring);
  radio.sendWithRetry(destination, sendstring, sendlength);
  Serial.println(F("SEND COMPLETE"));  
}
void initparams() {
    NODEID = 7;
    NETWORKID  = 100;
    GATEWAYID = 1;
    LOOPPERIOD = 100;
    SLEEPMODE = 0;
    SLEEPDELAY = 1000;
    storeparams();
    int i;
    for (i=0;i<numio;i++){
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
//    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
//    radio.setAddress(NODEID);
    
  // maximum initialized loop period is 256
  if (LOOPPERIOD/1000 > 256){
    EEPROM.write(58,256);
  }
  else {
    EEPROM.write(94,LOOPPERIOD/1000);
  }
  
  EEPROM.write(95,SLEEPMODE);
  EEPROM.write(96,SLEEPDELAY);
  
  int i;
  for (i=0;i<16;i++) {
//      EEPROM.write(i+3,ENCRYPTKEY[i]);
  }
  byte mybyte;
  for (i=0;i<numio;i++){    
    EEPROM.write(i+19,iomode[i]);
    EEPROM.write(i+19+numio,ioenabled[i]);
    if (ioreadfreq[i]/1000 > 256){
      EEPROM.write(i+ 19+numio+numio,256);
    }
    else {
      mybyte = ioreadfreq[i] / 1000;
      EEPROM.write(i+19+numio+numio,mybyte);
    }
  } // for num io
  
  // channels data
  byte offset = 97;
  byte numchannels = 8;
  for (i=0;i<numchannels;i++) {
    EEPROM.write(i+offset,chanenabled[i]);
    EEPROM.write(i+offset+numchannels,chanmode[i]);
    EEPROM.write(i+offset+2*numchannels,chanposfdbk[i]);
    EEPROM.write(i+offset+3*numchannels,channegfdbk[i]);
    EEPROM.write(i+offset+4*numchannels,chandeadband[i]);
    EEPROM.write(i+offset+5*numchannels,chanpvindex[i]);
    EEPROM.write(i+offset+6*numchannels,chansv[i]);
  } // for channels
}
void getparams() {

    NODEID = EEPROM.read(0);
    NETWORKID = EEPROM.read(1);
    GATEWAYID = EEPROM.read(2);    
    
    // update object
    // we now get these prior to initialization of radio.
    // this means we'll have to refresh manually if set during runtime.
    
//    radio.writeReg(REG_SYNCVALUE2, NETWORKID);
//    radio.setAddress(NODEID);
    
    LOOPPERIOD = EEPROM.read(94) * 1000;
    SLEEPMODE = EEPROM.read(95);
    SLEEPDELAY = EEPROM.read(96);
 
    // io
    int i;
    for (i=0;i<numio;i++){
      iomode[i] = EEPROM.read(i+19);
      ioenabled[i] = EEPROM.read(i+19+numio);
      ioreadfreq[i] = EEPROM.read(i+19+numio+numio)*1000;      
    } // for io 
    
    //channels
    byte numchannels = 8;
    byte offset = 97;
    for (i=0;i<numchannels;i++) {
      chanenabled[i] = EEPROM.read(i+offset);
      chanmode[i] = EEPROM.read(i+offset + numchannels);
      chanposfdbk[i] = EEPROM.read(i+offset + 2*numchannels);
      channegfdbk[i] = EEPROM.read(i+offset + 3*numchannels);
      chandeadband[i] = EEPROM.read(i+offset + 4*numchannels);
      chanpvindex[i] = EEPROM.read(i+offset + 5*numchannels);
      chansv[i] = EEPROM.read(i + offset + 6*numchannels);
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
    for (i=0;i<numio;i++) {
      Serial.print(iomode[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioenabled:["));
    for (i=0;i<numio;i++) {
      Serial.print(ioenabled[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("iovalue:["));
    for (i=0;i<numio;i++) {
      Serial.print(iovalue[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreadfreq:["));
    for (i=0;i<numio;i++) {
      Serial.print(ioreadfreq[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreadtimer:["));
    for (i=0;i<numio;i++) {
      Serial.print(ioreadtimer[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreportenabled:["));
    for (i=0;i<numio;i++) {
      Serial.print(ioreportenabled[i]);
      if (i<numio-1){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("ioreportfreq:["));
    for (i=0;i<numio;i++) {
      Serial.print(ioreportfreq[i]);
      if (i<numio-1){
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
    Serial.println(F("],"));
    Serial.print(F("chanpv:["));
    for (i=0;i<8;i++) {
      Serial.print(chanpv[i]);
      if (i<7){
        Serial.print(F(","));
      }
    }
    Serial.println(F("],"));
    Serial.print(F("chanstate:["));
    for (i=0;i<8;i++) {
      Serial.print(chanstate[i]);
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
void handleOWIO(byte ioindex) {
  owpin = iopins[ioindex];
  
  // Device identifier
  byte dsaddr[8];
//  char dscharaddr[16];
//  Serial.print("creating ds with pin: ");
//  Serial.println(owpin);
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
//  sprintf(dscharaddr,"%02x%02x%02x%02x%02x%02x%02x%02x",dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]);
//  Serial.println(',');
    Serial.println();
  
  // Data
  Serial.print(F("temperature:"));
  iovalue[ioindex] = dsreadtemp(myds, dsaddr);
  Serial.println(iovalue[ioindex]);
  
  if ((ioreportenabled[ioindex]) && (ioreportfreq[ioindex] == 0)){
    byte sendlength = 54;
    char sendstring[sendlength];
    
    int wholePart = iovalue[ioindex];
    long fractPart = (iovalue[ioindex] - wholePart) * 10000;
    sprintf(sendstring, "owtmpasc:%03d.%04d,owdev:ds18x,owrom:%0xx%02x%02x%02x%02x%02x%02x%02x%02x", wholePart, fractPart, dsaddr[0],dsaddr[1],dsaddr[2],dsaddr[3],dsaddr[4],dsaddr[5],dsaddr[6],dsaddr[7]); 
    sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
    
    sendIOMessage(iopins[ioindex], iomode[ioindex], iovalue[ioindex]);
  } // reportenabled and ioreportfreq
} // run OW sequence

void getfirstdsadd(OneWire myds, byte firstadd[]){
  byte i;
  byte present = 0;
  byte addr[8];
  float celsius, fahrenheit;
  
  int length = 8;
  
//  Serial.print("Looking for 1-Wire devices...\n\r");
  while(myds.search(addr)) {
//    Serial.print("\n\rFound \'1-Wire\' device with address:\n\r");
    for( i = 0; i < 8; i++) {
      firstadd[i]=addr[i];
//      Serial.print("0x");
      if (addr[i] < 16) {
//        Serial.print('0');
      }
      //Serial.print(addr[i], HEX);
      if (i < 7) {
//        Serial.print(", ");
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

int dsconvertfromioindex(byte ioindex){
  owpin = iopins[ioindex];
  byte dsaddr[8];
  int waittime;
  OneWire myds(owpin);
  getfirstdsadd(myds,dsaddr);
  dssetresolution(myds,dsaddr,OWRES);
  dsconvertcommand(myds,dsaddr);
//  for (int i=0; i<70;i++){
//    checkstatus(myds);
//    delay(10);
//  }
//  checkstatus(myds,dsaddr);
  switch (OWRES) {
    case 9:
      waittime = 100;
      break;
    case 10:
      waittime = 200;
      break;
    case 11:
      waittime = 400;
      break;
    case 12:
      waittime = 1000;
      break;
  }
   return waittime;
}
byte checkifdsreadyfromioindex(byte ioindex){
  byte dsaddr[8];
  owpin = iopins[ioindex];
  OneWire myds(owpin);
  getfirstdsadd(myds,dsaddr);
  checkstatus(myds,dsaddr);
}
byte checkstatus(OneWire theds, byte addr[8]){
  byte status = 0;
 
  if (theds.read()) {
    status = 1;
    Serial.println(F("IS READY"));
  }
  else {
    Serial.println(F("NOT READY"));
  }
  return status;
}
  // this just reads the scratchpad
float dsreadtemp(OneWire myds, byte addr[8]) {
  byte present = 0;
  int i;
  byte data[12];
  byte type_s;
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
//    default:
//      Serial.println(F("Device is not a DS18x20 family device."));
//  } 

  type_s = 0;
  
  present = myds.reset();
  myds.select(addr);    
  myds.write(0xBE);         // Read Scratchpad

  //Serial.print("  Data = ");
  //Serial.print(present,HEX);
//  Serial.println("Raw Scratchpad Data: ");
  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = myds.read();
//      Serial.print(data[i], HEX);
//    Serial.print(" ");
  }
  //Serial.print(" CRC=");
  //Serial.print(OneWire::crc8(data, 8), HEX);
//  Serial.println();

  // convert the data to actual temperature
  
  int TReading = (data[1] << 8) + data[0];
  int SignBit = TReading & 0x8000;  // test most sig bit
  if (SignBit) // negative
  {
    TReading = (TReading ^ 0xffff) + 1; // 2's comp
  }
  celsius = float(TReading)/16;
  
  if (SignBit){
    celsius = celsius * -1;
  }
  
//  Serial.print(F("Temp (C): "));
//  Serial.println(celsius);
  return celsius;
}

void dssetresolution(OneWire myds, byte addr[8], byte resolution) {
    
  // Get byte for desired resolution
  byte resbyte = 0x1F;
  if (resolution == 12){
    resbyte = 0x7F;
  }
  else if (resolution == 11) {
    resbyte = 0x5F;
  }
  else if (resolution == 10) {
    resbyte = 0x3F;
  }
  
  // Set configuration
  myds.reset();
  myds.select(addr);
  myds.write(0x4E);         // Write scratchpad
  myds.write(0);            // TL
  myds.write(0);            // TH
  myds.write(resbyte);         // Configuration Register
  
  myds.write(0x48);         // Copy Scratchpad
}
void dsconvertcommand(OneWire myds, byte addr[8]){
  myds.reset();
  myds.select(addr);
  myds.write(0x44,1);         // start conversion, with parasite power on at the end
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
  char buff[61];
  sprintf(buff, "\nTransmitting at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
  sprintf(buff, "I am node id: %d",NODEID);
  Serial.println(buff);
}
void sendIOMessage(byte pin, byte mode, float value) {
  // Initialize send string
//  char sendstring[61];
  int sendlength = 61;  // default
  if (mode == 0 || mode == 1 ) { // for integer values
    sendlength = 32;
    char sendstring[sendlength];
    sprintf(sendstring, "iopin:%02d,iomode:%02d,iovalue:%04d", pin, mode, value);         
    sendWithSerialNotify(GATEWAYID, sendstring, sendlength);
  }
  else if (mode == 2){ // for float values
    // nothing here yet
    int wholePart = value;
    long fractPart = (value - wholePart) * 10000;
    sendlength = 34; 
    char sendstring[sendlength];
    sprintf(sendstring, "iopin:%02d,iomode:%02d,ioval:%03d.%04d", pin,mode,wholePart, fractPart);

    sendWithSerialNotify(GATEWAYID, sendstring, sendlength); 
  }
}
void setBarDigits(byte barColors[], int runtime) {
  int i;
  int byte21 = 0;
  int byte22 = 0;
  int byte23 = 0;
  long starttime = millis();
  boolean doRun = true;
  
  // We are going to catch zero values for byte sets and only set them once. 
  // This will leave the bar display in the last state before the routine is 
  // exited, meaning if we have to wait until it's run again and there is only 
  // one anode active, we will leave it in that state.
  
  while (doRun){
    byte21 = 0;
    byte22 = 0;
    byte23 = 0;
    for (i=0;i<4;i++) {
      byte21 += getByteFromColorInt(i, barColors[i]);
    }
//    Serial.print("byte21: ");
//    Serial.println(byte21); 
    if (byte21 > 0 || i == 0) {
      setBarDisplay(byte21,1);
    }
    for (i=4;i<8;i++){
      byte22 += getByteFromColorInt(i%4, barColors[i]);
    }
//    Serial.print("byte22: ");
//    Serial.println(byte22);
    if (byte22 > 0 || i == 0) {
      setBarDisplay(byte22,2);
    }
    for (i=8;i<12;i++){
      byte23 += getByteFromColorInt(i%4, barColors[i]);
    } 
//    Serial.print("byte23: ");
//    Serial.println(byte23);
    if (byte23 > 0 || i == 0) {
      setBarDisplay(byte23,4);
    }
    
    if (millis()-starttime < runtime) {
      doRun = true;
    }
    else {
      doRun = false;
    }
    i++;
  }
}
int getByteFromColorInt(int digit, int colorint){
  int returnvalue=0;
  if (colorint > 0){
    if (colorint == 1){
      returnvalue = bit(digit);
    }
    else if (colorint == 2){
      returnvalue = bit(digit + 4);
    }
    else if (colorint == 3){
      returnvalue = bit(digit) + bit(digit +4);
    }    
  }
  return returnvalue;
}
void setBarDisplay(int byte1, int byte2) {
  int numtoset1 = 255-byte1;
  int numtoset2 = byte2;
  digitalWrite(barlatchPin, LOW);
  
    // shift out the bits:
    shiftOut(bardataPin, barclockPin, MSBFIRST, numtoset2);
    shiftOut(bardataPin, barclockPin, MSBFIRST, numtoset1);  

    //take the latch pin high so the LEDs will light up:
    digitalWrite(barlatchPin, HIGH);
  
}
