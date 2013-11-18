#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# This script handles spi read functions 
# We use SPIdev0, because this is what is physically
# connected on the cupid control

import os
import time
import pilib

querylist=[];

########################################
# Read Thermocouple temperature. Clearly 
# we need to have a selector for what to 
# read/write on our SPI interface

def readspi():
    valuedict={}
    valuedict['SPITC1']=getspitctemp().rstrip()
    return valuedict 
    
def getspitctemp():
    import subprocess
    tctemp=subprocess.check_output(['python3','/usr/lib/modwsgi/max31855-1.0/getmaxtemp.py'])
    return tctemp

def recordspidata(database,valuedict):
    # This is incomplete and hardcoded partially
    querylist=[]
    for key,value in valuedict.iteritems():
        querylist.append(pilib.makesqliteinsert(database,'inputsdata',[key,'SPI1','TC',value,'F',pilib.gettimestring(),1,'']))
    pilib.sqlitemultquery(database,querylist)

if __name__ == "__main__":
    database = '/var/www/data/controldata.db'
    valuedict=readspi() 
    recordspidata(database,valuedict)
    print(valuedict)
