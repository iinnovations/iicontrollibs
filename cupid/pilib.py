#!/usr/bin/python3

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
from iiutilities import dblib

dirs = Bunch()

dirs.baselib = '/usr/lib/iicontrollibs/'
dirs.web = '/var/www/'
dirs.database = dirs.web + 'data/'
dirs.onewire = '/var/1wire/'
dirs.output = dirs.web + 'data/'
dirs.log = '/var/log/cupid/'
dirs.archive = dirs.database + 'archive/'
dirs.safe = '/var/wwwsafe/'

dirs.dbs = Bunch()

dirs.dbs.control = dirs.database + 'control.db'
dirs.dbs.log = dirs.database + 'logdata.db'
dirs.dbs.session = dirs.database + 'authlog.db'
dirs.dbs.recipe = dirs.database + 'recipedata.db'
dirs.dbs.system = dirs.database + 'system.db'
dirs.dbs.motes = dirs.database + 'motes.db'
dirs.dbs.info = dirs.database + 'deviceinfo.db'
dirs.dbs.auths = dirs.database + 'authslog.db'
dirs.dbs.data_agent = '/var/wwwsafe/dataagent.db'
dirs.dbs.notifications = dirs.database + 'notifications.db'

dirs.dbs.safe = dirs.safe + 'safedata.db'
dirs.dbs.users = dirs.safe + 'users.db'

dirs.logs = Bunch()

dirs.logs.network = dirs.log + 'network.log'
dirs.logs.io = dirs.log + 'io.log'
dirs.logs.remote = dirs.log + 'remotes.log'
dirs.logs.system = dirs.log + 'systemstatus.log'
dirs.logs.control = dirs.log + 'control.log'
dirs.logs.daemon = dirs.log + 'daemon.log'
dirs.logs.actions = dirs.log + 'actions.log'
dirs.logs.serial = dirs.log + 'serial.log'
dirs.logs.notifications = dirs.log + 'notifications.log'
dirs.logs.daemonproc = dirs.log + 'daemonproc.log'
dirs.logs.error = dirs.log + 'error.log'
dirs.logs.db = dirs.log + 'db.log'

dbs = Bunch()

class cupidDatabase(dblib.sqliteDatabase):

    def __init__(self, *args, **kwargs):
        settings = {
            'log_errors':True,
            'log_path':dirs.logs.db,
            'quiet':True
        }
        settings.update(kwargs)

        # This calls the parent init
        super(cupidDatabase, self).__init__(*args, **settings)

for db_name in dirs.dbs.__dict__:
    setattr(dbs, db_name, cupidDatabase(getattr(dirs.dbs, db_name)))

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
loglevels.actions = 2
loglevels.notifications = 5

daemonprocs = ['cupid/periodicupdateio.py', 'cupid/picontrol.py', 'cupid/systemstatus.py', 'cupid/sessioncontrol.py', 'mote/serialhandler.py']
daemonprocnames = ['updateio', 'picontrol', 'systemstatus', 'sessioncontrol', 'serialhandler']

schema = Bunch()
schema.channel = dblib.sqliteTableSchema([
    # {'name': 'channelindex','type':'integer','primary':True},
    {'name': 'name', 'unique': True},
    {'name': 'index', 'type': 'integer', 'primary': True},
    {'name': 'type', 'default': 'local'},
    {'name': 'id', 'unique': True},
    {'name': 'pv_input', 'default': 'none'},
    {'name': 'sv_input', 'default': 'none'},
    {'name': 'output_input', 'default': 'none'},
    {'name': 'enabled_input', 'default': 'none'},
    {'name': 'enabled', 'type': 'boolean', 'default': 0},
    {'name': 'outputs_enabled', 'type': 'boolean', 'default': 0},
    {'name': 'control_update_time'},
    {'name': 'control_algorithm', 'default': 'on/off 1'},
    {'name': 'control_recipe', 'default': 'none'},
    {'name': 'recipe_stage', 'type': 'integer', 'default': 0},
    {'name': 'recipe_start_time'},
    {'name': 'recipe_stage_start_time'},
    {'name': 'setpoint_value', 'type': 'real'},
    {'name': 'process_value', 'type': 'real'},
    {'name': 'process_value_time'},
    {'name': 'positive_output'},
    {'name': 'negative_output'},
    {'name': 'action', 'type': 'real', 'default': 0},
    {'name': 'mode', 'default': 'manual'},
    {'name': 'status_message'},
    {'name': 'log_options', 'default': 'mode:timespan,size:8,unit:hours'},
    {'name': 'data'},
    {'name': 'dataclasses'},
    {'name': 'pending'}
])
schema.input = dblib.sqliteTableSchema([
    {'name': 'id', 'primary':True},
    {'name': 'interface'},
    {'name': 'type'},
    {'name': 'address'},
    {'name': 'name'},
    {'name': 'value', 'type': 'real'},
    {'name': 'unit'},
    {'name': 'polltime'},
    {'name': 'pollfreq'},
    {'name': 'ontime'},
    {'name': 'offtime'},
    {'name': 'log_options', 'default': 'mode:timespan,size:8,unit:hours'}
])

