#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# do this stuff to access stuff in other directories
import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

def getwpasupplicantdata(conffile='/etc/wpa_supplicant/wpa_supplicant.conf'):
    class data():
        pass

    file = open(conffile)
    lines = file.readlines()
    header=''
    tail=''
    datalines=[]
    readheader=True
    readbody=False
    readtail=False
    for line in lines:
        if readheader:
            header = header + line
        if '}' in line:
            print('parsing ended')
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            print('starting parse')
            readheader = False
            readbody = True

    datadict={}
    for line in datalines:
        split = line.split('=')
        datadict[split[0].strip()] = split[1].strip()

    returndict = data()
    returndict.header = header
    returndict.tail = tail
    returndict.data = datadict
    return returndict

def writesupplicantfile(filepath,filedata):
    writestring=''
    writestring += filedata.header
    for key,value in filedata.data.items():
        writestring += key + '=' + value + '\n'
    writestring += filedata.tail
    myfile = open(filepath,'w')
    myfile.write(writestring)

def runping(pingAddress,numpings=1):
    pingtimes=[]
    for i in range(numpings):
        # Perform the ping using the system ping command (one ping only)
        rawPingFile = os.popen('ping -c 1 %s' % (pingAddress))
        rawPingData = rawPingFile.readlines()
        rawPingFile.close()
        # Extract the ping time
        if len(rawPingData) < 2:
            # Failed to find a DNS resolution or route
            failed = True
            latency = 0
        else:
            index = rawPingData[1].find('time=')
            if index == -1:
                # Ping failed or timed-out
                failed = True
                latency = 0
            else:
                # We have a ping time, isolate it and convert to a number
                failed = False
                latency = rawPingData[1][index + 5:]
                latency = latency[:latency.find(' ')]
                latency = float(latency)
        # Set our outputs
        if failed:
            # Could not ping
            pingtimes.append[-1]
        else:
            # Ping stored in latency in milliseconds
            #print '%f ms' % (latency)
            pingtimes.append(latency)
    return pingtimes

def updateifacestatus():

    import resource.pyiface.iface as pyiface
    from cupid.pilib import sqlitemultquery, setsinglevalue, systemdatadatabase
    import subprocess

    # Networking check

    querylist = []
    table = 'netifaces'
    querylist.append('drop table if exists ' + table)
    querylist.append(
        "create table " + table + " (name text, hwaddr text, address text, ifaceindex integer, bcast text, mask text, flags text)")

    allIfaces = pyiface.getIfaces()
    for iface in allIfaces:
        querylist.append(
            "insert into " + table + " values ( \'" + iface.name + "\' , \'" + iface.hwaddr + "\' , \'" + iface._Interface__sockaddrToStr(
                iface.addr) + "\' , \'" + str(iface.index) + "\' , \'" + iface._Interface__sockaddrToStr(
                iface.broadaddr) + "\' , \'" + iface._Interface__sockaddrToStr(
                iface.netmask) + "\' , \'" + pyiface.flagsToStr(iface.flags) + "\')")
        #print(querylist)
        sqlitemultquery(systemdatadatabase, querylist)


    # Interfaces check
    pingresult = runping('8.8.8.8')
    if pingresult == 0:
        wanaccess = 0
        latency = 0
    else:
        wanaccess = 0
        latency = pingresult

    # Check supplicant configuration
    wpaconfig = getwpasupplicantdata()
    print(wpaconfig.data)
    print(wpaconfig.data['ssid'])
    setsinglevalue(systemdatadatabase, 'netstatus', 'networkSSID', '\"' + wpaconfig.data['ssid'] + '\"')
    setsinglevalue(systemdatadatabase, 'netstatus', 'WANaccess', str(wanaccess))


# Other stuff