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
import netconfig


def readhardwarefileintoversions():
    from pilib import systemdatadatabase, makesqliteinsert, sqlitequery
    devicefile = '/var/wwwsafe/devicedata'
    file = open(devicefile)
    lines = file.readlines()
    devicedict={}
    for line in lines:
        split = line.split(':')
        try:
            devicedict[split[0].strip()] = split[1].strip()
        except:
            print('parse error')
    sqlitequery(systemdatadatabase, makesqliteinsert('versions', ['hardware',devicedict['hardware']], ['item', 'version']))


def runping(pingAddress,numpings=1):
    pingtimes=[]
    for i in range(numpings):
        # Perform the ping using the system ping command (one ping only)
        try:
            rawPingFile = os.popen('ping -c 1 %s' % (pingAddress))
        except:
            failed = True
            latency = 0
        else:
            # Extract the ping time
            rawPingData = rawPingFile.readlines()
            rawPingFile.close()
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
            pingtimes.append(0)
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
    # pingresults = [20, 20, 20]
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
    querylist.append(pilib.makesinglevaluequery('netstatus', 'latency', str(latency)))

    # Check supplicant status, set on/offtime if necessary.
    wpastatusdict = netconfig.getwpaclientstatus()
    try:
        if wpastatusdict['wpa_state'] == 'COMPLETED':
            wpaconnected = 1
            if netstatus['connected'] == 0 or netstatus['onlinetime'] == '':
                print('setting online time')
                querylist.append(pilib.makesinglevaluequery('netstatus', 'onlinetime', gettimestring()))
                querylist.append(pilib.makesinglevaluequery('netstatus', 'offlinetime', ''))
        else:
            wpaconnected = 0
    except KeyError:
        wpaconnected = 0

    if wpaconnected == 0:
        if netstatus['connected'] == 1 or netstatus['offlinetime'] == '':
            if netconfigdata['mode'] == "station":
                print('setting offline time')
                querylist.append(pilib.makesinglevaluequery('netstatus', 'offlinetime', gettimestring()))
                querylist.append(pilib.makesinglevaluequery('netstatus', 'onlinetime', ''))
            else:
                print('erasing offline time')
                querylist.append(pilib.makesinglevaluequery('netstatus', 'offlinetime', ''))

    # Check dhcp server status
    result = subprocess.Popen(['service', 'isc-dhcp-server', 'status'], stdout=subprocess.PIPE)
    for line in result.stdout:
        if line.find('not running') > 0:
            dhcpstatus = 0
        elif line.find('is running') > 0:
            dhcpstatus = 1
        else:
            dhcpstatus = '\?'

    wpastatusdict['connected'] = wpaconnected
    try:
        wpastatusdict['dhcpstatus'] = dhcpstatus
    except:
        wpastatusdict['dhcpstatus'] = 0
        dhcpstatus = 0
    try:
        mode = wpastatusdict['mode']
    except KeyError:
        mode = 'none'
    try:
        ssid = wpastatusdict['ssid']
    except KeyError:
        ssid = 'none'
    try:
        address = wpastatusdict['ip_address']
    except KeyError:
        address = 'none'

    # print('myaddress is ' + address)
    querylist.append(pilib.makesinglevaluequery('netstatus', 'dhcpstatus', dhcpstatus))
    querylist.append(pilib.makesinglevaluequery('netstatus', 'connected', str(wpaconnected)))
    if netconfigdata['mode'] in ['ap','tempap']:
        print('setting apmode netstatus')
        querylist.append(pilib.makesinglevaluequery('netstatus', 'mode', netconfigdata['mode']))
        querylist.append(pilib.makesinglevaluequery('netstatus', 'SSID', 'cupidwifi'))
    else:
        print('setting station mode netstatus')
        querylist.append(pilib.makesinglevaluequery('netstatus', 'mode', str(mode)))
        querylist.append(pilib.makesinglevaluequery('netstatus', 'SSID', str(ssid)))
    querylist.append(pilib.makesinglevaluequery('netstatus', 'WANaccess', str(wanaccess)))
    querylist.append(pilib.makesinglevaluequery('netstatus', 'address', str(address)))

    pilib.sqlitemultquery(pilib.systemdatadatabase, querylist)
    return wpastatusdict


