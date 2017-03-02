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

"""
Global declarations of useful variables. We are transitioning to bunches of definitions, which make
things a bit easier to move around, and mainly simpler to iteratively assign without having to use hacks for
variable names

Question:   Which things are hard-coded here? Why would everything just not be in the database?
Answer:     Only things which may need to be changed at run-time by the user/admin are in the database. \
            Log locations, for example, don't have a practical reason to be assigned in this instance.
            Log levels, on the other hand, may need to be regularly changed from the web UI
            We have hybrids (as above) where we set a default level here and then set attempt to get updated values
            from the database. We try to do this in as error-tolerant a fashion as we can.
"""

from iiutilities.utility import Bunch

dirs = Bunch()

dirs.baselib = '/usr/lib/iicontrollibs/'
dirs.database = '/var/www/data/'
dirs.onewire = '/var/1wire/'
dirs.output = '/var/www/data/'
dirs.log = '/var/log/cupid/'

dirs.dbs = Bunch()

dirs.dbs.control = dirs.database + 'control.db'
dirs.dbs.log = dirs.database + 'logdata.db'
dirs.dbs.session = dirs.database + 'authlog.db'
dirs.dbs.recipe = dirs.database + 'recipedata.db'
dirs.dbs.system = dirs.database + 'system.db'
dirs.dbs.motes = dirs.database + 'motes.db'
dirs.dbs.info = dirs.database + 'deviceinfo.db'
dirs.dbs.auths = dirs.database + 'authslog.db'
dirs.dbs.notifications = dirs.database + 'notifications.db'
dirs.dbs.safe = '/var/wwwsafe/safedata.db'
dirs.dbs.users = '/var/wwwsafe/users.db'

dirs.logs = Bunch()

dirs.logs.network = dirs.log + 'network.log'
dirs.logs.io = dirs.log + 'io.log'
dirs.logs.remote = dirs.log + 'remotes.log'
dirs.logs.system = dirs.log + 'systemstatus.log'
dirs.logs.control = dirs.log + 'control.log'
dirs.logs.daemon = dirs.log + 'daemon.log'
dirs.logs.serial = dirs.log + 'serial.log'
dirs.logs.notifications = dirs.log + 'notifications.log'
dirs.logs.daemonproc = dirs.log + 'daemonproc.log'
dirs.logs.error = dirs.log + 'error.log'

salt = 'a bunch of random characters and symbols for security'

maxlogsize = 1024  # kB
numlogs = 5

loglevels = Bunch()

# These just really serve as defaults. We pick them up later from the db.

loglevels.network = 5
loglevels.io = 3
loglevels.system = 4
loglevels.control = 4
loglevels.daemon = 3
loglevels.serial = 2
loglevels.notifications = 5

daemonprocs = ['cupid/periodicupdateio.py', 'cupid/picontrol.py', 'cupid/systemstatus.py', 'cupid/sessioncontrol.py', 'mote/serialhandler.py']
daemonprocnames = ['updateio', 'picontrol', 'systemstatus', 'sessioncontrol', 'serialhandler']

