#!/usr/bin/env python

import serial
import time

ser=serial.Serial('/dev/ttyAMA0',115200,timeout=10)

while True:
   print('writing')
   ser.write('r')
   print('reading')
   ser.read()
   time.sleep(10)
