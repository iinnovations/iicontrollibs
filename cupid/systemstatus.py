#!/usr/bin/env python

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


def readhardwarefileintoversions():

    from iiutilities import utility
    from cupid import pilib
    from iiutilities import dblib

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
                utility.log(pilib.dirs.logs.system, 'Device data parse error', 1, pilib.loglevels.system)
        dblib.sqlitequery(pilib.dirs.dbs.system,
                          dblib.makesqliteinsert('versions', ['hardware', devicedict['hardware']], ['item', 'version']))
    except:
        utility.log(pilib.dirs.logs.system, 'Error opening devicedata file to parse', 1,
                      pilib.loglevels.system)


def updateiwstatus():

    from iiutilities.netfun import getiwstatus
    from iiutilities.datalib import gettimestring
    from cupid.pilib import dirs
    from iiutilities.dblib import insertstringdicttablelist

    iwdict = getiwstatus()
    iwdict['updatetime'] = gettimestring()

    # put into database
    insertstringdicttablelist(dirs.dbs.system, 'iwstatus', [iwdict], droptable=True)


def watchdoghamachi(pingip):
    from iiutilities.netfun import runping, restarthamachi, killhamachi
    from iiutilities import utility
    from iiutilities import dblib
    from cupid import pilib

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
        if pingave <= 0 or pingave > 3000:
            utility.log(pilib.dirs.logs.network, 'Pingtime unacceptable: ' + str(pingave) + '. ', 1, pilib.loglevels.network)
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'hamachistatus', 0)
            utility.log(pilib.dirs.logs.network, 'Restarting Hamachi. ', 1, pilib.loglevels.network)

            killhamachi()
            restarthamachi()
            utility.log(pilib.dirs.logs.network, 'Completed restarting Hamachi. ', 1, pilib.loglevels.network)

        else:
            if pingmax > 3000 or pingmin <= 0:
                utility.log(pilib.dirs.logs.system, 'Hamachi lives, with issues: ' + str(pingtimes), 3, pilib.loglevels.system)
            else:
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'hamachistatus', 1)
                utility.log(pilib.dirs.logs.network, 'Hamachi appears fine. ', 3, pilib.loglevels.network)

    except Exception as e:

        utility.log(pilib.dirs.logs.network, 'Error checking Hamachi with message:  ' + e.message, 1, pilib.loglevels.network)

        killhamachi()
        restarthamachi()
        print('blurg')


def updatehamachistatus():
    from pilib import dirs
    from iiutilities.dblib import insertstringdicttablelist
    from iiutilities import netfun
    from iiutilities.datalib import gettimestring
    try:
        hamdicts = netfun.gethamachidata()
    except:
        pass
    else:
        for index, dict in enumerate(hamdicts):
            hamdicts[index]['updatetime'] = gettimestring()

        # put into database
        insertstringdicttablelist(dirs.dbs.system, 'hamachistatus', hamdicts, droptable=True)


