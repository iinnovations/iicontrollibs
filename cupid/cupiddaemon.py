#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


class Proc(object):
    ''' Data structure for a processes . The class properties are
    process attributes '''

    def __init__(self, proc_info):
        self.user = proc_info[0]
        self.pid = proc_info[1]
        self.cpu = proc_info[2]
        self.mem = proc_info[3]
        self.vsz = proc_info[4]
        self.rss = proc_info[5]
        self.tty = proc_info[6]
        self.stat = proc_info[7]
        self.start = proc_info[8]
        self.time = proc_info[9]
        if len(proc_info) > 11:
            self.cmd = proc_info[10] + ' ' + proc_info[11]
        else:
            self.cmd = proc_info[10]

    def to_str(self):
        """ Returns a string containing minimalistic info
        about the process : user, pid, and command """
        return '%s %s %s' % (self.user, self.pid, self.cmd)


def get_proc_list():
    """ Return a list [] of Proc objects representing the active
    process list list """

    from subprocess import Popen, PIPE
    from re import split

    proc_list = []
    sub_proc = Popen(['ps', 'aux'], shell=False, stdout=PIPE)

    #Discard the first line (ps aux header)
    sub_proc.stdout.readline()

    for line in sub_proc.stdout:
        #The separator for splitting is 'variable number of spaces'

        proc_info = split(" *", line)
        proc_list.append(Proc(proc_info))
    return proc_list


def pgrepstatus(regex, full=True):
    import subprocess
    if full:
        cmd = ['pgrep','-f',regex]
    else:
        cmd = ['pgrep',regex]
    try:
        result = subprocess.check_output(cmd).decode('utf-8')
    except:
        pcount = 0
        pids = []
    else:
        split = result.split('\n')
        # print(split)
        pcount = 0
        pids = []
        for pid in split:
            if pid:
                pcount += 1
                pids.append(pid)
    return {'count': pcount, 'pids': pids}


# This is in utilities, but we include it here in case we cannot import other things
class gmail:
    def __init__(self, server='smtp.gmail.com', port=587, subject='default subject', message='default message',
                 login='cupidmailer@interfaceinnovations.org', password='cupidmail', recipient='cupid_status@interfaceinnovations.org', sender='CuPID Mailer'):
        self.server = server
        self.port = port
        self.message = message
        self.subject = subject
        self.sender = sender
        self.login = login
        self.password = password
        self.recipient = recipient
        self.sender = sender

    def send(self):
        import smtplib

        headers = ['From:' + self.sender,
                  'Subject:' + self.subject,
                  'To:' + self.recipient,
                  'MIME-Version: 1.0',
                  'Content-Type: text/plain']
        headers = '\r\n'.join(headers)

        session = smtplib.SMTP(self.server, self.port)

        session.ehlo()
        session.starttls()
        session.login(self.login, self.password)

        session.sendmail(self.sender, self.recipient, headers + '\r\n\r\n' + self.message)
        session.quit()


def runallprocs():
    import subprocess

    # TODO: Convert this to threading.
    # import threading
    from cupid import pilib
    FNULL = open(os.devnull, 'w')

    for index, proc in enumerate(pilib.daemonprocs):
        full_process_name = pilib.dirs.baselib + pilib.daemonprocs[index]

        subprocess.call([full_process_name, '&'], stdout=FNULL, stderr=FNULL)
        # proc = Popen([pilib.dirs.baselib + pilib.daemonprocs[index], '&'])

        # thread = threading.Thread(target=self.run, args=())
        # thread.daemon = True  # Daemonize thread
        # thread.start()


