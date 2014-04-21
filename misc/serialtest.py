#!/usr/bin/env python

import serial
import time

serialPort = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=3)

if (serialPort.isOpen() == False):
    serialport.open()

outStr = ''
inStr = ''

serialPort.flushInput()
serialPort.flushOutput()

for i, a in enumerate(range(33, 126)):
    outStr += chr(a)

    serialPort.write(outStr)
    time.sleep(0.05)
    inStr = serialPort.read(serialPort.inWaiting())

    #print "inStr =  " + inStr
    #print "outStr = " + outStr

    if(inStr == outStr):
        print "WORKED! for length of %d" % (i+1)
    else:
        print "failed"

serialPort.close()
