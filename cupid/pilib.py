#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


# This library is for use by all other pi
# functions

# Global declarations of file locations

baselibdir = '/usr/lib/iicontrollibs/'
databasedir = '/var/www/data/'
onewiredir = '/var/1wire/'
outputdir = '/var/www/data/'

controldatabase = databasedir + 'controldata.db'
logdatabase = databasedir + 'logdata.db'
sessiondatabase = databasedir + 'authlog.db'
recipedatabase = databasedir + 'recipedata.db'
systemdatadatabase = databasedir + 'systemdata.db'
motesdatabase = databasedir + 'motes.db'
infodatabase = databasedir + 'deviceinfo.db'
authsdatabase = databasedir + 'authslog.db'

safedatabase = '/var/wwwsafe/safedata.db'
usersdatabase = '/var/wwwsafe/users.db'

logdir = '/var/log/cupid/'

networklog = logdir + 'network.log'
iolog = logdir + 'io.log'
remotelog = logdir + 'remotes.log'
syslog = logdir + 'systemstatus.log'
controllog = logdir + 'control.log'
daemonlog = logdir + 'daemon.log'
seriallog = logdir + 'serial.log'

daemonproclog = logdir + '/daemonproc.log'
errorlog = logdir + '/error.log'

salt = 'a bunch of random characters and symbols for security'

maxlogsize = 1024  # kB
numlogs = 5


networkloglevel = 5
iologlevel = 3
sysloglevel = 4
controlloglevel = 4
daemonloglevel = 3
serialloglevel = 2

daemonprocs = ['cupid/periodicupdateio.py', 'cupid/picontrol.py', 'cupid/systemstatus.py', 'cupid/sessioncontrol.py', 'mote/serialhandler.py']


"""
## Utility Functions

# This function is what keeps things sane for our database handling.
# We moved all references to database paths out of html entirely, and we
# pass handles. This does several things:
#   1. Centralizes all path references. No longer do we need to name paths in js and also in python
#      Now all references live on the server, where they belong. This way the the html/js is totally agnostic to
#      where things live.
#   2. Removes any path information from the html. Security issue: all html/js is visible to world.
#   3. Eliminates the possibility of queries on databases that are not properly locked down. There are permissions in
#      place to require authorization for anything but read-only operation, and often requirements in these cases,
#      but even better, we do aliasing server-side so that ONLY those databases that we alias (and under which conditions
#      we specify) are even readable. It also puts in place a clean way of selectively allowing access via user auths/keywords.

"""


def dbnametopath(friendlyname):
    friendlynames = ['controldb', 'logdatadb', 'infodb', 'systemdb', 'authdb', 'safedatadb', 'usersdb', 'motesdb', 'systemdatadb']
    paths = [controldatabase, logdatabase, infodatabase, systemdatadatabase, authsdatabase, safedatabase, usersdatabase, motesdatabase, systemdatadatabase]
    path = None
    if friendlyname in friendlynames:
        path = paths[friendlynames.index(friendlyname)]
    return path


def getgpiostatus():

    from subprocess import check_output

    gpiolist=[]
    alloutput = check_output(['gpio','readall'])
    lines = alloutput.split('\n')[3:18]
    for line in lines:
        BCM1 = line[4:6].strip()
        wpi1 = line[10:12].strip()
        name1 = line[15:22].strip()
        mode1 = line[25:30].strip()
        val1 = line[32:34].strip()
        phys1 = line[36:39].strip()

        phys2 = line[42:44].strip()
        val2 = line[46:48].strip()
        mode2 = line[50:55].strip()
        name2 = line[57:65].strip()
        wpi2 = line[68:70].strip()
        BCM2 = line[74:76].strip()

        if BCM1 and BCM1 != '--':
            # print(BCM1 + ':' + wpi1 + ':' + name1 + ':' + mode1 + ':' + val1 + ':' + phys1)
            gpiolist.append({'BCM': BCM1, 'wpi': wpi1, 'name': name1, 'mode': mode1, 'value': val1, 'phys': phys1})
        if BCM2 and BCM2 != '--':
            # print(BCM2 + ':' + wpi2 + ':' + name2 + ':' + mode2 + ':' + val2 + ':' + phys2)
            gpiolist.append({'BCM': BCM2, 'wpi': wpi2, 'name': name2, 'mode': mode2, 'value': val2, 'phys': phys2})

    return gpiolist


def gethashedentry(user, password):
    import hashlib
     # Create hashed, salted password entry
    hpass = hashlib.new('sha1')
    hpass.update(password)
    hashedpassword = hpass.hexdigest()
    hname = hashlib.new('sha1')
    hname.update(user)
    hashedname = hname.hexdigest()
    hentry = hashlib.new('md5')
    hentry.update(hashedname + salt + hashedpassword)
    hashedentry = hentry.hexdigest()
    return hashedentry


