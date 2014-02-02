#!/usr/bin/python

import os,sys
from pilib import sqlitequery
from subprocess import Popen, PIPE
from sys import stdout
from re import split

controldb='/var/www/data/controldata.db'
authdb='/var/www/data/authlog.db'
procspath='/usr/lib/iicontrollibs/cupid/'
procstofind=['periodicreadio.py','picontrol.py','sessioncontrol.py']
debug=False

args=sys.argv
if len(args)>1:
    arg = args[1]
else:
    arg = False

debug=arg

if debug:
    os.system('echo i am running > /home/pi/iamrunning.txt')

# Set up list of enabled statuses (whether to restart if
# we find that the process is not currently running

picontrolenabled=sqlitequery(controldb,'select picontrolenabled from systemstatus')[0][0]
inputsreadenabled=sqlitequery(controldb,'select inputsreadenabled from systemstatus')[0][0]
sessioncontrolenabled=sqlitequery(controldb,'select sessioncontrolenabled from systemstatus')[0][0]

enableditemlist=[(int(inputsreadenabled)),(int(picontrolenabled)), int(sessioncontrolenabled)]

if debug:
    print('picontrolenabled = ' + str(picontrolenabled))
    print('inputsreadenabled = ' + str(inputsreadenabled))
    print(enableditemlist)

# Set up list of itemnames in the systemstatus table that
# we assign the values to when we detect if the process
# is running or not

statustableitemnames=['inputsreadstatus','picontrolstatus','sessioncontrolstatus']

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
        ''' Returns a string containing minimalistic info
        about the process : user, pid, and command '''
        return '%s %s %s' % (self.user, self.pid, self.cmd)

def get_proc_list():
    ''' Return a list [] of Proc objects representing the active
    process list list '''

    proc_list = []
    sub_proc = Popen(['ps', 'aux'], shell=False, stdout=PIPE)

    #Discard the first line (ps aux header)
    sub_proc.stdout.readline()

    for line in sub_proc.stdout:
        #The separator for splitting is 'variable number of spaces'

        proc_info = split(" *", line)
        proc_list.append(Proc(proc_info))
    return proc_list

if __name__ == "__main__":
    proc_list = get_proc_list()

    #Show the minimal proc list (user, pid, cmd)

    #stdout.write('Process list:n')
    #print(proc_list)

    procslist=''
    for proc in proc_list:
        strproc=proc.to_str()
        #stdout.write('t' + strproc + 'n')
        procslist=procslist+strproc
        for proc in procstofind:
            if strproc.count(proc)>0:
                #print('** found **')
                #print(proc + ' in ')
                #print(strproc)
                pass

    #Build &amp; print a list of processes that are owned by root
    #(proc.user == 'root')

    root_proc_list = [ x for x in proc_list if x.user == 'root' ]

    #stdout.write('Owned by root:n')

    for proc in root_proc_list:
        #stdout.write('t' + proc.to_str() + 'n')
        procslist=procslist+proc.to_str()
     
    for item in procstofind:
        index=procstofind.index(item)
        #print(index)
        if procslist.count(item)>0:    # Item was found
	    if debug:
                print(item + ' found')

            # set status in table
            
            sqlitequery(controldb,'update systemstatus set ' + statustableitemnames[index] + '=1')

        else:			    # Item not found
            if debug:
                print(item + ' not found')

            # set status
            sqlitequery(controldb,'update systemstatus set ' + statustableitemnames[index] + ' = 0')

            # run if set to enable
            if enableditemlist[index]:
                if debug:
                    print('enabling ' + item )
                    print(procspath + item + ' &')
                Popen(procspath + item,shell=False)

