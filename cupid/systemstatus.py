#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
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
    from pilib import insertstringdicttablelist, systemdatadatabase, gettimestring
    import netfun
    iwdict = netfun.getiwstatus()
    iwdict['updatetime'] = gettimestring()

    # put into database
    insertstringdicttablelist(systemdatadatabase, 'iwstatus', [iwdict])


def watchdoghamachi(pingip):
    from netfun import runping, restarthamachi, killhamachi
    import pilib
    try:
        # Turns out this is not going to work, as when it hangs, it hangs hard
        # hamachistatusdata = gethamachistatusdata()

        # So instead, we are going to test with a ping to another member on the network that
        # should always be online. This of course means that we have to make sure that it is, in fact, always
        # online

        pingtimes = runping(pingip, numpings=5)
        pingmax = max(pingtimes)
        pingmin = min(pingtimes)
        pingave = sum(pingtimes)/len(pingtimes)

        # if hamachistatusdata['status'] not in ['logged in']:
        if pingave == 0 or pingave > 3000:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Pingtime unacceptable: ' + str(pingave) + '. ', 1, pilib.systemstatusloglevel)
            pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'hamachistatus', 0)
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Restarting Hamachi. ', 1, pilib.systemstatusloglevel)

            killhamachi()
            restarthamachi()
        else:
            if pingmax > 3000 or pingmin <= 0:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Hamachi lives, with issues: [' + ','.join(pingtimes) + '].' , 3, pilib.systemstatusloglevel)
            else:
                pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'hamachistatus', 1)
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Hamachi appears fine. ', 3, pilib.systemstatusloglevel)

    except Exception as e:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Error checking Hamachi with message:  ' + e.message, 1, pilib.systemstatusloglevel)

        killhamachi()
        restarthamachi()


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