def watchdognetstatus(allnetstatus=None):

    import subprocess
    from cupiddaemon import pgrepstatus
    from iiutilities import utility
    from cupid import pilib
    from iiutilities import datalib
    from cupid import netconfig
    from iiutilities import dblib

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

    # print(ifacedict)

    statusmsg = ''
    currenttime = datalib.gettimestring()

    runconfig = False
    if netconfigdata['mode'] in ['ap', 'tempap']:
        utility.log(pilib.dirs.logs.network, 'AP Mode is set. ', 1, pilib.loglevels.network)

        """

        THIS NEEDS TO BE REWRITTEN ( or absorbed into eth0wlan0bridge )

        """

        if netconfigdata['mode'] == 'tempap':
            timesincelastretry = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(netconfigdata['laststationretry'])
            utility.log(pilib.dirs.logs.network, 'TempAP mode: Time since last retry:  ' + str(timesincelastretry) + '. Station retry time: '
                          + str(netconfigdata['stationretrytime']), 1, pilib.loglevels.network)

            if timesincelastretry > netconfigdata['stationretrytime']:
                # We go back to station mode
                statusmsg += 'Time to go back to station mode. '
                utility.log(pilib.dirs.logs.network, 'Time to go back to station mode. ', 1, pilib.loglevels.network)
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'mode', 'station')
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'laststationretry', '')
                netconfig.runconfig()
        else:
            # If we have ap up, do nothing

            if netstatus['dhcpstatus']:
                statusmsg += 'AP checked and ok. '
                utility.log(pilib.dirs.logs.network, 'AP checked and ok. ', 1, pilib.loglevels.network)
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'mode', 'ap')
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'SSID', 'cupidwifi')
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'offlinetime', '')

            # If we don't have dhcp up, restart ap mode
            # this will currently cause reboot if we don't set onboot=True
            # We set status message in case we change our minds and reboot here.
            else:
                statusmsg += 'Restarting AP. '
                utility.log(pilib.dirs.logs.network, 'Restarting AP mode. ', 1, pilib.loglevels.network)
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', statusmsg)
                netconfig.runconfig()

    #    Station Mode. Again, like above, this should be modular.

    elif netconfigdata['mode'] == 'station':

        utility.log(pilib.dirs.logs.network, 'Station mode is set. ', 3, pilib.loglevels.network)

        # Check station address (not yet implemented) and wpa status (implemented)
        stationinterface = 'wlan0'
        try:
            stationifacedata = ifacedict[stationinterface]
        except KeyError:
            utility.log(pilib.dirs.logs.network, 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode'], 1, pilib.loglevels.network)
            statusmsg += 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode']
            runconfig = True
        else:
            wpadata = datalib.parseoptions(stationifacedata['wpastate'])
            if wpadata['wpa_state'] == 'COMPLETED' and stationifacedata['address']:
                utility.log(pilib.dirs.logs.network, 'station interface ' + stationinterface + ' wpastatus appears ok with address ' + str(stationifacedata['address']), 3, pilib.loglevels.network)

                # Update netstatus
                try:
                    wpastatedata = utility.jsontodict(stationifacedata['wpastate'])
                    ssid = wpastatedata['ssid']
                except:
                    print('oops')
                    ssid = 'oops'
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'SSID', ssid)

            else:
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'SSID', '')
                utility.log(pilib.dirs.logs.network, 'station interface for ' + stationinterface + ' does not appear ok judged by wpa_state: wpastate = ' + wpadata['wpa_state'] + ' address= ' + stationifacedata['address'], 1, pilib.loglevels.network)
                statusmsg += 'station interface does not appear ok judged by wpa_state. '
                runconfig = True

    elif netconfigdata['mode'] == 'eth0wlan0bridge':

        # We don't actually check eth0. This is because we shouldn't have to. Also, if we don't check on eth0, we can
        # use the same mode for wlan0 AP and eth0wlan0 bridge. Hot plug, works fine.

        # Check wlan0 dhcp and hostapd status
        try:
            wlan0ifacedata =ifacedict['wlan0']
        except KeyError:
            utility.log(pilib.dirs.logs.network, 'No wlan0 data present in configuration of eth0wlan0bridge. ', 1, pilib.loglevels.network)
            statusmsg += 'wlan0 data is not present. '
            runconfig = True
        else:
            utility.log(pilib.dirs.logs.network, 'Checking dhcp server status on wlan0. ', 4, pilib.loglevels.network)
            try:
                result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
            except Exception, e:
                # If not running, the subprocess call will throw an error
                utility.log(pilib.dirs.logs.network, 'Error in reading dhcp server status. Assumed down. ', 1, pilib.loglevels.network)
                statusmsg += 'dhcp server appears down. '
                runconfig = True
            else:
                utility.log(pilib.dirs.logs.network, 'DHCP server appears to be up. ', 1, pilib.loglevels.network)

            """ Check ifconfig ipaddress for wlan0
                This should be programmable. """

            if wlan0ifacedata['address'] == '192.168.0.1':
                utility.log(pilib.dirs.logs.network, 'wlan0 address is appears to be set properly:  ' + str(wlan0ifacedata['address']), 3, pilib.loglevels.network)
            else:
                utility.log(pilib.dirs.logs.network, 'wlan0 address is not set properly:  ' + str(wlan0ifacedata['address']), 1, pilib.loglevels.network)
                statusmsg += 'wlan0 address does not appear ok. '
                runconfig = True

            if pgrepstatus('hostapd.*wlan0')['count'] == 1:
                utility.log(pilib.dirs.logs.network, 'hostapd on wlan0 appears to be ok. ', 3, pilib.loglevels.network)
            else:
                utility.log(pilib.dirs.logs.network, 'hostapd on wlan0 does NOT appear to be ok. ', 1, pilib.loglevels.network)
                statusmsg += 'wlan0 hostpad does not appear ok. '
                runconfig=True

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
            utility.log(pilib.dirs.logs.network, 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode'], 1, pilib.loglevels.network)
            statusmsg += 'No stationiface data(' + stationinterface + ') present for mode ' + netconfigdata['mode']
            runconfig = True
        else:
            wpadata = datalib.parseoptions(stationifacedata['wpastate'])
            if wpadata['wpa_state'] == 'COMPLETED':
                utility.log(pilib.dirs.logs.network, 'station interface ' + stationinterface + ' wpastatus appears ok. ', 3, pilib.loglevels.network)

                # Update netstatus
                try:
                    wpastatedata = utility.jsontodict(stationifacedata['wpastate'])
                    ssid = wpastatedata['ssid']
                except:
                    print('oops')
                    ssid = 'oops'
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'SSID', ssid)

            else:
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'SSID', '')
                utility.log(pilib.dirs.logs.network, 'station interface for ' + stationinterface + ' does not appear ok judged by wpa_state. ', 1, pilib.loglevels.network)
                statusmsg += 'station interface does not appear ok judged by wpa_state. '
                runconfig = True

        # Check wlan1 dhcp and hostapd status
        try:
            apifacedata = ifacedict[apinterface]
        except KeyError:
            utility.log(pilib.dirs.logs.network, 'No apiface data(' + apinterface + ') present for mode ' + netconfigdata['mode'], 1, pilib.loglevels.network)
            runconfig = True
        else:
            utility.log(pilib.dirs.logs.network, 'Checking dhcp server status on ' + apinterface, 4, pilib.loglevels.network)
            try:
                # Note that this does not check carefully that the dhcp server is running on the correct interface.
                # We need a check on this.
                result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
            except Exception, e:
                # If not running, the subprocess call will throw an error
                utility.log(pilib.dirs.logs.network, 'Error in reading dhcp server status for interface ' + apinterface + ' Assumed down. ', 1, pilib.loglevels.network)
                statusmsg += 'Error in reading dhcp server status. Assumed down. '
                print('SETTING TRUE')
                runconfig = True
            else:
                utility.log(pilib.dirs.logs.network, 'DHCP server appears to be up. ', 1, pilib.loglevels.network)


            # Check ifconfig ipaddress for ap
            # This should be programmable.
            if apifacedata['address'] == '192.168.0.1':
                utility.log(pilib.dirs.logs.network, 'ap interface ' + apinterface + ' address is appears to be set properly:  ' + str(apifacedata['address']), 3, pilib.loglevels.network)
            else:
                utility.log(pilib.dirs.logs.network, 'ap interface ' + apinterface + ' address is not set properly:  ' + str(apifacedata['address']), 1, pilib.loglevels.network)
                runconfig = True

            if pgrepstatus('hostapd.*' + apinterface)['count'] == 1:
                utility.log(pilib.dirs.logs.network, 'hostapd on ' + apinterface + ' appears to be ok. ', 3, pilib.loglevels.network)
            else:
                utility.log(pilib.dirs.logs.network, 'hostapd on ' + apinterface + ' does NOT appear to be ok. ', 1, pilib.loglevels.network)
                statusmsg += 'hostapd on ' + apinterface + ' does NOT appear to be ok. '
                runconfig = True

    elif netconfigdata['mode'] in ['']:
        statusmsg += 'mode not handled: ' + netconfigdata['mode']

    # Now do some sleuthing if we are being stringent about WAN access. Have to be careful about this if we are on a
    # private network

    if netconfigdata['requireWANaccess']:
        utility.log(pilib.dirs.logs.network, 'Requiring WAN access. Checking status and times. ', 3, pilib.loglevels.network)
        # print('NETSTATUS')
        # print(netstatus)
        if not netstatus['WANaccess']:
            utility.log(pilib.dirs.logs.network, 'No WANaccess. Checking offline time. ', 2, pilib.loglevels.network)
            try:
                offlinetime = netstatus['offlinetime']
            except:
                print('netstatus ERROR')
                utility.log(pilib.dirs.logs.network, 'Error gettng offlinetime. ', 2, pilib.loglevels.network)

            offlineperiod = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(offlinetime)
            utility.log(pilib.dirs.logs.network, 'We have been offline for ' + str(offlineperiod))

            # When did we last restart the network config? Is it time to again?
            timesincelastnetrestart = datalib.timestringtoseconds(
                datalib.gettimestring()) - datalib.timestringtoseconds(netstatus['lastnetreconfig'])
            utility.log(pilib.dirs.logs.network, 'It has been ' + str(timesincelastnetrestart) + ' seconds since we last restarted the network configuration. ')
            if timesincelastnetrestart > int(netconfigdata['WANretrytime']):
                utility.log(pilib.dirs.logs.network, 'We are not online, and it has been long enough, exceeding retry time of ' + str(int(netconfigdata['WANretrytime'])))
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'lastnetreconfig', datalib.gettimestring())

                # We do reset the WAN offline time in the reboot sequence, hwoever.

                restarts = int(dblib.getsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccessrestarts'))
                restarts += 1
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccessrestarts', restarts)

                utility.log(pilib.dirs.logs.network, 'Going to run netconfig to correct WAN access.')
                runconfig = True

            else:
                utility.log(pilib.dirs.logs.network, 'Not yet time to run netconfig to correct WAN access. Retry time set at ' + str(netconfigdata['WANretrytime']))
        else:
            utility.log(pilib.dirs.logs.network, 'WANAccess is fine. ')

    if runconfig:
        # Set bad status in netstatus
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstate', 0)

        # Set ok time to '' to trigger rewrite next time status is ok
        lastoktime = dblib.getsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime')
        if not lastoktime:
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime', datalib.gettimestring())
        else:
            if netconfigdata['rebootonfail']:
                offlinetime = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(lastoktime)
                if offlinetime > int(netconfigdata['rebootonfailperiod']):

                    # Set to '' so we get another full fail period before rebooting again
                    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime', '')

                    # Same thing for WAN offline time
                    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'offlinetime', '')

                    bootcounts = int(dblib.getsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netrebootcounter'))
                    bootcounts += 1
                    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netrebootcounter', str(bootcounts))

                    # Set system flag to reboot
                    utility.log(pilib.dirs.logs.system, 'REBOOTING to try to fix network', 0, pilib.loglevels.system)
                    dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemflags', 'reboot', 1)

        utility.log(pilib.dirs.logs.network, 'Running netconfig. ', 1, pilib.loglevels.network)
        statusmsg += 'Running netconfig to fix. '
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', statusmsg)
        netconfig.runconfig()

    else:
        # Clear bad status in netstatus and set netoktime
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', 'Mode appears to be set.')
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstate', 1)
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime', datalib.gettimestring())

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
    #                 pilib.writedatedlogmsg(pilib.dirs.logs.network, 'setting online time', 2, pilib.loglevels.network)
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
    #                 pilib.writedatedlogmsg(pilib.dirs.logs.network, 'setting offline time', 2, pilib.loglevels.network)
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
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Checking dhcp server status ', 4, pilib.loglevels.network)
    # try:
    #     result = subprocess.check_output(['/usr/sbin/service', 'isc-dhcp-server', 'status'], stderr=subprocess.PIPE)
    # except Exception, e:
    #     dhcpstatus = 0
    #     pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Error in reading dhcp server status. Assumed down', 1,
    #                            pilib.loglevels.network)
    # else:
    #     for line in result:
    #         if line.find('not running') > 0:
    #             dhcpstatus = 0
    #         elif line.find('is running') > 0:
    #             dhcpstatus = 1
    #         else:
    #             dhcpstatus = '\?'
    #
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Done checking dhcp server status. ', 4, pilib.loglevels.network)
    #
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Updating netstatus. ', 4, pilib.loglevels.network)
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
    #     pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Updating netstatus to AP mode', 1, pilib.loglevels.network)
    #     netstatusdict['mode'] = netconfigdata['mode']
    #     netstatusdict['SSID'] = 'cupidwifi'
    # else:
    #     pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Updating netstatus to station mode', 1, pilib.loglevels.network)
    #     netstatusdict['mode'] = str(mode)
    #     netstatusdict['SSID'] = str(ssid)
    # netstatusdict['WANaccess'] = str(wanaccess)
    # netstatusdict['address'] = str(address)
    #
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Inserting/updating netstatusdict. ', 4, pilib.loglevels.network)
    #
    # # Recently changed to take an arbitrary dictionary.
    # # Flexible, but be careful on what you rely on being in here
    #
    # netstatusdict['updatetime'] = pilib.gettimestring()
    #
    # pilib.insertstringdicttablelist(pilib.systemdatadatabase, 'netstatus', [netstatusdict])
    #
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Completed netstatus query. ', 4, pilib.loglevels.network)
    #
    # pilib.writedatedlogmsg(pilib.dirs.logs.network, 'Completed netstatus update. ', 4, pilib.loglevels.network)
    #
    # return {'wpastatusdict':wpastatusdict, 'ifacesdictarray':ifacesdictarray}
    #


def updatenetstatus(lastnetstatus=None):
    import time
    from iiutilities import netfun
    from iiutilities import dblib
    from cupid import pilib
    from iiutilities import utility
    from iiutilities import datalib
    from iiutilities.netfun import getifconfigstatus, getwpaclientstatus

    netconfigdata = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]

    """ We get last netstatus so that we can save last online times, previous online status, etc. """

    if not lastnetstatus:
        try:
            lastnetstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]
        except:
            utility.log(pilib.dirs.logs.system, 'Error reading netstatus. Attempting to recreate netstatus table with default values. ', 1, pilib.loglevels.network)
            try:
                dblib.emptyandsetdefaults(pilib.dirs.dbs.system, 'netstatus')
                lastnetstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]
            except:
                utility.log(pilib.dirs.logs.system, 'Error recreating netstatus. ', 1, pilib.loglevels.network)

    """ Pyiface is one way to read some iface data, but it doesn't always appear to show all interfaces(?!)
        So we wrote our own instead. A work in progress but quite functional at the moment. """

    utility.log(pilib.dirs.logs.network, 'Reading ifaces with ifconfig status. ', 4, pilib.loglevels.network)
    ifacesdictarray = getifconfigstatus()
    # ifacesdictarray = getifacestatus()

    """ We supplement with wpa status on the wlan interfaces """

    updateddictarray = []
    for interface in ifacesdictarray:
        if interface['name'].find('wlan') >= 0:
            interface['wpastate'] = utility.dicttojson(getwpaclientstatus(interface['name']))
        else:
            interface['wpastate'] = ''
        updateddictarray.append(interface)
    ifacesdictarray = updateddictarray

    """ Then write it to the table """

    if ifacesdictarray:
        utility.log(pilib.dirs.logs.network, 'Sending ifaces query. ', 5, pilib.loglevels.network)
        # print(ifacesdictarray)
        dblib.insertstringdicttablelist(pilib.dirs.dbs.system, 'netifaces', ifacesdictarray, droptable=True)
    else:
        utility.log(pilib.dirs.logs.network, 'Empty ifaces query. ', 2, pilib.loglevels.network)

    utility.log(pilib.dirs.logs.network, 'Completed ifaces. ', 4, pilib.loglevels.network)

    """ Now we check to see if we can connect to WAN """

    utility.log(pilib.dirs.logs.network, 'Checking pingtimes. ', 4, pilib.loglevels.network)
    okping = float(netconfigdata['pingthreshold'])

    netstatusdict = {}

    querylist=[]
    pingresults = netfun.runping('8.8.8.8')

    # pingresults = [20, 20, 20]
    pingresult = sum(pingresults) / float(len(pingresults))

    if pingresult == 0:
        wanaccess = 0
        latency = 0
    else:
        latency = pingresult
        if pingresult < okping:
            wanaccess = 1
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccess', 1)
            if lastnetstatus['WANaccess'] == 0 or not lastnetstatus['onlinetime']:
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'onlinetime', datalib.gettimestring())

        else:
            wanaccess = 0

    if not wanaccess:
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccess', 0)
        if lastnetstatus['WANaccess'] == 1 or not lastnetstatus['offlinetime']:
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'offlinetime', datalib.gettimestring())

    # we set all the values here, so when we retreive it we get changed and also whatever else happens to be there.
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'latency', latency)
    updatetime = datalib.gettimestring()
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'updatetime', updatetime)
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccess', wanaccess)

    utility.log(pilib.dirs.logs.network, 'Done checking pings. ', 4, pilib.loglevels.network)

    if netconfigdata['netstatslogenabled']:
        # print('going to log stuff')
        dblib.logtimevaluedata(pilib.dirs.dbs.log, 'system_WANping', time.time(), pingresult, 1000,
                               netconfigdata['netstatslogfreq'])

    #This is kinda ugly. Should be fixed.
    # netstatusdict = {'WANaccess':wanaccess, 'latency': latency, 'updatetime': updatetime}
    netstatusdict = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]

    return {'netstatusdict': netstatusdict, 'ifacesdictarray': ifacesdictarray, 'netconfigdata':netconfigdata}


