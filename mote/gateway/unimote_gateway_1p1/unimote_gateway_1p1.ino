
// Sample RFM69 receiver/gateway sketch, with ACK and optional encryption
// Passes through any wireless received messages to the serial port & responds to ACKs
// It also looks for an onboard FLASH chip, if present
// Library and code by Felix Rusu - felix@lowpowerlab.com
// Get the RFM69 and SPIFlash library at: https://github.com/LowPowerLab/

#include <RFM69.h>
#include <RFM69registers.h>
#include <SPI.h>
#include <SPIFlash.h>
#include <EEPROM.h>

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY RF69_433MHZ
//#define FREQUENCY RF69_868MHZ
//#define FREQUENCY RF69_915MHZ
#define ENCRYPTKEY "sampleEncryptKey" //exactly the same 16 characters/bytes on all nodes!
#define IS_RFM69HW //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define ACK_TIME 30 // max # of ms to wait for an ack
#define LED 9 // Moteinos have LEDs on D9
#define SERIAL_BAUD 115200

int DEBUG = 1;
byte NODEID = 1;
byte NETWORKID = 100;
byte GATEWAYID = 1;
byte SLEEPMODE = 0;
char buff[20];

int LOOPPERIOD = 50;

RFM69 radio;
SPIFlash flash(8, 0xEF30); //EF40 for 16mbit windbond chip
bool promiscuousMode = false; //set to 'true' to sniff all packets on the same network

// constants
//PROGMEM char ionames[13][3] = { "D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","A7" };
int iopins[13] = { 3,4,5,6,7,A0,A1,A2,A3,A4,A5,A6,A7 };
int owpin;

// user-assigned variables
byte ioenabled[13];
int iomode[13];
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
  delay(10);
  char buff[50];
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
#ifdef IS_RFM69HW
  radio.setHighPower(); //uncomment only for RFM69HW!
#endif
  radio.encrypt(ENCRYPTKEY);
  radio.promiscuous(promiscuousMode);

  sprintf(buff, "\nListening at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
  sprintf(buff, "I am node id: %d",NODEID);
  Serial.println(buff);
  if (flash.initialize())
  {
    Serial.println(F("SPI Flash Init OK"));
    Serial.println(F("UniqueID (MAC): "));
    flash.readUniqueId();
    for (byte i=0;i<8;i++)
    {
      Serial.print(flash.UNIQUEID[i], HEX);
      Serial.print(' ');
    }
    Serial.println();
  }
  else
    Serial.println("SPI Flash Init FAIL! (is chip present?)");
  }

byte ackCount=0;
void loop() {

  if (Serial.available() > 0)
  {
    if (DEBUG) {
      Serial.println("reading characters");
    }
    String cmdstring =Serial.readStringUntil('\n');
    if (DEBUG) {
      Serial.println("Serial cmd buffer is: ");
      Serial.println(cmdstring);
      Serial.println("Of length");
      Serial.println(cmdstring.length());
    }
    processcmdstring(cmdstring); 
  }// comnand sequence
  if (radio.receiveDone())
  {
    Serial.println(F("BEGIN RECEIVED"));
    Serial.print("nodeid:");Serial.print(radio.SENDERID, DEC);Serial.print(", ");
    if (promiscuousMode)
    {
      Serial.print("to [");Serial.print(radio.TARGETID, DEC);Serial.print("] ");
    }
    for (byte i = 0; i < radio.DATALEN; i++)
      Serial.print((char)radio.DATA[i]);
      Serial.print(",RX_RSSI:");Serial.print(radio.RSSI);Serial.print("");
      Serial.println();
      Serial.println(F("END RECEIVED"));
    if (radio.ACK_REQUESTED)
    {
      byte theNodeID = radio.SENDERID;
      radio.sendACK();
      Serial.print(" - ACK sent.");

      // When a node requests an ACK, respond to the ACK
      // and also send a packet requesting an ACK (every 3rd one only)
      // This way both TX/RX NODE functions are tested on 1 end at the GATEWAY
      if (ackCount++%3==0)
      {
        Serial.print(" Pinging node ");
        Serial.print(theNodeID);
        Serial.print(" - ACK...");
        delay(3); //need this when sending right after reception .. ?
        if (radio.sendWithRetry(theNodeID, "ACK TEST", 8, 0)) // 0 = only 1 attempt, no retries
          Serial.print("ok!");
        else Serial.print("nothing");
      }
     } // Ack requested
     Serial.println();
     Blink(LED,3);
  } // Receive done
}// loop

void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
void parseargs(String args, String *option, String *optionvalue)
{
   // parse arguments
  boolean readoption = false;
  boolean readoptionvalue = false;
  char readchar;
  args.trim();
  for (int i=0; i<args.length(); i++)
  {
    readchar = args.charAt(i);
    if (readoption)
    {
      *option += readchar;
    }
    else if (readoptionvalue)
    {
      *optionvalue += readchar;
    }
    if (readchar == '-')
    {
      readoption = true;
    }
    else if (readchar == ' ')
    {
      readoptionvalue = true;
      readoption = false;
    }            
  }
}
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
    else if (str1 == "modparam") {
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
      if (str2 == "nodeid") {
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
      if (str2 == "networkid") {
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
      if (str2 == "gatewayid") {
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
        int ionumber = str3.toInt();
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
          Serial.print(F("Value out of range: "));
            Serial.println(newvalue);
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
          Serial.print(F("Changing sv to"));
          Serial.println(newvalue);
          chansv[channumber]=newvalue;
          storeparams();
        }
        else {
          Serial.println(F("chan number out of range"));
        }
      }// chansv
      else if (str2 == "chanenabled") {
        int channumber = str3.toInt();
        if (channumber >=0 && channumber <=8) {
          Serial.print(F("Modifying channel: "));
          Serial.println(channumber);
          int newvalue = str4.toInt();
          if (newvalue == 0) {
            Serial.print(F("Disabling channel."));
            chanenabled[channumber] = 0;
            storeparams();
          }
          else if (newvalue == 1) {
            Serial.print(F("Enabling channel."));
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

      Serial.print("0-256: ");
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
void initparams() {
    NODEID = 1;
    NETWORKID  = 100;
    GATEWAYID = 1;
    LOOPPERIOD = 50;
    SLEEPMODE = 0;
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

