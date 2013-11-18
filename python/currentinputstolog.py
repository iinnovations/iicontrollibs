#!/usr/bin/python
# Colin Reese
# 12/18/2012
#
# This script appends all temps found in currenttemps to the
# log file, according to the settings in the settings file 

############################# DEPRECATED  ###################

#############################################################

import re
import os
import csv
import time
import pilib

filedir = ""
settingsfilepath = "/var/www/data/settings.txt"
tempsfilepath = "/var/www/data/currenttemps.txt"
plottempsfilepath = "/var/www/data/plottemps.txt"
logtempsfilepath = "/var/www/data/logtemps.txt"
controlfilepath = "/var/www/data/control_status.txt"

# Read settings

settingsdict=pilib.readsettingsfile(settingsfilepath)
logpoints=int(settingsdict['logpoints'])
plotpoints=int(settingsdict['plotpoints'])

# Read control_status info

controldict=pilib.readcontrolfile(controlfilepath)
action=controldict['action']
setpoint=controldict['setpoint']
fan=controldict['fan']

actionint='0'
fanint='0'

if action=="heat":
    actionint="1"
elif action=="cool":
    actionint="-1"
else:
    actionint=0

if fan=="on":
    fanint="0.9"
else:
    fanint="0"


# Read all temps into a list
# Need some error handling in here for files

tempsfile=open(tempsfilepath,'r')
tempslist=[]
tempsreaderlist=csv.reader(tempsfile,delimiter=',')
for item in tempsreaderlist:
    tempslist.append(item)

# Add setpoint and action settings
tempslist.append(["setpoint",setpoint, time.strftime("%d-%m-%Y %H:%M:%S")])
tempslist.append(["action",actionint, time.strftime("%d-%m-%Y %H:%M:%S")])
tempslist.append(["fan",fanint, time.strftime("%d-%m-%Y %H:%M:%S")])

# Open log files, create if don't exist
logtempsfile=open(logtempsfilepath,'ab+')
plottempsfile=open(plottempsfilepath,'w+')

# Read existing data out of file
loglist=[]
logreaderlist=csv.reader(logtempsfile,delimiter=",")
for item in logreaderlist:
    loglist.append(item)
#print("loglist")
#print(loglist)

logtempsfile.close

# Format of log:
#                  Header
#                  time, timedata, timedata ... 
#                  ROM, temperature, temperature ...

# iterate through and add data
newlog=[]
for temptuple in tempslist:
    #print("temptuple")
    #print(temptuple)
    found=False
    for entry in loglist:
        if entry[0] == temptuple[0]:
            #print("entry")
            #print(entry)

            # identify index of match
            index=loglist.index(entry)

            # add time and temperature
            timelist=loglist[index-1]
            templist=loglist[index]
            timelist.append(temptuple[2])
            templist.append(temptuple[1])
            newlog.append(timelist)
            newlog.append(templist)
            #print("found")
            found=True
            break
    if found==False:
        #print("making new entry")
        newlog.append(["time",temptuple[2]])
        newlog.append([temptuple[0],temptuple[1]])

#print(newlog)

# Write log to file

header = "log file written " + time.strftime("%d-%m-%Y %H:%M:%S" + "\n")
outputlogfile=open(logtempsfilepath,'wb')
outputlogfile.write(header)
w=csv.writer(outputlogfile, lineterminator="\n")
for row in newlog:
    if len(row)>logpoints+1:
        startindex=int(len(row)-logpoints)
        endindex=int(len(row))
        newrow=row[startindex:endindex]
        newrow.insert(0,row[0])
        row=newrow
    w.writerow(row)
outputlogfile.close()

# Write plot points to file

header = "log file written " + time.strftime("%d-%m-%Y %H:%M:%S" + "\n")
outputplotlogfile=open(plottempsfilepath,'wb')
outputplotlogfile.write(header)
w=csv.writer(outputplotlogfile, lineterminator="\n")
for row in newlog:
    if len(row)>plotpoints+1:
        startindex=int(len(row)-plotpoints)
        endindex=int(len(row))
        newrow=row[startindex:endindex]
        newrow.insert(0,row[0])
        row=newrow
    w.writerow(row)
outputplotlogfile.close()