schema.channel_datalog = dblib.sqliteTableSchema([
    {'name':'time','primary':True},
    {'name':'process_value','type':'real'},
    {'name':'setpoint_value','type':'real'},
    {'name':'action','type':'real'},
    {'name':'algorithm'},
    {'name':'enabled','type':'real'},
    {'name':'status_msg'}
])
schema.standard_datalog = dblib.sqliteTableSchema([
    {'name':'time', 'primary':True},
    {'name':'value', 'type':'real'}
])
schema.data_agent = dblib.sqliteTableSchema([
    {'name':'data_id','primary':True},
    {'name':'data_name'},
    {'name':'send_freq', 'default':'0'},           # Seconds. Zero means whenever there is new data, send it
    {'name':'last_send'},
    {'name':'last_send_timestamp'},
    {'name':'total_sends', 'type':'integer'},
    {'name':'last_send_size','type':'integer'},
    {'name':'cume_send_size','type':'integer'}
])
schema.data_items = dblib.sqliteTableSchema([
    {'name':'valuename','primary':True},
    {'name':'value'}
])
schema.mote = dblib.sqliteTableSchema([
    {'name':'time'},
    {'name':'message','primary':True},
    {'name':'value'}
])
schema.users = dblib.sqliteTableSchema([
    {'name':'id','type':'integer', 'primary':True},
    {'name':'name'},
    {'name':'password'},
    {'name':'email'},
    {'name':'temp'},
    {'name':'authlevel','type':'integer','default':0}
])

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

# This is a subclass to set default pilib logging options.


def updateiicontrollibs(stash=False):
    from iiutilities.gitupdatelib import stashrepo, pullrepo, updaterepoversion
    repodirectory = dirs.baselib
    originname = 'master'
    if stash:
        stashrepo(repodirectory, originname)
    pullrepo(repodirectory, originname)
    updaterepoversion(repodirectory)
    print('update complete')


def updatecupidweblib(stash=False):
    from iiutilities.gitupdatelib import stashrepo, pullrepo, updaterepoversion
    repodirectory = dirs.web
    originname = 'master'
    if stash:
        stashrepo(repodirectory,originname)
    pullrepo(repodirectory, originname)
    updaterepoversion(repodirectory)
    print('update complete')


def table_name_to_type(tablename):
    type = 'unknown'
    subtype = 'unknown'
    id = 'unknown'
    try:
        splits = tablename.split('_')
        for test_type in ['input', 'channel']:
            if splits[0] == test_type:
                type = test_type

        if splits[1].lower().find('gpio') >= 0:
            subtype = 'gpio'
        elif splits[1].lower().find('mote') >=0:
            subtype = 'mote'
        elif splits[1].lower().find('1wire') >=0:
            subtype = '1wire'

        id = '_'.join(splits[1:-1])
    except:
        pass
    return {'type':type, 'subtype':subtype, 'id':id}


def dbnametopath(friendlyname):
    friendlynames = ['controldb', 'logdatadb', 'infodb', 'systemdb', 'authdb', 'safedatadb', 'usersdb', 'motesdb', 'notificationsdb']
    paths = [dirs.dbs.control, dirs.dbs.log, dirs.dbs.info, dirs.dbs.system, dirs.dbs.auths, dirs.dbs.safe, dirs.dbs.users, dirs.dbs.motes, dirs.dbs.notifications]
    path = None
    if friendlyname in friendlynames:
        path = paths[friendlynames.index(friendlyname)]
    return path