"""
Utility Functions

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
    friendlynames = ['controldb', 'logdatadb', 'infodb', 'systemdb', 'authdb', 'safedatadb', 'usersdb', 'motesdb', 'notificationsdb']
    paths = [dirs.dbs.control, dirs.dbs.log, dirs.dbs.info, dirs.dbs.system, dirs.dbs.auths, dirs.dbs.safe, dirs.dbs.users, dirs.dbs.motes, dirs.dbs.notifications]
    path = None
    if friendlyname in friendlynames:
        path = paths[friendlynames.index(friendlyname)]
    return path


def processnotification(notification):
    from cupid import pilib
    from iiutilities import datalib
    from iiutilities import utility
    from iiutilities.netfun import pingstatus

    senttime = datalib.gettimestring()
    result = {'status':1, 'senttime':senttime}
    if notification['type'] == 'email':

        # Check to make sure we're online.
        pingresult = pingstatus()
        if not pingresult['status']:

            utility.log(dirs.logs.notifications, 'WAN access is ok, so processing notification')
            options = datalib.parseoptions(notification['options'])
            message = notification['message']
            if 'subject' in options:
                subject = options['subject']
            else:
                subject = 'CuPID Notification Email'

            message += '\r\n\r\n'
            message += 'Message queued:\t ' + notification['queuedtime'] + '\r\n'
            message += 'Message sent:\t ' + senttime + '\r\n'

            if 'email' in options:
                print('i found emai')
                try:
                    email = options['email']
                    actionmail = utility.gmail(message=message, subject=subject, recipient=email)
                    actionmail.send()
                except:
                    pass
                else:
                    result['status'] = 0
        else:
            utility.log(dirs.logs.notifications, 'WAN access does not appear to be ok. Status is: ' + str(pingstatus['status']))

    return result


def processnotificationsqueue():
    from iiutilities import dblib
    from iiutilities.utility import log

    notifications_db = dblib.sqliteDatabase(dirs.dbs.notifications)
    queuednotifications = notifications_db.read_table('queued')

    for notification in queuednotifications:
        if loglevels.notifications >= 5:
            log(dirs.logs.notifications, 'Processing notification of type' + notification['type'] + '. Message: ' + notification['message'] + '. Options: ' + notification['options'])
        else:
            log(dirs.logs.notifications, 'Processing notification of type' + notification['type'], dirs.logs.notifications)

        result = processnotification(notification)

        if result['status'] == 0:
            log(dirs.logs.notifications, 'Notification appears to have been successful. Copying message to sent.')
            sententry = notification.copy()
            sententry['senttime'] = result['senttime']
            dblib.insertstringdicttablelist(dirs.dbs.notifications, 'sent', [sententry], droptable=False)

            log(dirs.logs.notifications, 'Removing entry from queued messages.')

            # match by time and message
            conditionnames = ['queuedtime', 'message']
            conditionvalues = [sententry['queuedtime'], sententry['message']]

            notifications_db.delete('queued', {'conditionnames':conditionnames, 'conditionvalues':conditionvalues})

            # delquery = dblib.makedeletesinglevaluequery('queuednotifications', {'conditionnames':conditionnames, 'conditionvalues':conditionvalues})
            # dblib.sqlitequery(dirs.dbs.notifications, delquery)

        else:
            log(dirs.logs.notifications, 'Notification appears to have failed. Status: ' + str(result['status']))


""" IO functions

