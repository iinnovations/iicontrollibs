#!/usr/bin/python

import spidev
import time

spi = spidev.SpiDev()
spi.open(0,1)   # Port 0, CS1

try:
    while True: 
    # Transfer one byte
        resp = spi.xfer2([255,255])
        print(resp[0])
        time.sleep(1)
except KeyboardInterrupt:
    spi.close()

# Notes:
# First list element: Anodes, low is on 
#

# Second list element: Cathodes, low is on
#   first three bits are what count