def watchdognetstatus(allnetstatus=None):
    import pilib
    import netconfig
    import subprocess
    from cupiddaemon import pgrepstatus

    """
    And now comes the checking of configuration specific statuses and restarting them if enabled
    and necessary

    NOW
    Set number configuration types:
    eth0 is always dhcp

    if interface is not specified, it is assumed that the specified configuration applies to wlan0
    ap : access point on wlan0.
        Currently, address is hard-coded as 192.168.0.1 as set in hostapd (to have dhcp all on same subnet)
    station : station mode on wlan0
        IP address mode set in 'addtype' field. If DHCP, set as DHCP. If static, set as address field
    eth0wlan0bridge :
        wlan0 set as AP mode with bridge to eth0
    wlan0wlan1bridge :
        wlan0 set as station mode, wlan1 as ap mode with bridge
    wlan1wlan0bridge
        wlan1 set as station mode, wlan0 as ap mode with bridge

    IN THE FUTURE
    netconfigdata will have a row for each interface that needs to be configured.
    Each interface can be either static, dhcp, or ap.
    Each interface can also bridge, but this will be limited at first, due to the number of combinations.
    If bridge is selected, the mode will be checked, and the appropriate IPTables will be set based on which one is AP

    """

    if not allnetstatus:
        allnetstatus = updatenetstatus()

    netconfigdata = allnetstatus['netconfigdata']
    netstatus = allnetstatus['netstatusdict']

    # Refactor ifaces array. We could probably do this earlier and pass it around like this
    ifacedict = {}
    for iface in allnetstatus['ifacesdictarray']:
        # print(iface['name'])
        # print(iface)
        ifacedict[iface['name']] = iface

    statusmsg = ''
    currenttime = pilib.gettimestring()

    if netconfigdata['mode'] in ['ap', 'tempap']:
        pilib.writedatedlogmsg(pilib.networklog, 'AP Mode is set. ', 1, pilib.networkloglevel)

        """

        THIS NEEDS TO BE REWRITTEN ( or absorbed into eth0wlan0bridge )

        """

        if netconfigdata['mode'] == 'tempap':
            timesincelastretry = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(netconfigdata['laststationretry'])
            pilib.writedatedlogmsg(pilib.networklog, 'TempAP mode: Time since last retry:  ' + str(timesincelastretry) + '. Station retry time: '
                                   + str(netconfigdata['stationretrytime']), 1, pilib.networkloglevel)

            if timesincelastretry > netconfigdata['stationretrytime']:
                # We go back to station mode
                statusmsg += 'Time to go back to station mode. '
                pilib.writedatedlogmsg(pilib.networklog, 'Time to go back to station mode. ', 1, pilib.networkloglevel)
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'station')
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'laststationretry', '')
                netconfig.runconfig()
        else:
            # If we have ap up, do nothing

            if netstatus['dhcpstatus']:
                statusmsg += 'AP checked and ok. '
                pilib.writedatedlogmsg(pilib.networklog, 'AP checked and ok. ', 1, pilib.networkloglevel)
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'mode', 'ap')
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'SSID', 'cupidwifi')
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'offlinetime', '')

            # If we don't have dhcp up, restart ap mode
            # this will currently cause reboot if we don't set onboot=True
            # We set status message in case we change our minds and reboot here.
            else:
                statusmsg += 'Restarting AP. '
                pilib.writedatedlogmsg(pilib.networklog, 'Restarting AP mode. ', 1, pilib.networkloglevel)
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', statusmsg)
                netconfig.runconfig()

    #    Station Mode. Again, like above, this should be modular.

    elif netconfigdata['mode'] == 'station':
        pilib.writedatedlogmsg(pilib.networklog, 'Station mode is set. ', 3, pilib.networkloglevel)

        # If we have wpa up, do nothing
        if int(netstatus['connected']):
            statusmsg += 'Station wpamode appears ok. '
            pilib.writedatedlogmsg(pilib.networklog, 'wpamode appears ok. ', 1, pilib.networkloglevel)

        # If wpa is not connected
        else:
            statusmsg += 'Station wpamode appears disconnected. '
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
            statusmsg += 'We have been offline for ' + str(offlinetime) + '. '

            # If aprevert is aprevert or temprevert and we've been offline long enough, flip over to ap
            # then set offline time to now (otherwise this keeps happening)
            if netconfigdata['aprevert'] in ['temprevert', 'aprevert'] and offlinetime > netconfigdata[
                'apreverttime']:

                # set laststationretry to currenttime. This marks when we flipped over to ap
                statusmsg += 'Setting last station retry time. '
                pilib.writedatedlogmsg(pilib.networklog, 'Reverting to AP mode', 3, pilib.networkloglevel)
                pilib.writedatedlogmsg(pilib.networklog,
                                       'Setting last station retry time to ' + str(currenttime), 0,
                                       pilib.networkloglevel)
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'laststationretry', currenttime)
                pilib.setsinglevalue('netstatus', 'offlinetime', currenttime)

                if netconfigdata['aprevert'] == 'aprevert':
                    # set mode to ap
                    statusmsg += 'Setting mode to ap. '
                    pilib.writedatedlogmsg(pilib.networklog, 'Setting mode to ap ' + str(currenttime), 3,
                                           pilib.networkloglevel)
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'ap')
                elif netconfigdata['aprevert'] == 'temprevert':
                    # set mode to tempap
                    statusmsg += 'Setting mode to tempap. '
                    pilib.writedatedlogmsg(pilib.networklog, 'Setting mode to tempap ' + str(currenttime), 3,
                                           pilib.networkloglevel)
                    pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'tempap')

                # Unfortunately, to revert to ap mode successfully, we currently have to reboot
                # this is built into the netconfig script - any time you set ap mode except at boot, it reboots
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', statusmsg)
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running netconfig . ', 4,
                                       pilib.systemstatusloglevel)
                netconfig.runconfig()
            elif offlinetime > 15:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Restarting netconfig on bad wpastatus', 1,
                                       pilib.systemstatusloglevel)
                netconfig.runconfig()

            # Here, we need to check the ifaces address. Netstatus address is ambiguous
            if netstatus['ip_address'] != netconfigdata['address']:
                pilib.writedatedlogmsg(pilib.networklog, 'IP address mismatch ( Configured for ' + netconfigdata['address'] + '. Reporting' + netstatus['ip_address'] + ' ). Running config.', 1, pilib.networkloglevel)
                netconfig.runconfig()
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'IP address match for ' + netconfigdata['address'] + '. ', 3, pilib.networkloglevel)

    elif netconfigdata['mode'] == 'eth0wlan0bridge':
        runconfig = False

        # Check wlan0 dhcp and hostapd status
        try:
            wlan0ifacedata =ifacedict['wlan0']
        except KeyError:
            pilib.writedatedlogmsg(pilib.networklog, 'No wlan0 data present in configuration of eth0wlan0bridge. ', 1, pilib.networkloglevel)
            statusmsg += 'wlan0 data is not present. '
            runconfig = True
        else:
            pilib.writedatedlogmsg(pilib.networklog, 'Checking dhcp server status on wlan0. ', 4, pilib.networkloglevel)
            try:
                result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
            except Exception, e:
                # If not running, the subprocess call will throw an error
                pilib.writedatedlogmsg(pilib.networklog, 'Error in reading dhcp server status. Assumed down. ', 1, pilib.networkloglevel)
                statusmsg += 'dhcp server appears down. '
                runconfig = True
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'DHCP server appears to be up. ', 1,  pilib.networkloglevel)

            """ Check ifconfig ipaddress for wlan0
                This should be programmable. """

            if wlan0ifacedata['address'] == '192.168.0.1':
                pilib.writedatedlogmsg(pilib.networklog, 'wlan0 address is appears to be set properly:  ' + str(wlan0ifacedata['address']), 3, pilib.networkloglevel)
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'wlan0 address is not set properly:  ' + str(wlan0ifacedata['address']), 1, pilib.networkloglevel)
                statusmsg += 'wlan0 address does not appear ok. '
                runconfig = True

            if pgrepstatus('hostapd.*wlan0')['count'] == 1:
                pilib.writedatedlogmsg(pilib.networklog, 'hostapd on wlan0 appears to be ok. ', 3, pilib.networkloglevel)
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'hostapd on wlan0 does NOT appear to be ok. ', 1, pilib.networkloglevel)
                statusmsg += 'wlan0 hostpad does not appear ok. '
                runconfig=True

        if runconfig:
            pilib.writedatedlogmsg(pilib.networklog, 'Running netconfig. ', 1, pilib.networkloglevel)
            statusmsg += 'Running netconfig to fix. '
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', statusmsg)
            netconfig.runconfig()
        else:
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', 'Mode appears to be set.')

    elif netconfigdata['mode'] == 'wlan0wlan1bridge' or 'wlan1wlan0bridge':
        if netconfigdata['mode'] == 'wlan0wlan1bridge':
            stationinterface = 'wlan0'
            apinterface = 'wlan1'
        else:
            stationinterface = 'wlan1'
            apinterface = 'wlan0'
        runconfig = False

        # Check station address (not yet implemented) and wpa status (implemented)
        try:
            stationifacedata = ifacedict[stationinterface]
        except KeyError:
            pilib.writedatedlogmsg(pilib.networklog, 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode'], 1, pilib.networkloglevel)
            statusmsg += 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode']
            runconfig = True
        else:
            wpadata = pilib.parseoptions(stationifacedata['wpastate'])
            if wpadata['wpa_state'] == 'COMPLETED':
                pilib.writedatedlogmsg(pilib.networklog, 'station interface ' + stationinterface + ' wpastatus appears ok. ', 3, pilib.networkloglevel)
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'station interface for ' + stationinterface + ' does not appear ok judged by wpa_state. ', 1, pilib.networkloglevel)
                statusmsg += 'station interface does not appear ok judged by wpa_state. '
                runconfig = True

        # Check wlan1 dhcp and hostapd status
        try:
            apifacedata = ifacedict[apinterface]
        except KeyError:
            pilib.writedatedlogmsg(pilib.networklog, 'No apiface data(' + apinterface + ') present for mode ' + netconfigdata['mode'], 1, pilib.networkloglevel)
            runconfig = True
        else:
            pilib.writedatedlogmsg(pilib.networklog, 'Checking dhcp server status on ' + apinterface, 4, pilib.networkloglevel)
            try:
                # Note that this does not check carefully that the dhcp server is running on the correct interface.
                # We need a check on this.
                result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
            except Exception, e:
                # If not running, the subprocess call will throw an error
                pilib.writedatedlogmsg(pilib.networklog, 'Error in reading dhcp server status for interface ' + apinterface + ' Assumed down. ', 1, pilib.networkloglevel)
                statusmsg += 'Error in reading dhcp server status. Assumed down. '
                runconfig = True
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'DHCP server appears to be up. ', 1,  pilib.networkloglevel)


            # Check ifconfig ipaddress for ap
            # This should be programmable.
            if apifacedata['address'] == '192.168.0.1':
                pilib.writedatedlogmsg(pilib.networklog, 'ap interface ' + apinterface + ' address is appears to be set properly:  ' + str(apifacedata['address']), 3, pilib.networkloglevel)
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'ap interface ' + apinterface + ' address is not set properly:  ' + str(apifacedata['address']), 1, pilib.networkloglevel)
                runconfig = True

            if pgrepstatus('hostapd.*' + apinterface)['count'] == 1:
                pilib.writedatedlogmsg(pilib.networklog, 'hostapd on ' + apinterface + ' appears to be ok. ', 3, pilib.networkloglevel)
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'hostapd on ' + apinterface + ' does NOT appear to be ok. ', 1, pilib.networkloglevel)
                statusmsg += 'hostapd on ' + apinterface + ' does NOT appear to be ok. '
                runconfig=True

        if runconfig:
            pilib.writedatedlogmsg(pilib.networklog, 'Running netconfig. ', 1, pilib.networkloglevel)
            statusmsg += 'Running netconfig to fix. '
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', statusmsg)
            netconfig.runconfig()

    elif netconfigdata['mode'] in ['']:
        # We don't yet handle bridge modes. We probably should (!)
        statusmsg += 'mode not handled: ' + netconfigdata['mode']


    # if netconfigdata['mode'] in ['station', 'wlan0wlan1bridge']:
    #     pilib.writedatedlogmsg(pilib.systemstatuslog, 'Checking WPA status for mode ' + netconfigdata['mode'], 2, pilib.systemstatusloglevel)
    #     wpastatusdict = getwpaclientstatus()
    #     # try:
    #
    #     # COMPLETED is onlinetime
    #     if wpastatusdict['wpa_state'] == 'COMPLETED':
    #         wpastatusdict['connected'] = 1
    #
    #         # if we have an online time, leave it alone, or set it to now if it is empty
    #         if 'onlinetime' in lastnetstatus:
    #             # if we are newly connected or empty online time, set online time
    #             if lastnetstatus['connected'] == 0 or lastnetstatus['onlinetime'] == '':
    #                 pilib.writedatedlogmsg(pilib.networklog, 'setting online time', 2, pilib.networkloglevel)
    #                 netstatusdict['onlinetime'] = gettimestring()
    #
    #             # else retain onlinetime
    #             else:
    #                 netstatusdict['onlinetime'] = lastnetstatus['onlinetime']
    #         # if no onlinetime, set ot current time
    #         else:
    #             netstatusdict['onlinetime'] = gettimestring()
    #
    #         # if we have an offlinetime, keep it. otherwise set to empty
    #         if 'offlinetime' in lastnetstatus:
    #             netstatusdict['offlinetime'] = lastnetstatus['offlinetime']
    #         else:
    #             netstatusdict['offlinetime'] = ''
    #
    #     # Else we are unconnected. do opposite of above
    #     else:
    #         wpastatusdict['connected'] = 0
    #
    #         # if we have an offline time, leave it alone, or set it to now if it is empty
    #         if 'offlinetime' in lastnetstatus:
    #             # if we are newly connected or empty online time, set online time
    #             if lastnetstatus['connected'] == 1 or lastnetstatus['offlinetime'] == '':
    #                 pilib.writedatedlogmsg(pilib.networklog, 'setting offline time', 2, pilib.networkloglevel)
    #                 netstatusdict['offlinetime'] = gettimestring()
    #
    #             # else retain offlinetime
    #             else:
    #                 netstatusdict['offlinetime'] = lastnetstatus['offlinetime']
    #         # if no offlinetime, set ot current time
    #         else:
    #             netstatusdict['offlinetime'] = gettimestring()
    #
    #         # if we have an onlinetime, keep it. otherwise set to empty
    #         if 'onlinetime' in lastnetstatus:
    #             netstatusdict['onlinetime'] = lastnetstatus['onlinetime']
    #         else:
    #             netstatusdict['onlinetime'] = ''
    # else:
    #     pilib.writedatedlogmsg(pilib.systemstatuslog, 'Not checking WPA status for mode ' + netconfigdata['mode'], 2, pilib.systemstatusloglevel)
    #     wpastatusdict = {'connected':0}
    #
    # # Check dhcp server status
    # pilib.writedatedlogmsg(pilib.networklog, 'Checking dhcp server status ', 4, pilib.networkloglevel)
    # try:
    #     result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
    # except Exception, e:
    #     dhcpstatus = 0
    #     pilib.writedatedlogmsg(pilib.networklog, 'Error in reading dhcp server status. Assumed down', 1,
    #                            pilib.networkloglevel)
    # else:
    #     for line in result:
    #         if line.find('not running') > 0:
    #             dhcpstatus = 0
    #         elif line.find('is running') > 0:
    #             dhcpstatus = 1
    #         else:
    #             dhcpstatus = '\?'
    #
    # pilib.writedatedlogmsg(pilib.networklog, 'Done checking dhcp server status. ', 4, pilib.networkloglevel)
    #
    # pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus. ', 4, pilib.networkloglevel)
    #
    # wpaconnected = wpastatusdict['connected']
    # try:
    #     wpastatusdict['dhcpstatus'] = dhcpstatus
    # except:
    #     wpastatusdict['dhcpstatus'] = 0
    #     dhcpstatus = 0
    # try:
    #     mode = wpastatusdict['mode']
    # except KeyError:
    #     mode = 'none'
    # try:
    #     ssid = wpastatusdict['ssid']
    # except KeyError:
    #     ssid = 'none'
    # try:
    #     address = wpastatusdict['ip_address']
    # except KeyError:
    #     address = 'none'
    #
    # # print('myaddress is ' + address)
    # netstatusdict['dhcpstatus'] = dhcpstatus
    # netstatusdict['connected'] = wpaconnected
    # netstatusdict['statusmsg'] = 'wpaconnected: ' + str(wpaconnected)
    #
    # if netconfigdata['mode'] in ['ap', 'tempap']:
    #     pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus to AP mode', 1, pilib.networkloglevel)
    #     netstatusdict['mode'] = netconfigdata['mode']
    #     netstatusdict['SSID'] = 'cupidwifi'
    # else:
    #     pilib.writedatedlogmsg(pilib.networklog, 'Updating netstatus to station mode', 1, pilib.networkloglevel)
    #     netstatusdict['mode'] = str(mode)
    #     netstatusdict['SSID'] = str(ssid)
    # netstatusdict['WANaccess'] = str(wanaccess)
    # netstatusdict['address'] = str(address)
    #
    # pilib.writedatedlogmsg(pilib.networklog, 'Inserting/updating netstatusdict. ', 4, pilib.networkloglevel)
    #
    # # Recently changed to take an arbitrary dictionary.
    # # Flexible, but be careful on what you rely on being in here
    #
    # netstatusdict['updatetime'] = pilib.gettimestring()
    #
    # pilib.insertstringdicttablelist(pilib.systemdatadatabase, 'netstatus', [netstatusdict])
    #
    # pilib.writedatedlogmsg(pilib.networklog, 'Completed netstatus query. ', 4, pilib.networkloglevel)
    #
    # pilib.writedatedlogmsg(pilib.networklog, 'Completed netstatus update. ', 4, pilib.networkloglevel)
    #
    # return {'wpastatusdict':wpastatusdict, 'ifacesdictarray':ifacesdictarray}
    #