"""


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



class io_wrapper(object):

    """
    This is going to be a general class of IO handler that has a identifying values to match against (to know when we
    need to destroy and recreate it), and can handle functions in the background, such as pigpiod callbacks. This way
    we can do more than atomic read/write operations. For GPIO, we can even set callbacks for value changes.
    """
    def __init__(self, **kwargs):
        # self.required_properties = ['type','options', 'pi']
        self.required_properties = ['pi']

        if not all(property in kwargs for property in self.required_properties):
            print('You did not provide all required parameters: ' + str(self.required_properties))
        self.settings = {}
        self.settings.update(kwargs)
        for key,value in self.settings.iteritems():
            setattr(self, key, value)


class pigpiod_gpio_counter(io_wrapper):

    def __init__(self, **kwargs):
        # inherit parent properties
        super(pigpiod_gpio_counter, self).__init__(**kwargs)

        import pigpio
        self.settings = {'edge':'falling', 'pullupdown':None, 'debounce_ms':20, 'event_min_ms':20,
                         'watchdog_ms':1000, 'rate_period_ms':2000}
        self.settings.update(kwargs)
        for key,value in self.settings.iteritems():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.INPUT)
        if self.pullupdown in ['up', 'pullup']:
            self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)

        self._cb = self.pi.callback(self.gpio, pigpio.FALLING_EDGE, self._cbf)
        self.pi.set_watchdog(self.gpio, self.watchdog_ms)

        self.busy = False
        self.ticks = 0
        self.last_event_count = 0

        self.last_counts = None
        self.last_counts_time = None
        self.rate = 0

    def _cbf(self, gpio, level, tick):
        if not self.busy:
            self.busy = True
            self.process_callback(gpio, level, tick)

    def process_callback(self, gpio, level, tick):
        # a tick event happened
        import time

        if level == 0:  # Falling edge
            time.sleep(0.001 * self.debounce_ms)
            value = self.pi.read(self.gpio)
            if value == 0:
                # print('event length satisfied')

                if tick - self.last_event_count > self.debounce_ms * 1000:
                    self.ticks += 1
                    self.last_event_count = tick
                else:
                    print('debounce')
            else:
                # print('event not long enough ( we waited to see ).')
                pass

        elif level == 2:  # Watchdog timeout. We will calculate
            pass

        self.busy = False

    def get_value(self):
        from datetime import datetime
        now = datetime.now()
        if self.last_counts_time:
            seconds_delta = now - self.last_counts_time
            seconds_passed = seconds_delta.seconds + float(seconds_delta.microseconds) / 1000000
            self.rate = float(self.ticks - self.last_counts) / seconds_passed

            print('COUNTING RATE')
            print(self.last_counts, self.ticks)

        self.last_counts = self.ticks
        self.last_counts_time = now

        # self.event_tick = 0  # reset event
        return self.ticks

    def get_rate(self):

        return self.rate


class pigpiod_gpio_input(io_wrapper):
    def __init__(self, **kwargs):
        # inherit parent properties
        super(pigpiod_gpio_input, self).__init__(**kwargs)

        import pigpio
        self.settings = {'pullupdown': None}
        self.settings.update(kwargs)

        for key, value in self.settings.iteritems():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.INPUT)
        if self.pullupdown in ['up', 'pullup']:
            self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)
        elif self.pullupdown in ['down','pulldown']:
            self.pi.set_pull_up_down(self.gpio, pigpio.PUD_DOWN)

    def get_value(self):
        self.pi.read(self.gpio)


class pigpiod_gpio_output(io_wrapper):
    def __init__(self, **kwargs):
        # inherit parent properties
        super(pigpiod_gpio_output, self).__init__(**kwargs)

        import pigpio
        self.settings = {}
        self.settings.update(kwargs)

        for key, value in self.settings.iteritems():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.OUTPUT)

    def get_value(self):
        self.pi.read(self.gpio)

    def set_value(self, value):
        self.pi.write(self.gpio, value)


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


#############################################
## Authlog functions 
#############################################

def checklivesessions(authdb, user, expiry):
    import time
    from iiutilities.datalib import timestringtoseconds
    from iiutilities.dblib import readalldbrows
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
    from iiutilities.datalib import gettimestring
    from iiutilities import dblib
    from iiutilities import utility

    if table == 'channels':
        utility.log(dirs.logs.control, "Table: " + table + " found in keywords", 4, loglevels.control)

        if valuename in ['setpointvalue']:
            utility.log(dirs.logs.control, "Set value: " + valuename + " found in keywords", 4, loglevels.control)

            # Get the channel data
            try:
                channeldata = dblib.readonedbrow(dirs.dbs.control, 'channels', condition=condition)[0]
            except:
                utility.log(dirs.logs.control, "error retrieving channel with condition " + condition, 1, loglevels.control)
            else:
                utility.log(dirs.logs.control, "Channel retrieval went ok with " + condition, 1, loglevels.control)

                if channeldata['type'] == 'remote' and channeldata['enabled']:
                    # Process setpointvalue send for remote here to make it as fast as possible.
                    # First we need to identify the node and channel by retrieving the interface

                    channelname = channeldata['name']
                    utility.log(dirs.logs.control, "Processing remote setpoint for channel " + channelname, 1, loglevels.io)
                    # Then go to the interfaces table to get the node and channel addresses
                    address = dblib.getsinglevalue(dirs.dbs.control, 'interfaces', 'address', "name='" + channelname + "'")
                    utility.log(dirs.logs.control, "Channel has address " + address, 1, loglevels.io)

                    node = address.split(':')[0]
                    channel = address.split(':')[1]

                    # If it's local, we send the command to the controller directly
                    if int(node) == 1:
                        message = '~setsv;' + channel + ';' + str(value)

                    # If not, first insert the sendmsg command to send it to the remote node
                    else:
                        message = '~sendmsg;' + node + ';;~setsv;' + channel + ';' + str(value)

                    utility.log(dirs.logs.control, "Sending message: " + message, 1, loglevels.io)


                    # Then queue up the message for dispatch

                    dblib.sqliteinsertsingle(dirs.dbs.motes, 'queued', [gettimestring(), message])

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
            utility.log(dirs.logs.control, "Set value: " + valuename + " not found in keywords", 4, loglevels.control)

    # carry out original query no matter what
    response = dblib.setsinglevalue(database, table, valuename, value, condition)
    return response


def reload_log_config():
    from iiutilities.dblib import readonedbrow
    logconfigdata = readonedbrow(dirs.dbs.system, 'logconfig')[0]

    loglevels.network = logconfigdata['network']
    loglevels.io = logconfigdata['io']
    loglevels.system = logconfigdata['system']
    loglevels.control = logconfigdata['control']
    loglevels.daemon = logconfigdata['daemon']
    loglevels.serial = logconfigdata['serial']
    loglevels.notifications = logconfigdata['notifications']

    return logconfigdata


def set_debug():
    for attr, value in loglevels.__dict__.iteritems():
        setattr(loglevels, attr, 9)


# Attempt to update from database. If we are unsuccessful, the above are defaults

try:
    logconfig = reload_log_config()
except:
    pass
else:
    for key in logconfig:
        try:
            setattr(loglevels, key, logconfig[key])
        except:
            print ('Set attribute for "' + key + '" did not work')

