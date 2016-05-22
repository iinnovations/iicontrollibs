#define DEBUG 1
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
#include <SPIFlash.h>
//#include <LedControl.h>

//Match frequency to the hardware version of the radio on your Moteino (uncomment one):
#define FREQUENCY   RF69_433MHZ
//#define FREQUENCY   RF69_868MHZ
//#define FREQUENCY     RF69_915MHZ
#define IS_RFM69HW    //uncomment only for RFM69HW! Leave out if you have RFM69W!
#define REG_SYNCVALUE2 0x30

// Radio stuff
byte NODEID = 2;
byte NETWORKID = 1;
byte GATEWAYID = 1;
#define serialrfecho 1
#define RETRIES 2
#define ACK_TIME 300
#define ENCRYPTKEY    "sampleEncryptKey"

///////////////////////////////////////////////////////////
// Software Serial Stuff

#include <SoftwareSerial.h>
// Gateway is 16 RX, 15 RX, 17 RTS
// Mote is 14,15,16
SoftwareSerial mySerial(15, 16, 0); // RX, TX
#define LED           9 // Moteinos have LEDs on D9
#define SENDLED    18
#define FLASH_SS  8
  
char buff[61];
int i = 0;
int cmdlength;
uint8_t mbstate;
byte RTSPIN = 17;
int xmitdelay = 0;
unsigned long rxstart;
unsigned long rxwait = 1000;
float sv;
float pv;
byte rtuaddress=0;

// message : node, FC, register start high byte, low byte, number of registers high byte, low byte, CRC, CRC
byte pvsvmessage[] = {0x01, 0x03, 0x47, 0x00, 0x00, 0x02, 0x00, 0x00 };
byte outputmessage[] = {0x01, 0x03, 0x47, 0x14, 0x00, 0x02, 0x00, 0x00 };
byte modemessage[] = {0x01, 0x03, 0x47, 0x18, 0x00, 0x02, 0x00, 0x00 };

// for set message, same except two bytes for number of registers are replaced by the data to program into 
// the target register
byte setmessage[] = {0x01, 0x06, 0x47, 0x01, 0x04, 0x4C, 0x00, 0x00 };

byte nummessages = 3;

byte message[] = {0x01, 0x03, 0x47, 0x18, 0x00, 0x02, 0x00, 0x00 };

byte mbmessagetype = 0;

long mycrc;
byte rtuaddresses[] = {1,2,3};
byte rtuindex;

boolean requestACK = false;
SPIFlash flash(FLASH_SS, 0xEF30); //EF30 for 4mbit  Windbond chip (W25X40CL);
RFM69 radio;


void setup() {
  Serial.begin(115200);
  mbstate = 0;
  rtuindex = 0;
  addcrc(pvsvmessage,6);
  addcrc(outputmessage,6);
  addcrc(modemessage,6);
  addcrc(setmessage,6);
  
  mySerial.begin(9600);
  if (DEBUG) {
    Serial.println("DEBUG IS ON");
  }

  
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
 
  radio.encrypt(ENCRYPTKEY);
  //sendInitMessage();
  
}

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
  
