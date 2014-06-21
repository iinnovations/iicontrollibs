#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import pilib

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


def findprocstatuses(procstofind):
    proc_list = get_proc_list()

    #Show the minimal proc list (user, pid, cmd)

    #stdout.write('Process list:n')
    #print(proc_list)

    procslist = ''
    for proc in proc_list:
        strproc = proc.to_str()
        #stdout.write('t' + strproc + 'n')
        procslist = procslist + strproc
        for proc in procstofind:
            if strproc.count(proc) > 0:
                #print('** found **')
                #print(proc + ' in ')
                #print(strproc)
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

    for index, proc in enumerate(pilib.daemonprocs):
        proc = Popen([pilib.baselibdir + pilib.daemonprocs[index], '&'])


def rundaemon(startall=False):
    from subprocess import Popen, PIPE
    from time import sleep
    from pilib import writedatedlogmsg, daemonlog, daemonloglevel

    # Set up list of enabled statuses (whether to restart if
    # we find that the process is not currently running

    picontrolenabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select picontrolenabled from systemstatus')
    updateioenabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select updateioenabled from systemstatus')
    systemstatusenabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select systemstatusenabled from systemstatus')
    sessioncontrolenabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select sessioncontrolenabled from systemstatus')


    enableditemlist = [(int(updateioenabled)), (int(picontrolenabled)), int(systemstatusenabled), int(sessioncontrolenabled)]

    itemstatuses = findprocstatuses(pilib.daemonprocs)

    # Set system message
    systemstatusmsg = ''
    for name, enabled, status in zip(pilib.daemonprocs, enableditemlist, itemstatuses):
        systemstatusmsg += name + ' - Enabled: ' + str(enabled) + ' Status: ' + str(status) + '. '
        if pilib.daemonloglevel > 0:
            pilib.writedatedlogmsg(pilib.daemonlog, name + ' - Enabled: ' + str(enabled) + ' Status: ' + str(status) + '. ')

    pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'systemmessage', systemstatusmsg)

    # Set up list of itemnames in the systemstatus table that
    # we assign the values to when we detect if the process
    # is running or not

    statustableitemnames = ['updateiostatus', 'picontrolstatus', 'systemstatusstatus', 'sessioncontrolstatus']

    for index, item in enumerate(pilib.daemonprocs):
        # set status
        if itemstatuses[index]:
            pilib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 1')
            if pilib.daemonloglevel > 0:
                pilib.writedatedlogmsg(pilib.daemonlog, 'Process is running: ' + pilib.baselibdir + pilib.daemonprocs[index])
        else:
            pilib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 0')
            if pilib.daemonloglevel > 0:
                pilib.writedatedlogmsg(pilib.daemonlog, 'Process is not running: ' + pilib.baselibdir + pilib.daemonprocs[index])

            # run if set to enable
            if enableditemlist[index]:
                print(pilib.baselibdir + pilib.daemonprocs[index])
                if pilib.daemonloglevel > 0:
                    pilib.writedatedlogmsg(pilib.daemonlog, 'Starting ' + pilib.baselibdir + pilib.daemonprocs[index])
                procresult = Popen([pilib.baselibdir + pilib.daemonprocs[index]], stdout=PIPE)
                # if pilib.daemonloglevel > 0:
                #     pilib.writedatedlogmsg(pilib.daemonproclog, procresult.stdout.read())

    sleep(1)

    # Refresh after set
    itemstatuses = findprocstatuses(pilib.daemonprocs)
    for item in pilib.daemonprocs:
        index = pilib.daemonprocs.index(item)
        # set status
        if itemstatuses[index]:
            pilib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 1')
        else:
            pilib.sqlitequery(pilib.controldatabase, 'update systemstatus set ' + statustableitemnames[index] + ' = 0')

    # Set system message
    systemstatusmsg = ''
    for name, enabled, status in zip(pilib.daemonprocs, enableditemlist, itemstatuses):
        systemstatusmsg += name + ' - Enabled: ' + str(bool(enabled)) + ' Status: ' + str(status) + '. '
    pilib.setsinglevalue(pilib.controldatabase, 'systemstatus','systemmessage', systemstatusmsg)

    # Rotate all logs
    pilib.rotatelogs(pilib.networklog, pilib.numlogs, pilib.maxlogsize)

if __name__ == "__main__":
    from pilib import writedatedlogmsg, daemonlog, daemonloglevel
    writedatedlogmsg(daemonlog, 'Running daemon.',1,daemonloglevel)
    rundaemon()
    writedatedlogmsg(daemonlog, 'Daemon complete.',1,daemonloglevel)