def updatenetstatus(lastnetstatus=None):
    import pilib
    import time
    import subprocess
    from netfun import getifacestatus, getwpaclientstatus

    netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]

    """ We get last netstatus so that we can save last online times, previous online status, etc. """

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

    """ Pyiface is one way to read some iface data """

    pilib.writedatedlogmsg(pilib.networklog, 'Reading ifaces with pyiface. ', 4, pilib.networkloglevel)
    ifacesdictarray = getifacestatus()

    """ We supplement with wpa status on the wlan interfaces """

    updateddictarray = []
    for interface in ifacesdictarray:
        if interface['name'].find('wlan') >= 0:
            interface['wpastate'] = pilib.dicttojson(getwpaclientstatus(interface['name']))
        else:
            interface['wpastate'] = ''
        updateddictarray.append(interface)
    ifacesdictarray = updateddictarray

    """ Then write it to the table """

    if ifacesdictarray:
        pilib.writedatedlogmsg(pilib.networklog, 'Sending ifaces query. ', 5, pilib.networkloglevel)
        # print(ifacesdictarray)
        pilib.insertstringdicttablelist(pilib.systemdatadatabase, 'netifaces', ifacesdictarray)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Empty ifaces query. ', 2, pilib.networkloglevel)

    pilib.writedatedlogmsg(pilib.networklog, 'Completed pyiface ifaces. ', 4, pilib.networkloglevel)

    """ Now we check to see if we can connect to WAN """

    pilib.writedatedlogmsg(pilib.networklog, 'Checking pingtimes. ', 4, pilib.networkloglevel)
    okping = float(netconfigdata['pingthreshold'])

    from netfun import runping

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
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'WANaccess', 1)
            if lastnetstatus['WANaccess'] == 0:
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'onlinetime', pilib.gettimestring())

        else:
            wanaccess = 0
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'WANaccess', 0)
            if lastnetstatus['WANaccess'] == 1:
                pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'offlinetime', pilib.gettimestring())

        latency = pingresult

    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'latency', latency)
    pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'updatetime', pilib.gettimestring())

    pilib.writedatedlogmsg(pilib.networklog, 'Done checking pings. ', 4, pilib.networkloglevel)

    if netconfigdata['netstatslogenabled']:
        # print('going to log stuff')
        pilib.logtimevaluedata(pilib.logdatabase, 'system_WANping', time.time(), pingresult, 1000,
                               netconfigdata['netstatslogfreq'])

    return {'netstatusdict': netstatusdict, 'ifacesdictarray': ifacesdictarray, 'netconfigdata':netconfigdata}