// radio send/receive stuff
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
      //processcmdstring(buff, cmdlength, replynode);
    }

    // Reset sleepdelay timer
    //millistart = millis();
  } // Radio Receive
  // END RADIO RECEIVE
    
    
  // serial master stuff
  switch ( mbstate ) {
  case 0: // This is the transmit stage
    message[0] = rtuaddresses[rtuindex];
    for (byte i=1; i<6; i++) {
      switch (mbmessagetype) {
        case 0:
          message[i] = pvsvmessage[i];
          break;
        case 1:
          message[i] = outputmessage[i];
          break;
        case 2:
          message[i] = modemessage[i];
          break;  
        case 3:
          message[i] = setmessage[i];
          break;  
      }
    }
    
    addcrc(message,6);
     
    if (DEBUG) {
      Serial.print("MESSAGETYPE: ");
      Serial.println(mbmessagetype);
      Serial.print("sending to controller: ");
      Serial.println(rtuaddresses[rtuindex]);
      Serial.print(message[0],HEX);
      Serial.print(" ");
      Serial.print(message[1],HEX);
      Serial.print(" ");
      Serial.print(message[2],HEX);
      Serial.print(" ");
      Serial.print(message[3],HEX);
      Serial.print(" ");
      Serial.print(message[4],HEX);
      Serial.print(" ");
      Serial.print(message[5],HEX);
      Serial.print(" ");
      Serial.print(message[6],HEX);
      Serial.print(" ");
      Serial.println(message[7],HEX);
    }
    
    pinMode(RTSPIN, OUTPUT);
    digitalWrite(RTSPIN,HIGH);
    delay(xmitdelay);

    mySerial.write(message, sizeof(message));

    delay(xmitdelay);
    digitalWrite(RTSPIN,LOW);
    mbstate = 1;
    rxstart = millis();
    break; 
  case 1:  // wait for response
//    Serial.println("Waiting");
    if (mySerial.available() > 0)
    {
      Blink(LED,5);
      cmdlength = mySerial.readBytes(buff, 60);
      if (DEBUG) {
        Serial.print("Received message of length ");
        Serial.println(cmdlength);

        for (i=0; i<cmdlength;i++){
          Serial.print(buff[i], HEX);
          Serial.print(" ");
        }
        Serial.println();
      }
      
      if (buff[1]==3) {
        if (mbmessagetype == 0){
          pv = (float(buff[3] & 255) * 256 + float(buff[4] & 255))/10;
          sv = (float(buff[5] & 255) * 256 + float(buff[6] & 255))/10;
          if (DEBUG) {
            Serial.println("values");
    //        Serial.println((int(buff[3]&255))*256, DEC);
    //        Serial.println(buff[4]&255, DEC);
    //        Serial.println(int(buff[5]&255)*256, DEC);
    //        Serial.println(buff[6]&255, DEC);
 
            Serial.print("nodeid:");
            Serial.print(NODEID);
            Serial.print(",controller:");  
            Serial.print(rtuindex);
            Serial.print(",pv:");  
            Serial.print(pv);
            Serial.print(",sv:");
            Serial.println(sv);
          }
        }
        else if (mbmessagetype == 1) {
          pv = (float(buff[3] & 255) * 256 + float(buff[4] & 255));
          sv = (float(buff[5] & 255) * 256 + float(buff[6] & 255));
          if (DEBUG) {
            Serial.print("Proportional offset: ");
            Serial.println(pv);
            Serial.print("Regulation value");
            Serial.println(sv);
          }
        }
        else if (mbmessagetype == 2) {
          pv = (float(buff[3] & 255) * 256 + float(buff[4] & 255));
          sv = (float(buff[5] & 255) * 256 + float(buff[6] & 255));
          if (DEBUG) {
              Serial.print("Heating/cooling");
              Serial.println(pv);
              Serial.print("Run/Stop");
              Serial.println(sv);
          }
        }
        Blink(SENDLED,5);
        sendControllerMessage(rtuaddresses[rtuindex], pv, sv, mbmessagetype);
      }
      else if (buff[1]==6) {
        
        sv = (float(buff[4] & 255) * 256 + float(buff[5] & 255))/10;
        if (DEBUG) {
            
            Serial.print("Command acknowledged for node:");
            Serial.println(buff[0]);
            Serial.print("Setpoint: ");
            Serial.println(sv);
        }
        sendCmdResponseMessage(buff[0], sv);
      }
      else {
        if (DEBUG) {
          Serial.println("bad response");
        }
      }
    } 
    
    if (millis() - rxstart > rxwait) {
      if (mbmessagetype >= (nummessages - 1)) {
        mbmessagetype = 0;
        if (rtuindex >= sizeof(rtuaddresses)-1) {
          rtuindex = 0;
        }
        else {
          rtuindex ++;
        }
      }
      else {
        mbmessagetype ++;
        
      }
      mbstate=0;
    }
    break;
  } // switch

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
void sendCmdResponseMessage(byte controller, float sv) {
    // Initialize send string

  int sendlength = 61;  // default
  //int wholesv = sv;
  int wholesv = sv;
  long fractsv = ((long)(sv*1000))%1000;
  
  //Serial.println(wholesv);
  //Serial.println(fractsv);
  
  if (NODEID == 1) {
    sendlength = 31; 
    sprintf(buff, "nodeid:1,chan:%02d,svcmd:%03d.%03d", controller, wholesv, fractsv);
    Serial.println(buff);
  }
  else {
    sendlength = 23; 
    sprintf(buff, "chan:%02d,svcmd:%03d.%03d", controller, wholesv, fractsv);
    sendWithSerialNotify(GATEWAYID, buff, sendlength, 1); 
  }
}
void sendControllerMessage(byte controller, float pv, float sv, byte messagetype) {
  
  // Initialize send string

  int sendlength = 61;  // default
  int wholepv = pv;
  int fractpv = (pv - wholepv) * 1000;
  int wholesv = sv;
  int fractsv = (sv - wholesv) * 1000;
  
  if (messagetype == 0) {
    if (NODEID == 1) {
      sendlength = 39; 
      sprintf(buff, "nodeid:1,chan:%02d,sv:%03d.%03d,pv:%03d.%03d", controller, wholesv, fractsv, wholepv, fractpv);
      Serial.println(buff);
    }
    else {
      sendlength = 30; 
      sprintf(buff, "chan:%02d,sv:%03d.%03d,pv:%03d.%03d", controller, wholesv, fractsv, wholepv, fractpv);
      sendWithSerialNotify(GATEWAYID, buff, sendlength, 1); 
    }
  }
  else if (messagetype == 1) {
    if (NODEID == 1) {
      sendlength = 37; 
      sprintf(buff, "nodeid:1,chan:%02d,prop:%03d,treg:%03d.%01d", controller,wholepv, wholesv, fractpv);
      Serial.println(buff);
    }
    else {
      sendlength = 28; 
      sprintf(buff, "chan:%02d,prop:%03d,treg:%03d.%01d", controller,wholepv, wholesv, fractsv);
      sendWithSerialNotify(GATEWAYID, buff, sendlength, 1); 
    }
  }
  else if (messagetype == 2) {
    if (NODEID == 1) {
      sendlength = 31; 
      sprintf(buff, "nodeid:1,chan:%02d,htcool:%01d,run:%01d", controller,wholepv,wholesv);
      Serial.println(buff);
    }
    else {
      sendlength = 22; 
      sprintf(buff, "chan:%02d,htcool:%01d,run:%01d", controller,wholepv, wholesv);
      sendWithSerialNotify(GATEWAYID, buff, sendlength, 1); 
    }
  }
}

