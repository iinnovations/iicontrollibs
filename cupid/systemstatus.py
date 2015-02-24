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
    import pilib

    devicefile = '/var/wwwsafe/devicedata'
    try:
        file = open(devicefile)
        lines = file.readlines()
        devicedict = {}
        for line in lines:
            split = line.split(':')
            try:
                devicedict[split[0].strip()] = split[1].strip()
            except:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Device data parse error', 1, pilib.systemstatusloglevel)
        pilib.sqlitequery(pilib.systemdatadatabase,
                          pilib.makesqliteinsert('versions', ['hardware', devicedict['hardware']], ['item', 'version']))
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Cannot find devicedata file to parse', 1,
                               pilib.systemstatusloglevel)


def updateiwstatus():
    from pilib import insertstringdicttablelist, systemdatadatabase,gettimestring
    import netfun
    iwdict = netfun.getiwstatus()
    iwdict['updatetime'] = gettimestring()

    # put into database
    insertstringdicttablelist(systemdatadatabase, 'iwstatus', [iwdict])


def updatehamachistatus():
    from pilib import insertstringdicttablelist, systemdatadatabase, gettimestring
    import netfun
    try:
        hamdicts = netfun.gethamachidata()
    except:
        pass
    else:
        for index, dict in enumerate(hamdicts):
            hamdicts[index]['updatetime'] = gettimestring()

        # put into database
        insertstringdicttablelist(systemdatadatabase, 'hamachistatus', hamdicts)