def processnotification(notification):
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
                try:
                    email = options['email']
                    actionmail = utility.gmail(message=message, subject=subject, recipient=email)
                    actionmail.send()
                except:
                    pass
                else:
                    result['status'] = 0
        else:
            utility.log(dirs.logs.notifications, 'WAN access does not appear to be ok. Status is: ' + str(pingresult['status']))

    return result


def process_notifications_queue():
    from iiutilities import dblib
    from iiutilities.utility import log

    notifications_db = cupidDatabase(dirs.dbs.notifications)
    queuednotifications = notifications_db.read_table('queued')

    for notification in queuednotifications:
        if loglevels.notifications >= 5:
            log(dirs.logs.notifications, 'Processing notification of type' + notification['type'] + '. Message: ' + notification['message'] + '. Options: ' + notification['options'])
        else:
            log(dirs.logs.notifications, 'Processing notification of type' + notification['type'])

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


def run_cupid_data_agent():

    from iiutilities import dblib

    # Get api info
    safe_db = cupidDatabase(dirs.dbs.safe)
    api_info = safe_db.read_table('api')

    if not api_info:
        print('No API info found. Aborting. ')
        return




""" 
IO functions
"""


def getgpiostatus():

    from subprocess import check_output

    gpiolist=[]
    alloutput = check_output(['gpio','readall']).decode('utf-8')
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
        for key,value in self.settings.items():
            setattr(self, key, value)


class pigpiod_gpio_counter(io_wrapper):

    def __init__(self, **kwargs):
        import copy
        # inherit parent properties
        super(pigpiod_gpio_counter, self).__init__(**kwargs)

        import pigpio
        self.settings = {'edge':'falling', 'pullupdown':None, 'debounce_ms':10, 'event_min_ms':10,
                         'watchdog_ms':1000, 'rate_period_ms':2000, 'debug':False, 'reset_ticks':30000,
                         'busy':False, 'init_counts':0}
        self.settings.update(kwargs)
        for key,value in self.settings.items():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_glitch_filter(self.gpio, self.settings['debounce_ms'] * 1000)

        if self.pullupdown in ['up', 'pullup']:
            self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)

        self._cb = self.pi.callback(self.gpio, pigpio.FALLING_EDGE, self._cbf)
        self.pi.set_watchdog(self.gpio, self.watchdog_ms)

        self.busy = False
        self.ticks = copy.copy(self.settings['init_counts'])
        self.last_event_count = 0

        self.last_counts = copy.copy(self.settings['init_counts'])
        if self.settings['init_counts']:
            from datetime import datetime
            self.last_counts_time = datetime.now()
        else:
            self.last_counts_time = None
        self.rate = 0

    def _cbf(self, gpio, level, tick):
        if not self.busy:
            self.busy = True
            self.process_callback(gpio, level, tick)

    def process_callback(self, gpio, level, tick):
        # a tick event happened
        import time

        try:
            if level == 0:  # Falling edge
                # time.sleep(0.001 * self.debounce_ms)
                # value = self.pi.read(self.gpio)
                # if value == 0:
                    # print('event length satisfied')

                    # if tick - self.last_event_count > self.debounce_ms * 1000:
                self.ticks += 1
                self.last_event_count = tick
                    # else:
                    #     if self.debug:
                    #         print('debounce')
                # else:
                    # print('event not long enough ( we waited to see ).')
                    # pass

            elif level == 2:  # Watchdog timeout. We will calculate
                pass

            self.busy = False
        except:
            pass
            # import traceback
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print("*** ****************************************************")
            # print('PROCESSING ERROR')
            # errorstring = traceback.format_exc()
            # print(errorstring)


    def get_value(self):
        from datetime import datetime
        now = datetime.now()
        if self.last_counts_time:
            seconds_delta = now - self.last_counts_time
            seconds_passed = seconds_delta.seconds + float(seconds_delta.microseconds) / 1000000
            self.rate = float(self.ticks - self.last_counts) / seconds_passed
            if self.debug:
                print('COUNTING RATE')
                print(self.last_counts, self.ticks)

        self.last_counts = self.ticks
        self.last_counts_time = now

        if self.ticks > self.reset_ticks:
            if self.debug:
                print('RESETTINGS (count is ' + str(self.ticks) + ')')
                print('reset_ticks : ' + str(self.reset_ticks))
            self.last_counts -= self.reset_ticks
            self.ticks -= self.reset_ticks
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

        for key, value in self.settings.items():
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

        for key, value in self.settings.items():
            setattr(self, key, value)

        self.pi.set_mode(self.gpio, pigpio.OUTPUT)

    def get_value(self):
        self.pi.read(self.gpio)

    def set_value(self, value):
        self.pi.write(self.gpio, value)