def processsystemflags(systemflags=None):
    if not systemflags:
        systemflags = pilib.readalldbrows(pilib.systemdatadatabase, 'systemflags')

    flagnames = []
    flagvalues = []
    for flag in systemflags:
        flagnames.append(flag['name'])
        flagvalues.append(flag['value'])

    stop = False
    if 'reboot' in flagnames:
        if flagvalues[flagnames.index('reboot')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, "name='reboot'")
            import subprocess
            print('i reboot here')
            subprocess.call(['reboot'])
    if 'netconfig' in flagnames:
        if flagvalues[flagnames.index('netconfig')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, "name='netconfig'")
            from netconfig import runconfig
            print('restarting network configuration')
            runconfig()
    if 'updateiicontrollibs' in flagnames and not stop:
        if flagvalues[flagnames.index('updateiicontrollibs')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, 'name=\'updateiicontrollibs\'')
            from misc.gitupdatelib import updateiicontrollibs
            print('updating iicontrollibs')
            updateiicontrollibs(True)
    if 'updatecupidweblib' in flagnames and not stop:
        if flagvalues[flagnames.index('updatecupidweblib')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, 'name=\'updatecupidweblib\'')
            from misc.gitupdatelib import updatecupidweblib
            print('updating cupidweblib')
            updatecupidweblib(True)


def writenetlog(message):
    logfile = open(pilib.netstatuslog, 'a')
    logfile.writelines([message])
    logfile.close()


if __name__ == '__main__':

    import pilib
    import time
    from misc.gitupdatelib import updategitversions

    updategitversions()

    systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

    # Keep reading and updating system status?
    while systemstatus['systemstatusenabled']:

        # print('starting')
        currenttime = pilib.gettimestring()
        pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'lastsystemstatuspoll', pilib.gettimestring())

        # Update network interfaces statuses for all interfaces, in database tables as well
        # Check on wpa supplicant status as well. Function returns wpastatusdict

        wpastatusdict = updateifacestatus()
        netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
        netstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]

        wpastatusmsg = ''
        # If mode is ap or tempap
        if netconfigdata['mode'] in ['ap', 'tempap']:
            timesincelastretry = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(netconfigdata['laststationretry'])
            # If it's time to go back to station mode, we don't care whether we are connected as ap or not
            # We use dhcp status as indicator of ap status. Imperfect, but functional.
            if netconfigdata['mode'] == 'tempap' and timesincelastretry > netconfigdata['stationretrytime']:
                # We go back to station mode
                wpastatusmsg += 'Time to go back to station mode. '
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'station')
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'laststationretry', '')
                netconfig.runconfig()
            else:
                # If we have ap up, do nothing
                if wpastatusdict['dhcpstatus']:
                    print(wpastatusdict['dhcpstatus'])
                    wpastatusmsg += 'AP checked and ok. '
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'mode', 'ap')
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'SSID', 'cupidwifi')
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'offlinetime', '')


                # If we don't have dhcp up, restart ap mode
                # this will currently cause reboot if we don't set onboot=True
                # We set status message in case we change our minds and reboot here.
                else:
                    print('status is zero')
                    wpastatusmsg += 'Restarting AP. '
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', wpastatusmsg)
                    netconfig.runconfig()

        # If mode is station
        elif netconfigdata['mode'] == 'station':
            # If we have wpa up, do nothing
            if netstatus['connected']:
                wpastatusmsg += 'Station wpamode appears ok. '

            # If wpa is not connected
            else:
                wpastatusmsg += 'Station wpamode appears disconnected. '
                if netstatus['offlinetime'] == '':
                    pilib.setsinglevalue('netstatus', 'offlinetime', pilib.gettimestring())
                    offlinetime = 0
                else:
                    offlinetime = pilib.timestringtoseconds(currenttime)-pilib.timestringtoseconds(netstatus['offlinetime'])
                wpastatusmsg += 'we have been offline for ' + str(offlinetime) + '. '
                # If aprevert is aprevert or temprevert and we've been offline long enough, flip over to ap
                if netconfigdata['aprevert'] in ['temprevert', 'aprevert'] and offlinetime > netconfigdata['apreverttime']:

                    # set laststationretry to currenttime
                    wpastatusmsg += 'Setting last station retry time. '
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'laststationretry', currenttime)
                    if netconfigdata['aprevert'] == 'aprevert':
                        # set mode to ap
                        wpastatusmsg += 'Setting mode to ap. '
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'ap')
                    elif netconfigdata['aprevert'] == 'temprevert':
                        # set mode to tempap
                        wpastatusmsg += 'Setting mode to tempap. '
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'tempap')

                    # Unfortunately, to revert to ap mode successfully, we currently have to reboot
                    # this is built into the netconfig script - any time you set ap mode except at boot, it reboots
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', wpastatusmsg)
                    wpastatusmsg += 'Rebooting on wpaset ap mode. '
                    print(wpastatusmsg)
                    writenetlog(wpastatusmsg)
                    netconfig.runconfig()
        else:
            wpastatusmsg += 'mode error: ' + netconfigdata['mode']

        writenetlog(pilib.gettimestring() + wpastatusmsg)

        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', wpastatusmsg)

        print(wpastatusmsg)

        updateifacestatus()

        processsystemflags()

        # Get system status again
        systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

        # print('Status routine took ' + str(time.time()-starttime))
        time.sleep(systemstatus['systemstatusfreq'])