def rundaemon(**kwargs):

    """
    First thing we are going to do is check to see if code is working. We do this first to minimize what we have to
    import to test this -- the script should not crash out before we do this.

    So we need dblib to function to read from the database to see whether we are going to email someone if things are
    broken.
    We need datalib to parse options on the notifications
    We also need utility to send an email
    """
    settings = {'startall':False, 'debug':False}
    settings.update(kwargs)


    try:
        import socket
        hostname = socket.gethostname()
    except:
        hostname = 'unknown (?!)'

    import importlib

    testmodules = ['iiutilities.dblib', 'iiutilities.utility', 'iiutilities.datalib', 'cupid.pilib']

    # these are the libraries we will need to send notifications that things aren't working.
    # To do this, however, we need some libraries.
    failures = ''
    for testmodule in testmodules:
        try:
            tempmodule = importlib.import_module(testmodule)
        except:
            failures += testmodule + ', '
    if failures:
        # Send an email to indicate that things are horribly broken
        subject = 'Hostname: ' + hostname + ' things are broken.'
        message = 'Test import of module(s) ' + failures[:-2] + ' failed. '
        em_gmail = gmail(subject=subject, message=message)
        em_gmail.send()

    from iiutilities import dblib, utility, datalib
    from cupid import pilib
    if settings['debug']:
        print('** DEBUG MODE ** ')
        pilib.set_debug()

    import cupidunittests
    unittestresults = cupidunittests.runalltests()

    # Get notifications so we know when to notify
    system_database = pilib.cupidDatabase(pilib.dirs.dbs.system)
    notification_database = pilib.cupidDatabase(pilib.dirs.dbs.notifications)

    notifications = system_database.read_table('notifications')

    # print('** Unit TEST RESULTS ** ')
    # print(unittestresults['totalerrorcount'],unittestresults['totalfailurecount'])
    if unittestresults['totalerrorcount'] > 0 or unittestresults['totalfailurecount'] > 0:
        unitnotify = next((item for item in notifications if item['item'] == 'unittests' and int(item['enabled'])), None)

        if unitnotify:
            options = datalib.parseoptions(unitnotify['options'])
            if 'type' in options:
                if options['type'] == 'email' and 'email' in options:
                    currenttime = datalib.gettimestring()
                    lastnotificationtime = unitnotify['lastnotification']
                    # default
                    frequency = 600
                    if 'frequency' in options:
                        try:
                            frequency = float(options['frequency'])
                        except:
                            pass

                    elapsedtime = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(lastnotificationtime)
                    # print(elapsedtime,frequency)
                    if elapsedtime > frequency:

                        # Queue a message indicating we had to restart the systemstatus daemon
                        message = 'CuPID has failed unittests. Details follow:\r\n\r\n'
                        message += unittestresults['stringresult'].replace('\'','"')
                        # message += '\r\n\r\n'
                        # message +=

                        subject = 'CuPID : ' + hostname + ' : unittests'
                        notification_database.insert('queuednotifications',
                                                     {'type':'email','message':message,
                                                      'options':'email:' + options['email'] + ',subject:' + subject,
                                                      'queuedtime':currenttime})
                        system_database.set_single_value('notifications','lastnotification',currenttime, "item='unittests'")

    from subprocess import Popen, PIPE
    from time import sleep

    """
    Set up list of enabled statuses (whether to restart if
    we find that the process is not currently running
    from iiutilities import dblib, utility, datalib
    """

    system_status_options = system_database.read_table_row('systemstatus')[0]
    # print('systemstatusoptions')
    # print(system_status_options)

    item_enabled_dict = {'updateio':int(system_status_options['updateioenabled']),
                         'picontrol':int(system_status_options['picontrolenabled']),
                         'systemstatus':int(system_status_options['systemstatusenabled']),
                         'sessioncontrol':int(system_status_options['sessioncontrolenabled']),
                         'serialhandler':int(system_status_options['serialhandlerenabled'])
                         }

    # updateio_enabled = int(system_status_options['updateioenabled'])
    # picontrol_enabled = int(system_status_options['picontrolenabled'])
    # systemstatus_enabled = int(system_status_options['systemstatusenabled'])
    # sessioncontrol_enabled = int(system_status_options['sessioncontrolenabled'])
    # serialhandler_enabled =int( system_status_options['serialhandlerenabled'])

    # enableditemlist = [(int(updateio_enabled)), (int(picontrolenabled)), int(systemstatusenabled), int(sessioncontrolenabled), int(serialhandlerenabled)]

    # These are hard-coded and must match up for now. This should be cleaned up to be more easily modified.
    itemstatuses = utility.findprocstatuses(pilib.daemonprocs)

    item_status_dict = {}
    for name, status in zip(pilib.daemonprocnames, itemstatuses):
        item_status_dict[name] = status

    """
    Here we check to see if things are running properly and not hung. First here is systemstatus
    """

    if item_enabled_dict['systemstatus'] and item_status_dict['systemstatus']:
        lastsystemstatus = dblib.getsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastsystemstatuspoll')
        currenttime = datalib.gettimestring()
        timesincelastsystemstatus = datalib.timestringtoseconds(currenttime)- datalib.timestringtoseconds(lastsystemstatus)

        timecriterion = 90
        if timesincelastsystemstatus > timecriterion:
            utility.log(pilib.dirs.logs.system, 'Killing systemstatus because it has not run in ' + str(timesincelastsystemstatus) + 's')

            killnotify = next((item for item in notifications if item['item'] == 'daemonkillproc' and int(item['enabled'])), None)
            if killnotify:
                options = datalib.parseoptions(killnotify['options'])
                if 'type' in options:
                    if 'type' == 'email' and 'email' in options:
                        # Queue a message indicating we had to restart the systemstatus daemon
                        message = 'Systemstatus is being killed on ' + hostname + ' because it has not run in ' + \
                            str(timesincelastsystemstatus) + 's with a criteria of ' +  \
                            str(timecriterion) + '. This occurred at ' + currenttime
                        subject = 'CuPID : ' + hostname + ' : killnotify'
                        notification_database.insert('queuednotifications',
                                                     {'type': 'email', 'message': message,
                                                      'options': 'email:' + options['email'] + ',subject:' + subject,
                                                      'queuedtime': currenttime})

            utility.killprocbyname('systemstatus')


    # Set system message
    systemstatusmsg = ''
    for name in pilib.daemonprocnames:
        systemincmessage = name + ' - Enabled: ' + str(item_enabled_dict[name]) + ' Status: ' + str(item_status_dict[name]) + '. '
        systemstatusmsg += systemincmessage
        if pilib.loglevels.daemon > 0:
            utility.log(pilib.dirs.logs.daemon, 'Item status message: ' + systemincmessage)

    system_database.set_single_value('systemstatus', 'systemmessage', systemstatusmsg)

    # Set up list of itemnames in the systemstatus table that
    # we assign the values to when we detect if the process
    # is running or not

    for name, process in zip(pilib.daemonprocnames, pilib.daemonprocs):

        # set status
        if item_status_dict[name]:
            # Set status variable by name. This is static based on schema
            system_database.set_single_value('systemstatus', name + 'status', 1)
            if pilib.loglevels.daemon > 0:
                utility.log(pilib.dirs.logs.daemon, 'Process is running: ' + pilib.dirs.baselib + process, 4, pilib.loglevels.daemon)
        else:
            system_database.set_single_value('systemstatus', name + 'status', 0)
            if pilib.loglevels.daemon > 0:
                utility.log(pilib.dirs.logs.daemon, 'Process is not running: ' + pilib.dirs.baselib + process, 2, pilib.loglevels.daemon)

            # run if set to enable
            if item_enabled_dict[name]:
                # print(pilib.dirs.baselib + pilib.daemonprocs[index])
                if pilib.loglevels.daemon > 0:
                    utility.log(pilib.dirs.logs.daemon, 'Starting ' + pilib.dirs.baselib + process, 2, pilib.loglevels.daemon)
                procresult = Popen([pilib.dirs.baselib + process], stdout=PIPE, stderr=PIPE)
                # if pilib.loglevels.daemon > 0:
                #     pilib.writedatedlogmsg(pilib.dirs.logs.daemonproc, procresult.stdout.read())

    # Why is this here?
    sleep(3)

    # Refresh after set
    itemstatuses = utility.findprocstatuses(pilib.daemonprocs)
    item_status_dict = {}
    for name, status in zip(pilib.daemonprocnames, itemstatuses):
        item_status_dict[name] = status

    for name in pilib.daemonprocnames:
        # set status
        if item_status_dict[name]:
            system_database.set_single_value('systemstatus', name + 'status', 1)
        else:
            system_database.set_single_value('systemstatus', name + 'status', 0)

    """
    Process Actions.
    Careful here. This does not carry out things like indicators, which are set from picontrol. A bit wonky, as we
    would like the indicators to update immediately. On the other hand, we want picontrol to be the master controller
    of IO.
    """

    from cupid.actions import processactions
    processactions()

    systemstatusmsg = ''
    for name in pilib.daemonprocnames:
        systemincmessage = name + ' - Enabled: ' + str(item_enabled_dict[name]) + ' Status: ' + str(
            item_status_dict[name]) + '. '
        systemstatusmsg += systemincmessage
        if pilib.loglevels.daemon > 0:
            utility.log(pilib.dirs.logs.daemon, 'Item status message: ' + systemincmessage)

    system_database.set_single_value('systemstatus', 'systemmessage', systemstatusmsg)

    # Rotate all logs
    for attr, value in pilib.dirs.logs.__dict__.items():
        utility.rotate_log_by_size(value, pilib.numlogs, pilib.maxlogsize)

if __name__ == "__main__":

    try:
        from cupid.pilib import dirs, loglevels
    except:
        print('error importing pilib components')

    try:
        from iiutilities.utility import log, findprocstatuses
    except:
        print('error importing utility components')
    else:
        log(dirs.logs.daemon, 'Running daemon.', 1, loglevels.daemon)

    # This will pick up errors above. We handle above so we can warn in unittests
    # rundaemon(debug=True)
    rundaemon()

    log(dirs.logs.daemon, 'Daemon complete.',1,loglevels.daemon)