def updatenetstatus(lastnetstatus=None):
    import pilib
    import time

    from cupid.pilib import sqlitemultquery, systemdatadatabase, readonedbrow, gettimestring, insertstringdicttablelist
    import subprocess
    from netfun import getifacestatus

    netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]

    if not lastnetstatus:
        try:
            lastnetstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]
        except:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Error reading netstatus. Attempting to recreate netstatus table with default values. ', 1, pilib.networkloglevel)
            try:
                pilib.emptyandsetdefaults(pilib.systemdatadatabase, 'netstatus')
                lastnetstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]
            except:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Error recreating netstatus. ', 1, pilib.networkloglevel)




    ## Pyiface is one way to read some iface data

    pilib.writedatedlogmsg(pilib.networklog, 'Reading ifaces with pyiface. ', 4, pilib.networkloglevel)
    ifacesdictarray = getifacestatus()

    if ifacesdictarray:
        pilib.writedatedlogmsg(pilib.networklog, 'Sending ifaces query. ', 5, pilib.networkloglevel)
        insertstringdicttablelist(pilib.systemdatadatabase, 'netifaces', ifacesdictarray)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Empty ifaces query. ', 5, pilib.networkloglevel)

    pilib.writedatedlogmsg(pilib.networklog, 'Completed pyiface ifaces. ', 4, pilib.networkloglevel)


    # Interfaces check
    # WAN check
    pilib.writedatedlogmsg(pilib.networklog, 'Checking pingtimes. ', 4, pilib.networkloglevel)
    okping = float(netconfigdata['pingthreshold'])

    from netfun import runping, getwpaclientstatus

    netstatusdict = {}

    querylist=[]
    pingresults = runping('8.8.8.8')
    # pingresults = [20, 20, 20]
    pingresult = sum(pingresults) / float(len(pingresults))
    if pingresult == 0:
        wanaccess = 0
        latency = 0
    else:
        if pingresult < okping:
            wanaccess = 1
        else:
            wanaccess = 0
        latency = pingresult

    netstatusdict['latency'] = str(latency)

    pilib.writedatedlogmsg(pilib.networklog, 'Done checking pings. ', 4, pilib.networkloglevel)

    if netconfigdata['netstatslogenabled']:
        # print('going to log stuff')
        pilib.logtimevaluedata(pilib.logdatabase, 'system_WANping', time.time(), pingresult, 1000,
                               netconfigdata['netstatslogfreq'])

    # Check supplicant status, set on/offtime if necessary.
    wpastatusdict = getwpaclientstatus()
    # try:

    # COMPLETED is onlinetime
    if wpastatusdict['wpa_state'] == 'COMPLETED':
        wpaconnected = 1

        # if we have an online time, leave it alone, or set it to now if it is empty
        if 'onlinetime' in lastnetstatus:
            # if we are newly connected or empty online time, set online time
            if lastnetstatus['connected'] == 0 or lastnetstatus['onlinetime'] == '':
                pilib.writedatedlogmsg(pilib.networklog, 'setting online time', 2, pilib.networkloglevel)
                netstatusdict['onlinetime'] = gettimestring()

            # else retain onlinetime
            else:
                netstatusdict['onlinetime'] = lastnetstatus['onlinetime']
        # if no onlinetime, set ot current time
        else:
            netstatusdict['onlinetime'] = gettimestring()

        # if we have an offlinetime, keep it. otherwise set to empty
        if 'offlinetime' in lastnetstatus:
            netstatusdict['offlinetime'] = lastnetstatus['offlinetime']
        else:
            netstatusdict['offlinetime'] = ''

    # Else we are unconnected. do opposite of above
    else:
        print('i know we are not connected')
        wpaconnected = 0

        # if we have an offline time, leave it alone, or set it to now if it is empty
        if 'offlinetime' in lastnetstatus:
            # if we are newly connected or empty online time, set online time
            if lastnetstatus['connected'] == 1 or lastnetstatus['offlinetime'] == '':
                pilib.writedatedlogmsg(pilib.networklog, 'setting offline time', 2, pilib.networkloglevel)
                netstatusdict['offlinetime'] = gettimestring()

            # else retain offlinetime
            else:
                netstatusdict['offlinetime'] = lastnetstatus['offlinetime']
        # if no offlinetime, set ot current time
        else:
            netstatusdict['offlinetime'] = gettimestring()

        # if we have an onlinetime, keep it. otherwise set to empty
        if 'onlinetime' in lastnetstatus:
            netstatusdict['onlinetime'] = lastnetstatus['onlinetime']
        else:
            netstatusdict['onlinetime'] = ''

    # Check dhcp server status
    pilib.writedatedlogmsg(pilib.networklog, 'Checking dhcp server status ', 4, pilib.networkloglevel)
    try:
        result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
    except Exception, e:
        dhcpstatus = 0
        pilib.writedatedlogmsg(pilib.networklog, 'Error in reading dhcp server status:' + str(e), 1,
                               pilib.networkloglevel)
    else:
        for line in result.stdout:
            if line.find('not running') > 0:
                dhcpstatus = 0
            elif line.find('is running') > 0:
                dhcpstatus = 1
            else:
                dhcpstatus = '\?'

    pilib.writedatedlogmsg(pilib.networklog, 'Done checking dhcp server status. ', 4, pilib.networkloglevel)

    pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus. ', 4, pilib.networkloglevel)

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
    netstatusdict['dhcpstatus'] = dhcpstatus
    netstatusdict['connected'] = wpaconnected
    netstatusdict['statusmsg'] = 'wpaconnected: ' + str(wpaconnected)

    if netconfigdata['mode'] in ['ap', 'tempap']:
        pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus to AP mode', 1, pilib.networkloglevel)
        netstatusdict['mode'] = netconfigdata['mode']
        netstatusdict['SSID'] = 'cupidwifi'
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus to station mode', 1, pilib.networkloglevel)
        netstatusdict['mode'] = str(mode)
        netstatusdict['SSID'] = str(ssid)
    netstatusdict['WANaccess'] = str(wanaccess)
    netstatusdict['address'] = str(address)

    pilib.writedatedlogmsg(pilib.networklog, 'Inserting/updating netstatusdict. ', 4, pilib.networkloglevel)

    # Recently changed to take an arbitrary dictionary.
    # Flexible, but be careful on what you rely on being in here

    netstatusdict['updatetime'] = pilib.gettimestring()

    pilib.insertstringdicttablelist(pilib.systemdatadatabase, 'netstatus', [netstatusdict])

    pilib.writedatedlogmsg(pilib.networklog, 'Completed netstatus query. ', 4, pilib.networkloglevel)

    pilib.writedatedlogmsg(pilib.networklog, 'Completed netstatus update. ', 4, pilib.networkloglevel)

    return wpastatusdict