"""
Auths helpers
"""


def check_action_auths(action, level):
    action_auths_dict = {
        'gettabledata':1,
        'modifychannel':3,
        'enablechannel':2,
        'modifyaction':3,
        'modifchannelalarm':3,
        'enableaction':2,
        'userdelete':5, 'useradd':5, 'usermodify':5,
        'setvalue':4,
        'setsystemflag':5,
        'getmbtcpdata':2,
        'getfiletext':5,
        'dump':999
    }
    # Currently setup to blacklist only.
    if action in action_auths_dict:
        level_required = action_auths_dict[action]
    else:
        level_required = 0
    try:
        if int(level) >= level_required:
            authorized = True
        else:
            authorized = False
    except:
        authorized = False

    print('Action ' + action + ', ' + str(level) + ' provided, ' + str(level_required) + ' required : ' + str(authorized))

    return authorized


"""
Authlog functions
"""


def checklivesessions(authdb, user, expiry):
    import time
    from iiutilities.datalib import timestringtoseconds
    activesessions = 0
    sessions = dbs.authdb.read_table('sessions')
    for session in sessions:
        sessioncreation = timestringtoseconds(session['timecreated'])
        currenttime = time.mktime(time.localtime())
        if currenttime - sessioncreation < expiry:
            activesessions += 1

    return activesessions

"""
WSGI helpers
"""

# This needs to be a subroutine, since it's very commonly used.
def app_check_keywords(d, required_keywords, output):

    if not all(required_keywords in d):
        output['message'] += 'Not all required keywords found. '
        for keyword in required_keywords:
            if keyword not in d:
                output['message'] += '{} not found. '.format(keyword)
        return False
    else:
        return True


def copy_log_to_archive(log_name, **kwargs):

    settings = {
        'archive_name': None,
        'force_extension': True,
        'extension':'.db',
        'directory': dirs.archive
    }
    settings.update(kwargs)

    from iiutilities.datalib import gettimestring

    if not settings['archive_name']:
        settings['archive_name'] = log_name + gettimestring() + '.db'

    if settings['force_suffix'] and settings['archive_name'][-3:] != settings['suffix']:
        settings['archive_name'] += '.db'

    # Determine type by log name

    from iiutilities.datalib import gettimestring
    archive_db = dblib.sqliteDatabase(settings['directory'] + settings['archive_name'])
    logs_db = dblib.sqliteDatabase(dirs.dbs.log)

    existing_table = logs_db.read_table(log_name)
    existing_schema = logs_db.get_schema(log_name)
    archive_db.create_table('data', existing_schema, queue=True)
    archive_db.insert('data', existing_table, queue=True)

    archive_db.create_table('info', schema.data_items, queue=True)
    archive_db.insert('info', {'valuename': 'created', 'value': gettimestring()}, queue=True)
    archive_db.insert('info', {'valuename': 'name', 'value': log_name}, queue=True)

    archive_db.execute_queue()


def rotate_all_logs(**kwargs):

    # These defaults come from globals above
    settings = {
        'logs_to_keep':numlogs,
        'max_log_size':maxlogsize,
        'debug':False
    }
    settings.update(**kwargs)

    from iiutilities.utility import rotate_log_by_size
    for attr, value in dirs.logs.__dict__.items():
        if settings['debug']:
            print('Rotating {}'.format(attr))
        rotate_log_by_size(value, settings['logs_to_keep'], settings['max_log_size'])


