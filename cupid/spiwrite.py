#!/usr/bin/python

import spidev
import time

spi = spidev.SpiDev()
spi.open(0,1)   # Port 0, CS1

enabledlist1 = [0,0,0,0,0,0,0,0]
enabledlist2 = [0,0,0,0,0,0,0,0]

# Color LED assignments:
# list 1:
# 1 : RGB 2 Green 
# 2 : RGB 1 Blue 
# 3 : RGB 1 Red 
# 4 : RGB 1 Green 
# 5 : Yellow single color 
# 6 : Blue single color 
# 7 : Green single color 
# 8 : Red single color 

# list 2:

# 1 : RGB 4 Blue 
# 2 : RGB 4 Red 
# 3 : RGB 4 Green 
# 4 : RGB 3 Blue 
# 5 : RGB 3 Red 
# 6 : RGB 3 Green 
# 7 : RGB 2 Blue 
# 8 : RGB 2 Red 

wordsum1=0
for index,bit in enumerate(enabledlist1):
   wordsum1+=bit*(bit*2)**index
print('wordsum1: ' + str(wordsum1))
wordsum2=0
for index,bit in enumerate(enabledlist2):
   wordsum2+=bit*(bit*2)**index
print('wordsum2: ' + str(wordsum2)) 

spiassign1=255-wordsum1
spiassign2=255-wordsum2
#spiassign1=0
#spiassign2=0

try:
    while True: 
    # Transfer one byte
        resp = spi.xfer2([spiassign1,spiassign2])
        print(resp[0])
        time.sleep(1)
except KeyboardInterrupt:
    spi.close()

# Notes:
# First list element: Anodes, low is on 
#

# Second list element: Cathodes, low is on
#   first three bits are what count

