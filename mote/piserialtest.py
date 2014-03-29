#!/usr/bin/python

import serial
import time

ser = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=1)

serstatus = ser.isOpen()
if not serstatus:
   ser.open()

input=1
while 1 :
        while ser.inWaiting() > 0:
            print(ser.readline())