def app_copy_log_to_archive(d,output):
    required_keywords = ['log_name', 'archived_log_name']
    if not app_check_keywords(d,required_keywords,output):
        return

    copy_log_to_archive(d['log_name'], d['archived_log_name'])


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

                """
                This all needs to go into the picontrol section
                Set a pending value in modify channel, then picontrol processes pending setpoint

                """
                if channeldata['type'] == 'remote' and channeldata['enabled']:
                    # Process setpointvalue send for remote here to make it as fast as possible.
                    # First we need to identify the node and channel by retrieving the interface

                    channelname = channeldata['name']
                    utility.log(dirs.logs.control, "Processing remote setpoint for channel " + channelname, 1, loglevels.io)

                    # Then go to the interfaces table to get the node and channel addresses
                    address = dblib.getsinglevalue(dirs.dbs.control, 'interfaces', 'address', condition ="name='" + channelname + "'")
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

                pendingentry = dblib.getsinglevalue(database, table, 'pending', condition=condition)
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


def set_all_wal(wal=True):
    db_paths = [
        dirs.dbs.control,
        dirs.dbs.log,
        dirs.dbs.session,
        dirs.dbs.recipe,
        dirs.dbs.system,
        dirs.dbs.motes,
        dirs.dbs.info,
        dirs.dbs.auths,
        dirs.dbs.notifications,
        dirs.dbs.safe,
        dirs.dbs.users
    ]
    for db_path in db_paths:
        database = cupidDatabase(db_path)
        database.set_wal_mode(wal)


def reload_log_config(**kwargs):
    settings = {'quiet':False}
    settings.update(kwargs)

    logconfig_query_result = dbs.system.read_table_row('logconfig')[0]

    logconfigdata = logconfig_query_result
    loglevels.network = logconfigdata['network']
    loglevels.io = logconfigdata['io']
    loglevels.system = logconfigdata['system']
    loglevels.control = logconfigdata['control']
    loglevels.daemon = logconfigdata['daemon']
    loglevels.serial = logconfigdata['serial']
    loglevels.notifications = logconfigdata['notifications']

    return logconfigdata


def set_debug():
    print('** ENABLING DEBUG MODE **')
    for attr, value in loglevels.__dict__.items():
        setattr(loglevels, attr, 9)

    for db_name in dirs.dbs.__dict__:
        setattr(dbs, db_name, cupidDatabase(getattr(dirs.dbs, db_name), quiet=False))


# On import, Attempt to update from database. If we are unsuccessful, the above are defaults

try:
    logconfig = reload_log_config(quiet=True)
except:
    pass
else:
    for key in logconfig:
        try:
            setattr(loglevels, key, logconfig[key])
        except:
            print ('Set attribute for "' + key + '" did not work')


def getdatameta(database, **kwargs):
    settings = {
        'get_time_span':True
    }
    settings.update(kwargs)

    tablenames = dblib.gettablenames(database)
    if 'metadata' in tablenames:
        tablenames.remove('metadata')
    queryarray = []
    for tablename in tablenames:
        queryarray.append("select count(*) from '" + tablename + "'")
    results = dblib.sqlitemultquery(database, queryarray, **kwargs)['data']
    meta = []
    for result, tablename in zip(results, tablenames):
        this_meta = {}

        this_meta['tablename'] = tablename
        this_meta['numpoints'] = result[0][0]

        # Quick hacky way to know if this is an archive log or not
        if tablename == 'data':
            from os.path import split
            db_name = split(database)[1]
            types = table_name_to_type(db_name)
        else:
            types = table_name_to_type(tablename)

        this_meta['type'] = types['type']
        this_meta['subtype'] = types['subtype']
        this_meta['id'] = types['id']

        if settings['get_time_span']:
            timespan = dblib.gettimespan(database, tablename)['seconds']
            this_meta['timespan'] = timespan

        meta.append(this_meta)
    return meta


def get_and_set_logdb_metadata(database, **kwargs):

    meta = getdatameta(database, **kwargs)

    the_db = dblib.sqliteDatabase(database)
    the_schema = dblib.sqliteTableSchema([
        {'name':'tablename','primary':True},
        {'name':'numpoints','type':'integer'},
        {'name':'timespan','type':'real'},
        {'name':'type'},
        {'name':'subtype'},
        {'name':'id'}
    ])
    the_db.create_table('metadata', the_schema, dropexisting=True, queue=True)
    for meta_item in meta:
        the_db.insert('metadata', {'tablename':meta_item['tablename'], 'numpoints':meta_item['numpoints'],
                                   'timespan':meta_item['timespan'], 'type':meta_item['type'],
                                   'subtype':meta_item['subtype'], 'id':meta_item['id']}, queue=True)
    the_db.execute_queue()