def processsystemflags(systemflags=None):
    import pilib
    from pilib import writedatedlogmsg, systemstatuslog, systemstatusloglevel

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

            writedatedlogmsg(systemstatuslog, 'Rebooting for system flag', 0, systemstatusloglevel)
            subprocess.call(['/sbin/reboot'])
    if 'netconfig' in flagnames:
        if flagvalues[flagnames.index('netconfig')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, "name='netconfig'")
            from netconfig import runconfig

            writedatedlogmsg(systemstatuslog, 'Restarting network configuration', 0, systemstatusloglevel)
            runconfig()
    if 'updateiicontrollibs' in flagnames and not stop:
        if flagvalues[flagnames.index('updateiicontrollibs')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, 'name=\'updateiicontrollibs\'')
            from misc.gitupdatelib import updateiicontrollibs

            writedatedlogmsg(systemstatuslog, 'Updating iicontrollibs', 0, systemstatusloglevel)
            updateiicontrollibs(True)
    if 'updatecupidweblib' in flagnames and not stop:
        if flagvalues[flagnames.index('updatecupidweblib')]:
            stop = True
            pilib.setsinglevalue(pilib.systemdatadatabase, 'systemflags', 'value', 0, 'name=\'updatecupidweblib\'')
            from misc.gitupdatelib import updatecupidweblib

            writedatedlogmsg(systemstatuslog, 'Updating cupidweblib', 0, systemstatusloglevel)
            updatecupidweblib(True)


