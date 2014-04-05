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
import netconfig

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


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
    # print(pingtimes)
    return pingtimes

def updateifacestatus():

    import resource.pyiface.iface as pyiface
    from cupid.pilib import sqlitemultquery, setsinglevalue, systemdatadatabase, readonedbrow, gettimestring
    import subprocess

    netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
    netstatus = readonedbrow(systemdatadatabase, 'netstatus')[0]
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
    # WAN check

    okping = float(netconfigdata['pingthreshold'])
    pingresults = runping('8.8.8.8')
    pingresult = sum(pingresults)/float(len(pingresults))
    if pingresult == 0:
        wanaccess = 0
        latency = 0
    else:
        if pingresult < okping:
            wanaccess = 1
        else:
            wanaccess = 0
        latency = pingresult
    setsinglevalue(systemdatadatabase, 'netstatus', 'latency', str(latency))

    # Check supplicant status, set on/offtime if necessary.
    wpastatusdict = netconfig.getwpaclientstatus()
    if wpastatusdict['wpa_state'] == 'COMPLETED':
        wpaconnected = 1
        if netstatus['connected'] == 0 or netstatus['onlinetime'] == '':
            setsinglevalue(systemdatadatabase, 'netstatus', 'onlinetime', gettimestring())
            setsinglevalue(systemdatadatabase, 'netstatus', 'offlinetime', '')
    else:
        wpaconnected = 0
        if netstatus['connected'] == 1 or netstatus['offlinetime'] == '':
            setsinglevalue(systemdatadatabase, 'netstatus', 'offlinetime', gettimestring())
            setsinglevalue(systemdatadatabase, 'netstatus', 'onlinetime', '')

    # Check dhcp server status
    result = subprocess.Popen(['service','isc-dhcp-server','status'], stdout=subprocess.PIPE)
    for line in result.stdout:
        if line.find('not running') > 0:
            dhcpstatus = 0
        elif line.find('is running') > 0:
            dhcpstatus = 1
        else:
            dhcpstatus = '\?'

    wpastatusdict['dhcptatus'] = str(dhcpstatus)
    wpastatusdict['connected'] = wpaconnected

    # This is not the most efficient way to do this. Laziness...
    setsinglevalue(systemdatadatabase, 'netstatus', 'dhcpstatus', str(dhcpstatus))
    setsinglevalue(systemdatadatabase, 'netstatus', 'connected', str(wpaconnected))
    setsinglevalue(systemdatadatabase, 'netstatus', 'mode', wpastatusdict['mode'])
    setsinglevalue(systemdatadatabase, 'netstatus', 'networkSSID', wpastatusdict['ssid'])
    setsinglevalue(systemdatadatabase, 'netstatus', 'WANaccess', str(wanaccess))
    setsinglevalue(systemdatadatabase, 'netstatus', 'IPAddress', wpastatusdict['ip_address'])

    return wpastatusdict


if __name__ == '__main__':
    wpastatusdict = updateifacestatus()
    import pilib
    netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
    netstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]

    # If not connected

    # If mode is temprevert, set to apmode, but don't update config
    # If mode is aprevert, set to apmode and update netconfig
    if not wpastatusdict['connected']:
        currenttime = pilib.gettimestring()
        if pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(netstatus['offtime']) > pilib.timestringtoseconds(netconfigdata['apreverttime']):
            if netconfigdata['aprevert'] == 'temprevert' or netconfigdata['temprevert'] == 'aprevert':
                netconfig.setapmode()

            # set mode to ap if 'permanent' revet
            if netconfigdata['aprevert'] == 'aprevert':
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'ap')

    suppconfig = netconfig.getwpasupplicantconfig()