def rotatelogs(logname, numlogs=5, logsize=1024):
    import os

    returnmessage = ''
    logmessage = ''
    try:
        currlogsize = os.path.getsize(logname)
    except:
        logmessage = 'Error sizing original log'
        returnmessage = logmessage
        statuscode = 1
    else:
        statuscode = 0
        if currlogsize > logsize * 1000:
            for i in range(numlogs - 1):
                oldlog = logname + '.' + str(numlogs - i - 2)
                newlog = logname + '.' + str(numlogs - i - 1)
                try:
                    os.rename(oldlog, newlog)
                except:
                    logmessage += 'file error. log ' + oldlog + ' does not exist?\n'

            try:
                os.rename(logname, logname + '.1')
                os.chmod(logname + '.1', 744)
                open(logname, 'a').close()
                os.chmod(logname, 764)

            except:
                logmessage += 'original doesn\'t exist\?\n'
                returnmessage = "error in "
        else:
            logmessage += 'log not big enough\n'
            returnmessage = 'logs not rotated'
    return {'message': returnmessage, 'logmessage': logmessage, 'statuscode': statuscode}


#############################################
## Authlog functions 
#############################################

def checklivesessions(authdb, user, expiry):
    import time
    from utilities.datalib import timestringtoseconds
    from utilities.dblib import readalldbrows
    activesessions = 0
    sessions = readalldbrows(authdb, 'sessions')
    for session in sessions:
        sessioncreation = timestringtoseconds(session['timecreated'])
        currenttime = time.mktime(time.localtime())
        if currenttime - sessioncreation < expiry:
            activesessions += 1

    return activesessions


# this is an auxiliary function that will carry out additional actions depending on
# table values. For example, setting a 'pending' value when modifying setpoints
def setsinglecontrolvalue(database, table, valuename, value, condition=None):
    from utilities.datalib import gettimestring
    from utilities import dblib
    from utilities import utility

    if table == 'channels':
        utility.log(controllog, "Table: " + table + " found in keywords", 4, controlloglevel)

        if valuename in ['setpointvalue']:
            utility.log(controllog, "Set value: " + valuename + " found in keywords", 4, controlloglevel)

            # Get the channel data
            try:
                channeldata = dblib.readonedbrow(controldatabase, 'channels', condition=condition)[0]
            except:
                utility.log(controllog, "error retrieving channel with condition " + condition, 1, controlloglevel)
            else:
                utility.log(controllog, "Channel retrieval went ok with " + condition, 1, controlloglevel)

                if channeldata['type'] == 'remote' and channeldata['enabled']:
                    # Process setpointvalue send for remote here to make it as fast as possible.
                    # First we need to identify the node and channel by retrieving the interface

                    channelname = channeldata['name']
                    utility.log(controllog, "Processing remote setpoint for channel " + channelname, 1, iologlevel)
                    # Then go to the interfaces table to get the node and channel addresses
                    address = dblib.getsinglevalue(controldatabase, 'interfaces', 'address', "name='" + channelname + "'")
                    utility.log(controllog, "Channel has address " + address, 1, iologlevel)

                    node = address.split(':')[0]
                    channel = address.split(':')[1]

                    # If it's local, we send the command to the controller directly
                    if int(node) == 1:
                        message = '~setsv;' + channel + ';' + str(value)

                    # If not, first insert the sendmsg command to send it to the remote node
                    else:
                        message = '~sendmsg;' + node + ';;~setsv;' + channel + ';' + str(value)

                    utility.log(controllog, "Sending message: " + message, 1, iologlevel)


                    # Then queue up the message for dispatch

                    dblib.sqliteinsertsingle(motesdatabase, 'queuedmessages', [gettimestring(), message])

                # get existing pending entry
                pendingvaluelist = []

                pendingentry = dblib.getsinglevalue(database, table, 'pending', condition)
                if pendingentry:
                    try:
                        pendingvaluelist = pendingentry.split(',')
                    except:
                        pendingvaluelist = []

                if valuename in pendingvaluelist:
                    pass
                else:
                    pendingvaluelist.append(valuename)

                pendinglistentry = ','.join(pendingvaluelist)

                dblib.setsinglevalue(database, table, 'pending', pendinglistentry, condition)
        else:
            utility.log(controllog, "Set value: " + valuename + " not found in keywords", 4, controlloglevel)

    # carry out original query no matter what
    response = dblib.setsinglevalue(database, table, valuename, value, condition)
    return response


def getlogconfig():
    logconfigdata = dblib.readonedbrow(controldatabase, 'logconfig')[0]
    return logconfigdata