def processapoverride(pin):
    pilib.writedatedlogmsg(pilib.networklog, "Reading GPIO override on pin " + str(pin) + '. ', 3, pilib.networkloglevel)
    pilib.writedatedlogmsg(pilib.systemstatuslog, "Reading GPIO override on pin " + str(pin) + '. ', 2, pilib.systemstatusloglevel)

    import RPi.GPIO as GPIO
    import pilib

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    except:
        pilib.writedatedlogmsg(pilib.networklog, "Error reading GPIO", 3, pilib.networkloglevel)
    else:
        # jumper in place = input off, --> AP mode
        if not GPIO.input(pin):
            pilib.writedatedlogmsg(pilib.networklog, "GPIO On. Setting AP Mode.", 3, pilib.networkloglevel)
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'ap')
        # else:
        #     pilib.writedatedlogmsg(pilib.networklog, "GPIO Off. Setting Station Mode.", 3, pilib.networkloglevel)
        #     pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'station')


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
    import netconfig

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
    # this is breaking systemstatus for some reason
    # updateiwstatus()

    ## Read current netstatus
    lastnetstatus={}
    try:
        lastnetstatus = pilib.readonedbrow(pilib.systemdatadatabase, 'netstatus')[0]
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error reading network status. ', 1, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Completed network status. ', 3, pilib.networkloglevel)

    # Poll netstatus and return data
    allnetstatus = updatenetstatus(lastnetstatus)
    # wpastatusdict = allnetstatus['wpastatusdict']

    # Keep reading system status?
    while systemstatus['systemstatusenabled']:

        currenttime = pilib.gettimestring()
        pilib.setsinglevalue(pilib.controldatabase, 'systemstatus', 'lastsystemstatuspoll', pilib.gettimestring())

        starttime = time.time()
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'System status routine is starting. ', 3,
                               pilib.systemstatusloglevel)

        """
        Check all network statuses. The goal here is to totally decouple status read and reconfigure
        When we need to check all status data, we'll have it either in a dict or dict array, or in a database table
        """

        if systemstatus['netstatusenabled']:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Beginning network routines. ', 3, pilib.systemstatusloglevel)

            # Update network interfaces statuses for all interfaces, in database tables as well
            # Check on wpa supplicant status as well. Function returns wpastatusdict
            try:
                pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running updateifacestatus. ', 4, pilib.systemstatusloglevel)
                pilib.writedatedlogmsg(pilib.networklog, 'Running updateifacestatus', 4, pilib.networkloglevel)
                allnetstatus = updatenetstatus(lastnetstatus)
            except:
                pilib.writedatedlogmsg(pilib.networklog, 'Exception in updateifacestatus. ')
            else:
                pilib.writedatedlogmsg(pilib.networklog, 'Updateifacestatus completed. ')

            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Completed net status update. ', 4, pilib.systemstatusloglevel)
        else:
            allnetstatus={'netstatusdict': {}, 'ifacesdictarray': {}}


        """
        End network configuration status
        """

        """
        Do we want to autoconfig the network? If so, we analyze our netstatus data against what should be going on,
        and translate this into a network status
        """

        if systemstatus['checkhamachistatus']:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Checking Hamachi Status. ', 3, pilib.systemstatusloglevel)
            watchdoghamachi(pingip='25.215.49.105')

        if systemstatus['netconfigenabled'] and systemstatus['netstatusenabled']:



            # No need to get this fresh. We have it stored.
            netconfigdata = allnetstatus['netconfigdata']

            # We are going to hack in a jumper that sets AP configuration. This isn't the worst thing ever.
            if netconfigdata['apoverride']:
                result = processapoverride(21)

            ''' Now we check network status depending on the configuration we have selected '''
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Running interface configuration watchdog. ', 4,
                                   pilib.systemstatusloglevel)
            pilib.writedatedlogmsg(pilib.networklog, 'Running interface configuration. Mode: ' + netconfigdata['mode'], 4,
                                   pilib.networkloglevel)

            result = watchdognetstatus()



        else:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'Netconfig disabled. ', 1, pilib.systemstatusloglevel)
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'mode', 'manual')
            pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'statusmsg', 'netconfig is disabled')

        pilib.writedatedlogmsg(pilib.systemstatuslog, 'Finished interface configuration. ', 4,
                               pilib.systemstatusloglevel)
        # pilib.writedatedlogmsg(pilib.networklog, statusmsg)

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