void Blink(byte PIN, int DELAY_MS)
{
  pinMode(PIN, OUTPUT);
  digitalWrite(PIN,HIGH);
  delay(DELAY_MS);
  digitalWrite(PIN,LOW);
}
// Compute the MODBUS RTU CRC
unsigned int ModRTU_CRC(byte* buf, int len)
{
  unsigned int crc = 0xFFFF;
 
  for (int pos = 0; pos < len; pos++) {
    crc ^= (unsigned int)buf[pos];          // XOR byte into least sig. byte of crc
 
    for (int i = 8; i != 0; i--) {    // Loop over each bit
      if ((crc & 0x0001) != 0) {      // If the LSB is set
        crc >>= 1;                    // Shift right and XOR 0xA001
        crc ^= 0xA001;
      }
      else                            // Else LSB is not set
        crc >>= 1;                    // Just shift right
    }
  }
  // Note, this number has low and high bytes swapped, so use it accordingly (or swap bytes)
  return crc;  
}
void sendsvcmd(int node, float sv) {
    message[0] = node;
    if (sv > 0 && sv < 250) {
      for (byte i=1; i<6; i++) {
            message[i] = setmessage[i];
      }
      Serial.print("received setpoint:");
      Serial.println(sv);
      int highbyte = (sv * 10) / 256;
      int lowbyte = int(sv * 10) & 255;
  
      Serial.print("High byte:");
      Serial.println(highbyte);
      Serial.print("Low byte:");
      Serial.println(lowbyte);
  
      message[4] = highbyte;
      message[5] = lowbyte;
     // pv = (float(buff[3] & 255) * 256 + float(buff[4] & 255))/10;
     // sv = (float(buff[5] & 255) * 256 + float(buff[6] & 255))/10;
      
      addcrc(message,6);
       
      if (DEBUG) {
        Serial.println("SENDING SV CMD");
        Serial.print("sending to controller: ");
        Serial.println(node);
        Serial.print(message[0],HEX);
        Serial.print(" ");
        Serial.print(message[1],HEX);
        Serial.print(" ");
        Serial.print(message[2],HEX);
        Serial.print(" ");
        Serial.print(message[3],HEX);
        Serial.print(" ");
        Serial.print(message[4],HEX);
        Serial.print(" ");
        Serial.print(message[5],HEX);
        Serial.print(" ");
        Serial.print(message[6],HEX);
        Serial.print(" ");
        Serial.println(message[7],HEX);
      }
      
      pinMode(RTSPIN, OUTPUT);
      digitalWrite(RTSPIN,HIGH);
      delay(xmitdelay);
  
      mySerial.write(message, sizeof(message));
  
      delay(xmitdelay);
      digitalWrite(RTSPIN,LOW);
      
      rxstart = millis();
      mbstate = 1;
    }

}
void addcrc(byte* message, int len) {
  mycrc = ModRTU_CRC(message, len);
//  Serial.println();
//  Serial.println(mycrc,HEX);
  long byte1 = mycrc & 255;
  long byte2 = (mycrc & long(255*256))>>8;
  if (DEBUG) {
    Serial.print(byte1,HEX);
    Serial.print(",");
    Serial.println(byte2,HEX);
  }
  message[len] = byte1;
  message[len + 1] = byte2;
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
      //listparams(0,0);
    }
    else if (str1 == "rlistparams") {
      //listparams(1,str2.toInt());
    }
    else if (str1 == "reset") {
//      resetMote();
    }
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
    else if (str1 =="setsv"){
      Serial.println(F("setsv: "));
      Serial.print(F("of channel: "));
      Serial.println(str2.toInt());
      Serial.print(F("To value: "));
      Serial.println(str3);
      Serial.println(F("AND here is where I send the message"));
      sendsvcmd(str2.toInt(), str3.toFloat());
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
