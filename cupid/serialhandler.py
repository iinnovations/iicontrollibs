#!/usr/bin/env python

import serial,time

port = '/dev/ttyAMA0'
baudrate = 115200
timeout=1

ser = serial.Serial(port=port,baudrate=baudrate,timeout=timeout)

def write(message,port=ser):
    ser.write(message)

def monitor():
    print "Monitoring serial port " + ser.name
    data = []
    while True:
	ch = ser.read(1)
	if len(ch) == 0:
		# rec'd nothing print all
		if len(data) > 0:
			s = ''
			for x in data:
				s += ' %02X' % ord(x)
			print '%s [len = %d]' % (s, len(data))
		data = []
	else:
		data.append(ch)