def runsystemstatus(runonce=False):
    import pilib
    import time

    from misc.gitupdatelib import updategitversions

    # This doesn't update git libraries. It checks current versions and updates the database

    try:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Checking git versions', 3, pilib.systemstatusloglevel)
        updategitversions()
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Error in git version check', 0, pilib.systemstatusloglevel)
    else:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Git version check complete', 3, pilib.systemstatusloglevel)

    systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

    ## Read wireless config via iwconfig
    updateiwstatus()

    ## Read current etstatus
    lastnetstatus={}
    try:
        lastnetstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error reading network status. ', 1, pilib.networkloglevel)

    # Poll netstatus and return data
    updatenetstatus(lastnetstatus)

    # Keep reading system status?
    while systemstatus['systemstatusenabled']:

        starttime = time.time()
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'System status routine is starting. ', 3,
                               pilib.systemstatusloglevel)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Beginning network routines. ', 3, pilib.systemstatusloglevel)

        currenttime = pilib.gettimestring()
        pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'lastsystemstatuspoll', pilib.gettimestring())

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running updateifacestatus. ', 4, pilib.systemstatusloglevel)

        # Update network interfaces statuses for all interfaces, in database tables as well
        # Check on wpa supplicant status as well. Function returns wpastatusdict
        try:
            pilib.writedatedlogmsg(pilib.networklog, 'Running updateifacestatus', 4, pilib.networkloglevel)
            wpastatusdict = updatenetstatus(lastnetstatus)
        except:
            pilib.writedatedlogmsg(pilib.networklog, 'Exception in updateifacestatus. ')
        else:
            pilib.writedatedlogmsg(pilib.networklog, 'Updateifacestatus completed. ')

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Completed updateifacestatus. ', 4, pilib.systemstatusloglevel)

        netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
        netstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]

        wpastatusmsg = ''

        # Do we want to autoconfig the network?
        # TODO: Better split netconfig up into reporting and configuration
        # Also, we appear to have duplicated a parameter, putting netconfig in both the netconfig
        # table and also the systemstatus table

        if systemstatus['netconfigenabled']:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running interface configuration. ', 4,
                                   pilib.systemstatusloglevel)
            pilib.writedatedlogmsg(pilib.networklog, 'Running interface configuration. ', 4,
                                   pilib.networkloglevel)
            # If mode is ap or tempap
            if netconfigdata['mode'] in ['ap', 'tempap']:
                pilib.writedatedlogmsg(pilib.networklog, 'AP Mode is set. ', 1, pilib.networkloglevel)

                timesincelastretry = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(
                    netconfigdata['laststationretry'])
                pilib.writedatedlogmsg(pilib.networklog, 'Time since last retry:  ' + str(timesincelastretry), 1,
                                       pilib.networkloglevel)

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
                        wpastatusmsg += 'AP checked and ok. '
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'mode', 'ap')
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'SSID', 'cupidwifi')
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'offlinetime', '')

                    # If we don't have dhcp up, restart ap mode
                    # this will currently cause reboot if we don't set onboot=True
                    # We set status message in case we change our minds and reboot here.
                    else:
                        wpastatusmsg += 'Restarting AP. '
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', wpastatusmsg)
                        netconfig.runconfig()

            # If mode is station
            elif netconfigdata['mode'] == 'station':
                pilib.writedatedlogmsg(pilib.networklog, 'Station mode is set. ', 3, pilib.networkloglevel)
                # If we have wpa up, do nothing
                if int(netstatus['connected']):
                    wpastatusmsg += 'Station wpamode appears ok. '
                    pilib.writedatedlogmsg(pilib.networklog, 'wpamode appears ok. ', 1, pilib.networkloglevel)

                # If wpa is not connected
                else:
                    wpastatusmsg += 'Station wpamode appears disconnected. '
                    print('HSIT IS NOT OK')
                    pilib.writedatedlogmsg(pilib.networklog, 'wpamode appears disconnected. ', 1, pilib.networkloglevel)

                    if netstatus['offlinetime'] == '':
                        pilib.writedatedlogmsg(pilib.networklog, 'Setting offline time for empty value. ', 4,
                                               pilib.networkloglevel)
                        pilib.setsinglevalue('netstatus', 'offlinetime', pilib.gettimestring())
                        offlinetime = 0
                    else:
                        pilib.writedatedlogmsg(pilib.networklog, 'Calculating offline time. ', 4, pilib.networkloglevel)
                        offlinetime = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(
                            netstatus['offlinetime'])

                    pilib.writedatedlogmsg(pilib.networklog, 'wpa has been offline for ' + str(offlinetime) + '. ', 3,
                                           pilib.networkloglevel)
                    wpastatusmsg += 'We have been offline for ' + str(offlinetime) + '. '

                    # If aprevert is aprevert or temprevert and we've been offline long enough, flip over to ap
                    if netconfigdata['aprevert'] in ['temprevert', 'aprevert'] and offlinetime > netconfigdata[
                        'apreverttime']:

                        # set laststationretry to currenttime. This marks when we flippsed over to ap
                        wpastatusmsg += 'Setting last station retry time. '
                        pilib.writedatedlogmsg(pilib.networklog, 'Reverting to AP mode', 3, pilib.networkloglevel)
                        pilib.writedatedlogmsg(pilib.networklog,
                                               'Setting last station retry time to ' + str(currenttime), 0,
                                               pilib.networkloglevel)
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'laststationretry', currenttime)

                        if netconfigdata['aprevert'] == 'aprevert':
                            # set mode to ap
                            wpastatusmsg += 'Setting mode to ap. '
                            pilib.writedatedlogmsg(pilib.networklog, 'Setting mode to ap ' + str(currenttime), 3,
                                                   pilib.networkloglevel)
                            pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'ap')
                        elif netconfigdata['aprevert'] == 'temprevert':
                            # set mode to tempap
                            wpastatusmsg += 'Setting mode to tempap. '
                            pilib.writedatedlogmsg(pilib.networklog, 'Setting mode to tempap ' + str(currenttime), 3,
                                                   pilib.networkloglevel)
                            pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'tempap')

                        # Unfortunately, to revert to ap mode successfully, we currently have to reboot
                        # this is built into the netconfig script - any time you set ap mode except at boot, it reboots
                        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', wpastatusmsg)
                        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running netconfig . ', 4,
                                               pilib.systemstatusloglevel)
                        netconfig.runconfig()
                    elif offlinetime > 15:
                        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Restarting netconfig on bad wpastatus', 1,
                                               pilib.systemstatusloglevel)
                        print('RUNNING CONFIG')
                        netconfig.runconfig()
            else:
                wpastatusmsg += 'mode error: ' + netconfigdata['mode']

        else:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Netconfig disabled. ', 1, pilib.systemstatusloglevel)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Finished interface configuration. ', 4,
                               pilib.systemstatusloglevel)
        pilib.writedatedlogmsg(pilib.networklog, wpastatusmsg)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running updateifacestatus. ', 4, pilib.systemstatusloglevel)
        updatenetstatus()
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Completed updateifacestatus. ', 4, pilib.systemstatusloglevel)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Network routines complete. ', 3, pilib.systemstatusloglevel)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Checking system flags. ', 3, pilib.systemstatusloglevel)
        processsystemflags()
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'System flags complete. ', 3, pilib.systemstatusloglevel)

        # Get system status again
        systemstatus = pilib.readalldbrows(pilib.controldatabase, 'systemstatus')[0]

        elapsedtime = int(time.time() - starttime)

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Status routines complete. Elapsed time: ' + str(elapsedtime), 3,
                               pilib.systemstatusloglevel)

        pilib.writedatedlogmsg(pilib.systemstatuslog,
                               'System status is sleeping for ' + str(systemstatus['systemstatusfreq']) + '. ', 3,
                               pilib.systemstatusloglevel)

        if runonce:
            break
        time.sleep(systemstatus['systemstatusfreq'])


    else:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'System status is disabled. Exiting. ', 0,
                               pilib.systemstatusloglevel)


if __name__ == '__main__':
    runsystemstatus()
