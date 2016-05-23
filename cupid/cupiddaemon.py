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
        result = subprocess.check_output(cmd)
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


def findprocstatuses(procstofind):
    import subprocess
    statuses = []
    for proc in procstofind:
        status = False
        try:
            result = subprocess.check_output(['pgrep','-fc',proc])
            print(result)
        except:
            pass
        else:
            if int(result) > 0:
                status = True
        statuses.append(status)
    return statuses

# This thing sucks. See above for trivially simple way to do this.
def deprecatedfindprocstatuses(procstofind):
    proc_list = get_proc_list()

    #Show the minimal proc list (user, pid, cmd)

    #stdout.write('Process list:n')
    #  print(proc_list)

    procslist = ''
    for proc in proc_list:
        strproc = proc.to_str()
        # stdout.write('t' + strproc + 'n')
        print(strproc + '\n')
        procslist = procslist + strproc
        for proc in procstofind:
            if strproc.count(proc) > 0:
                print('** found **')
                print(proc + ' in ')
                print(strproc)
                pass

    #Build &amp; print a list of processes that are owned by root
    #(proc.user == 'root')

    root_proc_list = [x for x in proc_list if x.user == 'root']

    #stdout.write('Owned by root:n')

    for proc in root_proc_list:
        #stdout.write('t' + proc.to_str() + 'n')
        procslist = procslist + proc.to_str()

    foundstatuses = []
    for item in procstofind:
        index = procstofind.index(item)
        #print(index)
        if procslist.count(item) > 0:  # Item was found
            foundstatuses.append(True)
        else:
            foundstatuses.append(False)

    return foundstatuses


def runallprocs():
    from subprocess import Popen, PIPE
    from cupid import pilib
    for index, proc in enumerate(pilib.daemonprocs):
        proc = Popen([pilib.baselibdir + pilib.daemonprocs[index], '&'])


def rundaemon(startall=False):
    from subprocess import Popen, PIPE
    from time import sleep
    from utilities import datalib, dblib, utility
    from cupid import pilib

    # Set up list of enabled statuses (whether to restart if
    # we find that the process is not currently running

    picontrolenabled = dblib.sqlitedatumquery(pilib.controldatabase, 'select picontrolenabled from systemstatus')
    updateioenabled = dblib.sqlitedatumquery(pilib.controldatabase, 'select updateioenabled from systemstatus')
    systemstatusenabled = dblib.sqlitedatumquery(pilib.controldatabase, 'select systemstatusenabled from systemstatus')
    sessioncontrolenabled = dblib.sqlitedatumquery(pilib.controldatabase, 'select sessioncontrolenabled from systemstatus')
    serialhandlerenabled = dblib.sqlitedatumquery(pilib.controldatabase, 'select serialhandlerenabled from systemstatus')

    enableditemlist = [(int(updateioenabled)), (int(picontrolenabled)), int(systemstatusenabled), int(sessioncontrolenabled), int(serialhandlerenabled)]

    itemstatuses = findprocstatuses(pilib.daemonprocs)

    if enableditemlist[2] and itemstatuses[2]:
        # Here we check to see if things are running properly and not hung
        lastsystemstatus =dblib.getsinglevalue(pilib.controldatabase, 'systemstatus', 'lastsystemstatuspoll')
        currenttime = datalib.gettimestring()
        timesincelastsystemstatus = datalib.timestringtoseconds(currenttime)- datalib.timestringtoseconds(lastsystemstatus)

        timecriterion = 90
        if timesincelastsystemstatus > timecriterion:
            utility.log(pilib.syslog, 'Killing systemstatus because it has not run in ' + str(timesincelastsystemstatus) + 's')
            # Queue a message indicating we had to restart the systemstatus daemon
            message = 'Systemstatus is being killed because it has not run in ' + str(timesincelastsystemstatus) + 's with a criteria of ' +  \
                str(timecriterion) + '. This occurred at ' + currenttime

            dblib.sqliteinsertsingle(pilib.notificationsdatabase, 'queuednotifications', \
                                     ['email', message, 'email:colin.reese@gmail.com', currenttime], \
                                     ['type', 'message', 'options', 'queuedtime'])

            utility.killprocbyname('systemstatus')



    # Set system message
    systemstatusmsg = ''
    for name, enabled, status in zip(pilib.daemonprocs, enableditemlist, itemstatuses):
        systemstatusmsg += name + ' - Enabled: ' + str(enabled) + ' Status: ' + str(status) + '. '
        if pilib.daemonloglevel > 0:
            utility.log(pilib.daemonlog, name + ' - Enabled: ' + str(enabled) + ' Status: ' + str(status) + '. ')

    dblib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'systemmessage', systemstatusmsg)

    # Set up list of itemnames in the systemstatus table that
    # we assign the values to when we detect if the process
    # is running or not

    statustableitemnames = ['updateiostatus', 'picontrolstatus', 'systemstatusstatus', 'sessioncontrolstatus', 'serialhandlerstatus']

    for index, item in enumerate(pilib.daemonprocs):
        # set status
        if itemstatuses[index]:
            dblib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 1')
            if pilib.daemonloglevel > 0:
                utility.log(pilib.daemonlog, 'Process is running: ' + pilib.baselibdir + pilib.daemonprocs[index])
        else:
            dblib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 0')
            if pilib.daemonloglevel > 0:
                utility.log(pilib.daemonlog, 'Process is not running: ' + pilib.baselibdir + pilib.daemonprocs[index])

            # run if set to enable
            if enableditemlist[index]:
                # print(pilib.baselibdir + pilib.daemonprocs[index])
                if pilib.daemonloglevel > 0:
                    utility.log(pilib.daemonlog, 'Starting ' + pilib.baselibdir + pilib.daemonprocs[index])
                procresult = Popen([pilib.baselibdir + pilib.daemonprocs[index]], stdout=PIPE, stderr=PIPE)
                # if pilib.daemonloglevel > 0:
                #     pilib.writedatedlogmsg(pilib.daemonproclog, procresult.stdout.read())

    sleep(1)

    # Refresh after set
    itemstatuses = findprocstatuses(pilib.daemonprocs)
    for item in pilib.daemonprocs:
        index = pilib.daemonprocs.index(item)
        # set status
        if itemstatuses[index]:
            dblib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 1')
        else:
            dblib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 0')

    # Set system message
    systemstatusmsg = ''
    for name, enabled, status in zip(pilib.daemonprocs, enableditemlist, itemstatuses):
        systemstatusmsg += name + ' - Enabled: ' + str(bool(enabled)) + ' Status: ' + str(status) + '. '
    dblib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'systemmessage', systemstatusmsg)

    # Rotate all logs
    pilib.rotatelogs(pilib.networklog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.syslog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.iolog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.controllog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.daemonlog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.seriallog, pilib.numlogs, pilib.maxlogsize)
    pilib.rotatelogs(pilib.notificationslog, pilib.numlogs, pilib.maxlogsize)

if __name__ == "__main__":
    from pilib import daemonlog, daemonloglevel
    from utilities.utility import log

    log(daemonlog, 'Running daemon.', 1, daemonloglevel)
    rundaemon()
    log(daemonlog, 'Daemon complete.',1,daemonloglevel)