def processapoverride(pin):
    from iiutilities import utility
    from iiutilities.dblib import setsinglevalue
    import pilib
    utility.log(pilib.dirs.logs.network, "Reading GPIO override on pin " + str(pin) + '. ', 3, pilib.loglevels.network)
    utility.log(pilib.dirs.logs.system, "Reading GPIO override on pin " + str(pin) + '. ', 2, pilib.loglevels.system)

    import RPi.GPIO as GPIO
    import pilib

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    except:
        utility.log(pilib.dirs.logs.network, "Error reading GPIO", 3, pilib.loglevels.network)
    else:
        # jumper in place = input off, --> AP mode
        if not GPIO.input(pin):
            utility.log(pilib.dirs.logs.network, "GPIO On. Setting AP Mode.", 3, pilib.loglevels.network)
            setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'mode', 'ap')
        # else:
        #     pilib.writedatedlogmsg(pilib.dirs.logs.network, "GPIO Off. Setting Station Mode.", 3, pilib.loglevels.network)
        #     pilib.setsinglevalue(pilib.systemdatadatabase, 'netconfig', 'mode', 'station')


def processsystemflags(systemflags=None):
    from cupid import pilib
    from iiutilities import dblib
    from iiutilities import utility


    if not systemflags:
        systemflags = dblib.readalldbrows(pilib.dirs.dbs.system, 'systemflags')

    flagnames = []
    flagvalues = []
    for flag in systemflags:
        flagnames.append(flag['name'])
        flagvalues.append(flag['value'])

    stop = False
    if 'reboot' in flagnames:
        if flagvalues[flagnames.index('reboot')]:
            stop = True
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemflags', 'value', 0, "name='reboot'")
            import subprocess

            utility.log(pilib.dirs.logs.system, 'Rebooting for system flag', 0, pilib.loglevels.system)
            subprocess.call(['/sbin/reboot'])
    if 'netconfig' in flagnames:
        if flagvalues[flagnames.index('netconfig')]:
            stop = True
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemflags', 'value', 0, "name='netconfig'")
            from netconfig import runconfig

            utility.log(pilib.dirs.logs.system, 'Restarting network configuration', 0, pilib.loglevels.system)
            runconfig()
    if 'updateiicontrollibs' in flagnames and not stop:
        if flagvalues[flagnames.index('updateiicontrollibs')]:
            stop = True
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemflags', 'value', 0, 'name=\'updateiicontrollibs\'')
            from iiutilities.gitupdatelib import updateiicontrollibs

            utility.log(pilib.dirs.logs.system, 'Updating iicontrollibs', 0, pilib.loglevels.system)
            updateiicontrollibs(True)
    if 'updatecupidweblib' in flagnames and not stop:
        if flagvalues[flagnames.index('updatecupidweblib')]:
            stop = True
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemflags', 'value', 0, 'name=\'updatecupidweblib\'')
            from iiutilities.gitupdatelib import updatecupidweblib

            utility.log(pilib.dirs.logs.system, 'Updating cupidweblib', 0, pilib.loglevels.system)
            updatecupidweblib(True)


