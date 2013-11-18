#!/usr/bin/python

def readgpio(gpiolist=[18,23,24,25,4,17,21,22]):
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    responsedict={}
    for pin in gpiolist:
        responsedict[string(pin)]=GPIO.input(pin)

    return responsedict

    

if __name__ == '__main__':
    readgpio()