def piversiontoversionname(version):

    detail = ''
    if version == '0002':
        versionname = 'Model B Revision 1.0'
        memory=256
    elif version == '0003':
        versionname = 'Model B Revision 1.0 + ECN0001'
        memory=256
    elif version in ['0004', '0005', '0006']:
        versionname = 'Model B Revision 2.0'
        memory=256
    elif version in ['0007', '0008', '0009']:
        versionname = 'Model A'
        memory=256
    elif version in ['000d', '000e', '000f']:
        versionname = 'Model B Revision 2.0'
        memory=512
    elif version == '0010':
        versionname = 'Model B+'
        memory=512
    elif version == '0011':
        versionname = 'Compute Module'
        memory=512
    elif version == '0012':
        versionname = 'Model A+'
        memory=256
    elif version in ['a01041', 'a21041']:
        versionname = 'Pi 2 Model B'
        memory=1024
    elif version == '900092':
        versionname = 'PiZero'
        memory=512
    elif version in ['a02082', 'a22082']:
        versionname = 'Pi 3 Model B'
        memory=1024
    else:
        versionname = 'not found'
        memory = 'unknown'

    return {'versionname':versionname, 'memory':memory, 'detail':detail}



def updatehardwareinfo(databasename='systemdatadb'):
    from subprocess import check_output
    from cupid import pilib
    from iiutilities import datalib
    from iiutilities import dblib
    from iiutilities import utility

    data = check_output(['cat','/proc/cpuinfo'])
    items = data.split('\n')
    dict = {}
    for item in items:
        try:
            dict[item.split(':')[0].strip()] = item.split(':')[1].strip()
        except:
            pass

    dictstring = utility.dicttojson(dict)
    dbpath = None
    try:
        dbpath = pilib.dbnametopath(databasename)
        # print(dbpath)
    except:
        pass

    if dbpath:
        time = datalib.gettimestring()
        dblib.sqliteinsertsingle(dbpath,'versions',['cpuinfo', dictstring, time, ''],['item', 'version', 'updatetime', 'versiontime'],)

    if 'Revision' in dict and dbpath:
        versiondetail = piversiontoversionname(dict['Revision'])
        dblib.sqliteinsertsingle(dbpath, 'versions', ['versionname', versiondetail['versionname'], time, ''],['item', 'version', 'updatetime', 'versiontime'],)
        dblib.sqliteinsertsingle(dbpath, 'versions', ['memory', versiondetail['memory'], time, ''],['item', 'version', 'updatetime', 'versiontime'],)
    return dictstring


def runsystemstatus(runonce=False):
    import pilib
    import time
    from iiutilities import utility
    from iiutilities import dblib
    from iiutilities import datalib

    from iiutilities.gitupdatelib import updategitversions

    # This doesn't update git libraries. It checks current versions and updates the database

    try:
        utility.log(pilib.dirs.logs.system, 'Checking git versions', 3, pilib.loglevels.system)
        updategitversions()
    except:
        utility.log(pilib.dirs.logs.system, 'Error in git version check', 0, pilib.loglevels.system)
    else:
        utility.log(pilib.dirs.logs.system, 'Git version check complete', 3, pilib.loglevels.system)

    systemstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'systemstatus')[0]

    # Get hardware info
    updatehardwareinfo()

    ## Read wireless config via iwconfig
    # this is breaking systemstatus for some reason
    # updateiwstatus()

    ## Read current netstatus
    lastnetstatus={}
    try:
        lastnetstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]
    except:
        utility.log(pilib.dirs.logs.network, 'Error reading network status. ', 1, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.system, 'Completed network status. ', 3, pilib.loglevels.network)

    # Poll netstatus and return data
    allnetstatus = updatenetstatus(lastnetstatus)
    # wpastatusdict = allnetstatus['wpastatusdict']

    # Keep reading system status?
    while systemstatus['systemstatusenabled']:

        # Run notifications
        pilib.processnotificationsqueue()

        currenttime = datalib.gettimestring()
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastsystemstatuspoll', datalib.gettimestring())

        starttime = time.time()
        utility.log(pilib.dirs.logs.system, 'System status routine is starting. ', 3,
                      pilib.loglevels.system)

        """
        Check all network statuses. The goal here is to totally decouple status read and reconfigure
        When we need to check all status data, we'll have it either in a dict or dict array, or in a database table
        """

        if systemstatus['netstatusenabled']:
            utility.log(pilib.dirs.logs.system, 'Beginning network routines. ', 3, pilib.loglevels.system)

            # Update network interfaces statuses for all interfaces, in database tables as well
            # Check on wpa supplicant status as well. Function returns wpastatusdict
            try:
                utility.log(pilib.dirs.logs.system, 'Running updateifacestatus. ', 4, pilib.loglevels.system)
                utility.log(pilib.dirs.logs.network, 'Running updateifacestatus', 4, pilib.loglevels.network)
                allnetstatus = updatenetstatus(lastnetstatus)
            except:
                utility.log(pilib.dirs.logs.network, 'Exception in updateifacestatus. ')
            else:
                utility.log(pilib.dirs.logs.network, 'Updateifacestatus completed. ')

            utility.log(pilib.dirs.logs.system, 'Completed net status update. ', 4, pilib.loglevels.system)
        else:
            allnetstatus={'netstatusdict': {}, 'ifacesdictarray': {}}


        """
        End network configuration status
        """

        """
        Do we want to autoconfig the network? If so, we analyze our netstatus data against what should be going on,
        and translate this into a network status
        """
        if systemstatus['netconfigenabled'] and systemstatus['netstatusenabled']:

            # No need to get this fresh. We have it stored.
            netconfigdata = allnetstatus['netconfigdata']

            # We are going to hack in a jumper that sets AP configuration. This isn't the worst thing ever.
            if netconfigdata['apoverride']:
                result = processapoverride(21)

            ''' Now we check network status depending on the configuration we have selected '''
            ''' Now we check network status depending on the configuration we have selected '''
            utility.log(pilib.dirs.logs.system, 'Running interface configuration watchdog. ', 4,
                          pilib.loglevels.system)
            utility.log(pilib.dirs.logs.network, 'Running interface configuration. Mode: ' + netconfigdata['mode'], 4,
                          pilib.loglevels.network)

            result = watchdognetstatus()

        else:
            utility.log(pilib.dirs.logs.system, 'Netconfig disabled. ', 1, pilib.loglevels.system)
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'mode', 'manual')
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', 'netconfig is disabled')

        if systemstatus['checkhamachistatus']:
            utility.log(pilib.dirs.logs.system, 'Hamachi watchdog is enabled', 3, pilib.loglevels.system)
            utility.log(pilib.dirs.logs.network, 'Hamachi watchdog is enabled. ', 3, pilib.loglevels.network)

            # Only watchdog haamchi if we are connected to the network.
            netstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]
            if netstatus['WANaccess']:
                utility.log(pilib.dirs.logs.system, 'We appear to be online. Checking Hamachi Status. ', 3, pilib.loglevels.system)
                utility.log(pilib.dirs.logs.network, 'We appear to be online. Checking Hamachi Status. ', 3, pilib.loglevels.network)
                watchdoghamachi(pingip='25.37.18.7')
                utility.log(pilib.dirs.logs.system, 'Completed checking Hamachi Status. ', 3, pilib.loglevels.network)
                utility.log(pilib.dirs.logs.system, 'Completed checking Hamachi Status. ', 3, pilib.loglevels.network)

            else:
                utility.log(pilib.dirs.logs.system, 'We appear to be offline. Not checking Hamachi Status, but setting to 0. ', 3, pilib.loglevels.system)
                utility.log(pilib.dirs.logs.network, 'We appear to be offline. Not checking Hamachi Status, but setting to 0. ', 3, pilib.loglevels.network)
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'hamachistatus', 0)
        else:
            utility.log(pilib.dirs.logs.system, 'Hamachi watchdog is disabled', 3, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'Finished interface configuration. ', 4,
                      pilib.loglevels.system)
        # pilib.writedatedlogmsg(pilib.dirs.logs.network, statusmsg)

        utility.log(pilib.dirs.logs.system, 'Running updateifacestatus. ', 4, pilib.loglevels.system)
        updatenetstatus()
        utility.log(pilib.dirs.logs.system, 'Completed updateifacestatus. ', 4, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'Network routines complete. ', 3, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'Checking system flags. ', 3, pilib.loglevels.system)
        processsystemflags()
        utility.log(pilib.dirs.logs.system, 'System flags complete. ', 3, pilib.loglevels.system)

        # Get system status again
        systemstatus = dblib.readalldbrows(pilib.dirs.dbs.system, 'systemstatus')[0]

        elapsedtime = int(time.time() - starttime)

        utility.log(pilib.dirs.logs.system, 'Status routines complete. Elapsed time: ' + str(elapsedtime), 3,
                      pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system,
                               'System status is sleeping for ' + str(systemstatus['systemstatusfreq']) + '. ', 3,
                      pilib.loglevels.system)

        if runonce:
            break

        time.sleep(systemstatus['systemstatusfreq'])


    else:
        utility.log(pilib.dirs.logs.system, 'System status is disabled. Exiting. ', 0,
                      pilib.loglevels.system)


if __name__ == '__main__':
    runsystemstatus()
