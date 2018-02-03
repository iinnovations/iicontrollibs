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

try:
    import simplejson as json
except:
    import json
#
# def readhardwarefileintoversions():
#
#     from iiutilities import utility
#     from cupid import pilib
#     from iiutilities import dblib
#
#     devicefile = '/var/wwwsafe/devicedata'
#     try:
#         file = open(devicefile)
#         lines = file.readlines()
#         devicedict = {}
#         for line in lines:
#             split = line.split(':')
#             try:
#                 devicedict[split[0].strip()] = split[1].strip()
#             except:
#                 utility.log(pilib.dirs.logs.system, 'Device data parse error', 1, pilib.loglevels.system)
#         dblib.sqlitequery(pilib.dirs.dbs.system,
#                           dblib.makesqliteinsert('versions', ['hardware', devicedict['hardware']], ['item', 'version']))
#     except:
#         utility.log(pilib.dirs.logs.system, 'Error opening devicedata file to parse', 1,
#                       pilib.loglevels.system)


def updateiwstatus():

    from iiutilities.netfun import getiwstatus
    from iiutilities.datalib import gettimestring
    from cupid.pilib import dirs
    from iiutilities.dblib import insertstringdicttablelist

    iwdict = getiwstatus()
    iwdict['updatetime'] = gettimestring()

    # put into database
    insertstringdicttablelist(dirs.dbs.system, 'iwstatus', [iwdict], droptable=True)


def watchdoghamachi(pingip='self', threshold=3000, debug=False, restart=True):
    from iiutilities.netfun import runping, restarthamachi, killhamachi, gethamachistatusdata
    from iiutilities import utility
    from iiutilities import dblib
    from cupid import pilib

    if debug:
        pilib.set_debug()

    try:
        # if this throws an error, it means that there is not a valid status
        hamachistatusdata = gethamachistatusdata()
    except:
        import traceback
        error_message = traceback.format_exc()
        print(error_message)
        utility.log(pilib.dirs.logs.network, 'Error checking Hamachi via gethamachistatusdata with message:  {}'.format(error_message), 1,
                pilib.loglevels.network)
        hamachistatusdata = {}

    # We are having some issue with return on hamachi status check. This is not always a reason to restart hamachi
    # We will carry on below and try to ping. if we can ping, we are good. if we need to self ping, this will still
    # Throw errors. BUT, main point is that if we can ping our chosen hamachi address, we are good.

    try:

        # So instead, we are going to test with a ping to another member on the network that
        # should always be online. This of course means that we have to make sure that it is, in fact, always
        # online
        if pingip in ['self', 'Self']:
            pingip = hamachistatusdata['address']

        pingtimes = runping(pingip, numpings=15, quiet=True)
        pingmax = max(pingtimes)
        pingmin = min(pingtimes)
        pingave = sum(pingtimes)/len(pingtimes)

        # if hamachistatusdata['status'] not in ['logged in']:
        if pingave <= 0 or pingave > threshold:
            utility.log(pilib.dirs.logs.network, 'Pingtime unacceptable: ' + str(pingave) + '. ', 1, pilib.loglevels.network)
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'hamachistatus', 0)
            utility.log(pilib.dirs.logs.network, 'Restarting Hamachi. ', 1, pilib.loglevels.network)

            # killhamachi()
            restarthamachi()
            utility.log(pilib.dirs.logs.network, 'Completed restarting Hamachi. ', 1, pilib.loglevels.network)

        else:
            if pingmax > threshold or pingmin <= 0:
                utility.log(pilib.dirs.logs.system, 'Hamachi lives, with issues: ' + str(pingtimes), 3, pilib.loglevels.system)
            else:
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'hamachistatus', 1)
                utility.log(pilib.dirs.logs.network, 'Hamachi appears fine. ', 3, pilib.loglevels.network)

    except:
        import traceback
        error_message = traceback.format_exc()

        utility.log(pilib.dirs.logs.network, 'Error checking Hamachi (second stage, pings) with message:  {}'.format(error_message), 1, pilib.loglevels.network)

        if restart:
            utility.log(pilib.dirs.logs.network, 'Restarting hamachi:  {}'.format(error_message), 1,
                        pilib.loglevels.network)

            killhamachi()
            restarthamachi()
        # print('blurg')


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


def check_interface_status(iface_config, iface_status):
    import pilib
    from iiutilities import utility
    # print("CONFIG")
    # print(iface_config)
    # print("STATUS")
    # print(iface_status)
    utility.log(pilib.dirs.logs.network, 'Checking configuration of interface {} type: {}. '.format(
        iface_config['name'], iface_config['mode']), 3, pilib.loglevels.network)

    return_dict = {'status':'ok', 'status_message':''}

    # Check address exists
    if iface_config['mode'] in ['ap', 'station', 'dhcp', 'static']:
        if 'address' not in iface_status['config']:
            new_message = 'no address present. Status: {}'.format(iface_status)
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status_message'] += new_message
            return_dict['status'] = 'fail'
            return return_dict

    # Check for address match
    if iface_config['mode'] in ['ap', 'static']:
        if iface_status['config']['address'] != iface_config['config']['address']:
            print(iface_config)
            print(iface_status)
            new_message = 'Address mismatch. Expected {}. Found {}. '.format(iface_config['address'], iface_status['address'])
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status_message'] += new_message

    # Check AP Mode
    if iface_config['mode'] in ['ap']:
        from netconfig import get_dhcp_status, get_hostapd_status

        # Check dhcp server
        iface_status['config']['dhcpstatus'] = get_dhcp_status()
        if not iface_status['config']['dhcpstatus']['status']:
            new_message = 'AP dhcp status checked and ok. '
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status_message'] += new_message
        else:
            new_message = 'AP dhcp status is not ok. '
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status'] = 'fail'
            return_dict['status_message'] += new_message
            return return_dict

        # Check hostapd
        iface_status['config']['hostapdstatus'] = get_hostapd_status()
        if not iface_status['config']['hostapdstatus']['status']:
            new_message = 'AP hostapd status checked and ok. '
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status_message'] += new_message
        else:
            new_message = 'AP hostapd status is not ok. '
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status'] = 'fail'
            return_dict['status_message'] += new_message
            return return_dict

    # Check for wpa state
    if iface_config['mode'] in ['station']:
        print('STATION')
        print(iface_status)
        if 'wpastate' not in iface_status['config']:
            new_message = 'No wpa state present in iface_status. '
            utility.log(pilib.dirs.logs.network, new_message, 1, pilib.loglevels.network)
            return_dict['status'] = 'fail'
            return_dict['status_message'] += new_message
            return return_dict

        wpadata = iface_status['config']['wpastate']
        if wpadata['wpa_state'] == 'COMPLETED':
            new_message = 'wpa state appears ok for interface. '
            utility.log(pilib.dirs.logs.network, new_message, 3, pilib.loglevels.network)
            return_dict['status_message'] += new_message
        else:
            new_message = 'wpa state appears BAD for interface: {} '.format(wpadata['wpastate'])
            utility.log(pilib.dirs.logs.network, new_message, 3, pilib.loglevels.network)
            return_dict['status_message'] += new_message
            return_dict['status'] = 'fail'

    return return_dict


def watchdognetstatus(allnetstatus={}):

    from iiutilities import utility
    from cupid import pilib
    from iiutilities import datalib
    from cupid import netconfig
    from iiutilities import dblib

    """
    And now comes the checking of configuration specific statuses and restarting them if enabled
    and necessary

    We are getting updated status information for each interface. 
    
    We have configuration info for interfaces. We compare the two based on mode and decide if we need to run 
    a netconfig on each interface. We do this by running through, interface by interface on netconfigstatus, and 
    comparing. We then add the name to interfaces we need to reconfig and pass to netconfig().
    
    We ignore interfaces we don't have a config for so we ignore things like hamachi interfaces, loopback, GSM, etc.

    """

    if 'ifaces_config' not in allnetstatus or 'ifaces_status' not in allnetstatus:
        print('WE DID NOT FIND THINGS')
        allnetstatus = update_net_status()

    netconfig_data = allnetstatus['netconfig_data']
    netstatus = allnetstatus['netstatusdict']
    ifaces_config = allnetstatus['ifaces_config']
    ifaces_status = allnetstatus['ifaces_status']


    statusmsg = ''
    currenttime = datalib.gettimestring()

    reconfig_interfaces = []
    for iface_name, iface_status in ifaces_status.items():
        utility.log(pilib.dirs.logs.network, 'Checking status of interface {}. '.format(iface_name, 3, pilib.loglevels.network))
        if iface_status['status'] == 'fail':
            reconfig_interfaces.append(iface_name)
            utility.log(pilib.dirs.logs.network,
                'Interface has faile status. Setting reconfig for {}. '.format(iface_name, 1, pilib.loglevels.network))


    # Now do some sleuthing if we are being stringent about WAN access. Have to be careful about this if we are on a
    # private network

    run_WAN_reconfig = False
    if netconfig_data['requireWANaccess']:
        utility.log(pilib.dirs.logs.network, 'Requiring WAN access. Checking status and times. ', 3, pilib.loglevels.network)
        # print('NETSTATUS')
        # print(netstatus)
        if not netstatus['WANaccess']:
            utility.log(pilib.dirs.logs.network, 'No WANaccess. Checking offline time. ', 2, pilib.loglevels.network)
            try:
                offlinetime = netstatus['offlinetime']
            except:
                # print('netstatus ERROR')
                utility.log(pilib.dirs.logs.network, 'Error getting offlinetime. ', 2, pilib.loglevels.network)


            offlineperiod = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(offlinetime)

            utility.log(pilib.dirs.logs.network, 'We have been offline for ' + str(offlineperiod))

            # When did we last restart the network config? Is it time to again?
            timesincelastnetrestart = datalib.timestringtoseconds(
                datalib.gettimestring()) - datalib.timestringtoseconds(netstatus['lastnetreconfig'])

            utility.log(pilib.dirs.logs.network, 'It has been ' + str(timesincelastnetrestart) + ' seconds since we last restarted the network configuration. ')

            # Require that offline time is greater than WANretrytime
            if timesincelastnetrestart > int(netconfig_data['WANretrytime']) and offlineperiod >  int(netconfig_data['WANretrytime']):
                utility.log(pilib.dirs.logs.network, 'We are not online, and it has been long enough, exceeding retry time of ' + str(int(netconfig_data['WANretrytime'])))
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'lastnetreconfig', datalib.gettimestring())

                # We do reset the WAN offline time in the reboot sequence, hwoever.

                restarts = int(dblib.getsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccessrestarts'))
                restarts += 1
                dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccessrestarts', restarts)

                utility.log(pilib.dirs.logs.network, 'Going to run netconfig to correct WAN access.')
                run_WAN_reconfig = True

            else:
                utility.log(pilib.dirs.logs.network, 'Not yet time to run netconfig to correct WAN access. Retry time set at ' + str(netconfig_data['WANretrytime']))
        else:
            utility.log(pilib.dirs.logs.network, 'WANAccess is fine. ')

    if run_WAN_reconfig:
        # Set bad status in netstatus
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstate', 0)

        # Set ok time to '' to trigger rewrite next time status is ok
        lastoktime = dblib.getsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime')
        if not lastoktime:
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime', datalib.gettimestring())
        else:
            if netconfig_data['rebootonfail']:
                offlinetime = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(lastoktime)
                if offlinetime > int(netconfig_data['rebootonfailperiod']):

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


        # Figure out which interfaces to restart to fix WAN issues

        for interface_name, interface in ifaces_config.items():
            utility.log(pilib.dirs.logs.network, 'Adding interface {} to reconfig list'.format(interface_name), 1, pilib.loglevels.network)
            if interface['mode'] in ['status', 'station', 'dhcp']:
                reconfig_interfaces.append(interface_name)

    else:
        # Clear bad status in netstatus and set netoktime
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', 'Mode appears to be set.')
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstate', 1)
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'netstateoktime', datalib.gettimestring())

    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', statusmsg)
    if reconfig_interfaces:
        utility.log(pilib.dirs.logs.network, 'Running netreconfig on list: {}'.format(reconfig_interfaces), 1,
                    pilib.loglevels.network)

        netconfig.runconfig(ifaces_to_configure=reconfig_interfaces, config=ifaces_config, config_all=False)


def update_net_status(lastnetstatus=None, quiet=True, ifaces_config=None, netconfig_data=None):

    """
    This function does two main things:

    1. Updates netstatus table. This table contains overall status information, i.e. whether we are attached to WAN,
    hamachi, etc.

    2. Updates netiface_status table (previously netifaces table). This does some contextual stuff like getting wpastate
    info if it makes sense based on mode. Trying to get wpastate data on interfaces that don't matter is not a big deal,
    except that it takes a little time. No need wasting time if the interface is not configured to use wpa.

    3. For interfaces that have a configuration, sets status in netifaces_status based on mode

    """

    import time
    from iiutilities import netfun
    from iiutilities import dblib
    from cupid import pilib
    from iiutilities import utility
    from iiutilities import datalib
    from iiutilities.netfun import getifconfigstatus, getwpaclientstatus

    if not netconfig_data:
        netconfig_data = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]

    if not ifaces_config:

        # Get config data
        ifaces_config = pilib.dbs.system.read_table('netifaceconfig', keyed_dict=True)

        # Unpack config
        for interface_name, element in ifaces_config.items():
            element['config'] = json.loads(element['config'])

    """ 
    We get last netstatus so that we can save last online times, previous online status, etc. 
    """

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

    utility.log(pilib.dirs.logs.network, 'Reading ifaces with ifconfig status. ', 4, pilib.loglevels.network)

    # Returns a dictionary, config is unpacked
    ifaces_status = getifconfigstatus()

    """
    We supplement with wpa status on the wlan interfaces if station mode should be set
    Here, we need to decide which interfaces should have a proper wpa status
    """

    for interface_name, this_interface_config in ifaces_config.items():
        this_interface_status = ifaces_status[interface_name]

        # Insert mode into status
        this_interface_status['mode'] = this_interface_config['mode']

        # this_interface_status = json.loads(this_interface_status['config'])
        if this_interface_config['mode'] == 'station':
            this_interface_status['config']['wpastate'] = getwpaclientstatus(interface_name)
        else:
            this_interface_status['config']['wpastate'] = ''

        this_interface_status_result = check_interface_status(this_interface_config, this_interface_status)

        this_interface_status['status'] = this_interface_status_result['status']
        this_interface_status['status_message'] = this_interface_status_result['status_message']


    """ 
    Then write it to the table 
    TODO : Double-check no problems here with not recreating status from scratch (stale data, et.)
    """

    utility.log(pilib.dirs.logs.network, 'Sending ifaces query \n {}. '.format(ifaces_status), 5, pilib.loglevels.network)
        # print(ifacesdictarray)
    this_schema = dblib.sqliteTableSchema([
        {'name':'name', 'primary':True},
        {'name':'config'},
        {'name':'status'},
        {'name':'status_message'},
        {'name':'mode'}
    ])

    pilib.dbs.system.create_table('netifacestatus', schema=this_schema, queue=True)
    from copy import deepcopy
    # print('IFACES')
    # print(ifaces_status)
    for interface_name, interface in ifaces_status.items():
        insert = deepcopy(interface)

        # Pack up the interface configuration data
        try:
            insert['config'] = json.dumps(interface['config'])
        except:
            print('error with iterface {}'.format(interface_name))
            print(interface)

        pilib.dbs.system.insert('netifacestatus', insert, queue=True)

    """ Now we check to see if we can connect to WAN """

    utility.log(pilib.dirs.logs.network, 'Checking pingtimes. ', 4, pilib.loglevels.network)
    okping = float(netconfig_data['pingthreshold'])

    pingresults = netfun.runping('8.8.8.8', quiet=quiet)

    # pingresults = [20, 20, 20]
    pingresult = sum(pingresults) / float(len(pingresults))

    if pingresult == 0:
        wanaccess = 0
        latency = 0
    else:
        latency = pingresult
        if pingresult < okping:
            wanaccess = 1
            pilib.dbs.system.set_single_value('netstatus', 'WANaccess', 1, queue=True)
            if lastnetstatus['WANaccess'] == 0 or not lastnetstatus['onlinetime']:
                lastnetstatus['onlinetime'] = datalib.gettimestring()

        else:
            wanaccess = 0

    if not wanaccess:
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'WANaccess', 0)
        if lastnetstatus['WANaccess'] == 1 or not lastnetstatus['offlinetime']:
            lastnetstatus['offlinetime'] = datalib.gettimestring()

    # we set all the values here, so when we retreive it we get changed and also whatever else happens to be there.
    lastnetstatus['latency'] = latency
    lastnetstatus['updatetime'] =  datalib.gettimestring()
    lastnetstatus['WANaccess'] = wanaccess

    # pilib.dbs.system.insert('netstatus', lastnetstatus, queue=True)

    utility.log(pilib.dirs.logs.network, 'Done checking pings. ', 4, pilib.loglevels.network)

    if netconfig_data['netstatslogenabled']:
        # print('going to log stuff')
        dblib.logtimevaluedata(pilib.dirs.dbs.log, 'system_WANping', time.time(), pingresult, 1000,
                               netconfig_data['netstatslogfreq'])

    #This is kinda ugly. Should be fixed.
    # netstatusdict = {'WANaccess':wanaccess, 'latency': latency, 'updatetime': updatetime}

    pilib.dbs.system.execute_queue(debug=True)
    return {'netstatusdict': lastnetstatus, 'ifaces_status': ifaces_status, 'ifaces_config':ifaces_config,
            'netconfig_data':netconfig_data}


def processapoverride(pin):
    from iiutilities import utility
    from iiutilities.dblib import setsinglevalue
    import pilib
    utility.log(pilib.dirs.logs.network, "Reading GPIO override on pin " + str(pin) + '. ', 3, pilib.loglevels.network)
    utility.log(pilib.dirs.logs.system, "Reading GPIO override on pin " + str(pin) + '. ', 2, pilib.loglevels.system)

    import RPi.GPIO as GPIO
    import pilib

    try:
        GPIO.set_mode(GPIO.BCM)
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
        systemflags = pilib.dbs.system.read_table('systemflags')

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


def updatehardwareinfo(databasename='systemdb'):
    from subprocess import check_output
    from cupid import pilib
    from iiutilities import datalib
    from iiutilities import dblib
    import json

    data = check_output(['cat','/proc/cpuinfo']).decode('utf-8')
    items = data.split('\n')
    hw_dict = {}
    for item in items:
        try:
            hw_dict[item.split(':')[0].strip()] = item.split(':')[1].strip()
        except:
            pass

    # print('HW DICT')
    # print(hw_dict)

    dictstring = json.dumps(hw_dict)
    dbpath = None
    try:
        dbpath = pilib.dbnametopath(databasename)
        # print(dbpath)
    except:
        pass

    if dbpath:
        time = datalib.gettimestring()
        dblib.sqliteinsertsingle(dbpath,'versions',['cpuinfo', dictstring, time, ''],['item', 'version', 'updatetime', 'versiontime'],)

    if 'Revision' in hw_dict and dbpath:
        versiondetail = piversiontoversionname(hw_dict['Revision'])
        dblib.sqliteinsertsingle(dbpath, 'versions', ['versionname', versiondetail['versionname'], time, ''],['item', 'version', 'updatetime', 'versiontime'],)
        dblib.sqliteinsertsingle(dbpath, 'versions', ['memory', versiondetail['memory'], time, ''],['item', 'version', 'updatetime', 'versiontime'],)
    return dictstring


def run_system_status(**kwargs):
    import pilib
    import time
    from iiutilities import utility
    from iiutilities import dblib
    from iiutilities import datalib
    from iiutilities import gitupdatelib
    from iiutilities import data_agent

    settings = {
        'debug':False,
        'quiet':False
    }
    settings.update(kwargs)

    if settings['debug']:
        print('DEBUG MODE')
        settings['quiet']=False
        pilib.set_debug()

    # This doesn't update git libraries. It checks current versions and updates the database

    try:
        utility.log(pilib.dirs.logs.system, 'Checking git versions', 3, pilib.loglevels.system)
        gitupdatelib.updaterepoversion(pilib.dirs.baselib, pilib.dirs.dbs.system, versiontablename='versions')
        gitupdatelib.updaterepoversion(pilib.dirs.web, pilib.dirs.dbs.system, versiontablename='versions')
    except:
        utility.log(pilib.dirs.logs.system, 'Error in git version check', 0, pilib.loglevels.system)
    else:
        utility.log(pilib.dirs.logs.system, 'Git version check complete', 3, pilib.loglevels.system)

    systemstatus = pilib.dbs.system.read_table_row('systemstatus')[0]

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

    # # Poll netstatus and return data
    # allnetstatus = updatenetstatus(lastnetstatus, quiet=settings['quiet'])

    # Keep reading system status?
    while systemstatus['systemstatusenabled']:

        # Run notifications
        pilib.process_notifications_queue()

        try:
            data_agent.run_data_agent()
        except:
            utility.log(pilib.dirs.logs.system, 'Error running data agent. ', 1, pilib.loglevels.network)
        else:
            utility.log(pilib.dirs.logs.system, 'Data agent run successfully. ', 3, pilib.loglevels.network)


        currenttime = datalib.gettimestring()
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', 'lastsystemstatuspoll', datalib.gettimestring())

        starttime = time.time()
        utility.log(pilib.dirs.logs.system, 'System status routine is starting. ', 3,
                      pilib.loglevels.system)

        """
        Check all network statuses. The goal here is to totally decouple status read and reconfigure
        When we need to check all status data, we'll have it either in a dict or dict array, or in a database table
        
        This sub will read config and status and give both overall and granular interface statuses.
        Then, if status is not 'ok', we will reconfigure interface.
        """

        allnetstatus = update_net_status(lastnetstatus, quiet=settings['quiet'])

        if systemstatus['netstatusenabled']:
            utility.log(pilib.dirs.logs.system, 'Beginning network routines. ', 3, pilib.loglevels.system)

            # Update network interfaces statuses for all interfaces, in database tables as well
            # Check on wpa supplicant status as well. Function returns wpastatusdict
            try:
                utility.log(pilib.dirs.logs.system, 'Running updateifacestatus. ', 4, pilib.loglevels.system)
                utility.log(pilib.dirs.logs.network, 'Running updateifacestatus', 4, pilib.loglevels.network)
                allnetstatus = update_net_status(lastnetstatus, quiet=settings['quiet'])
            except:
                utility.log(pilib.dirs.logs.network, 'Exception in updateifacestatus. ')
            else:
                utility.log(pilib.dirs.logs.network, 'Updateifacestatus completed. ')

            utility.log(pilib.dirs.logs.system, 'Completed net status update. ', 4, pilib.loglevels.system)

        """
        End network configuration status
        """


        """
        Do we want to autoconfig the network? 
        
        If so, we analyze our netstatus data against what should be going on,
        and translate this into a network status. We have a list of ifaceconfigs and a list if ifacestatus
        """
        if systemstatus['netconfigenabled'] and systemstatus['netstatusenabled']:

            # No need to get this fresh. We have it stored.
            netconfig_data = allnetstatus['netconfig_data']

            # We are going to hack in a jumper that sets AP configuration. This isn't the worst thing ever.
            # if netconfig_data['apoverride']:
            #     result = processapoverride(21)

            ''' Now we check network status depending on the configuration we have selected '''
            utility.log(pilib.dirs.logs.system, 'Running interface configuration watchdog. ', 4,
                          pilib.loglevels.system)
            utility.log(pilib.dirs.logs.network, 'Running interface configuration. Mode: ' + netconfig_data['mode'], 4,
                          pilib.loglevels.network)
            print('ALL IFACE STATUS')
            print(allnetstatus['ifaces_status'])

            result = watchdognetstatus(allnetstatus=allnetstatus)

        else:
            utility.log(pilib.dirs.logs.system, 'Netconfig or netstatus disabled. ', 1, pilib.loglevels.system)
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'mode', 'manual')
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'statusmsg', 'netconfig is disabled')

        """ Check Hamachi """
        if systemstatus['checkhamachistatus']:
            utility.log(pilib.dirs.logs.system, 'Hamachi watchdog is enabled', 3, pilib.loglevels.system)
            utility.log(pilib.dirs.logs.network, 'Hamachi watchdog is enabled. ', 3, pilib.loglevels.network)

            # Only watchdog haamchi if we are connected to the network.
            netstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'netstatus')[0]
            if netstatus['WANaccess']:
                utility.log(pilib.dirs.logs.system, 'We appear to be online. Checking Hamachi Status. ', 3, pilib.loglevels.system)
                utility.log(pilib.dirs.logs.network, 'We appear to be online. Checking Hamachi Status. ', 3, pilib.loglevels.network)
                
                watchdoghamachi(pingip='25.11.87.7')

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

        update_net_status()

        utility.log(pilib.dirs.logs.system, 'Completed updateifacestatus. ', 4, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'Network routines complete. ', 3, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'Checking system flags. ', 3, pilib.loglevels.system)
        processsystemflags()
        utility.log(pilib.dirs.logs.system, 'System flags complete. ', 3, pilib.loglevels.system)

        # Get system status again
        systemstatus = pilib.dbs.system.read_table('systemstatus')[0]

        elapsedtime = int(time.time() - starttime)

        utility.log(pilib.dirs.logs.system, 'Status routines complete. Elapsed time: ' + str(elapsedtime), 3,
                      pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system,
                               'System status is sleeping for ' + str(systemstatus['systemstatusfreq']) + '. ', 3,
                      pilib.loglevels.system)

        # print('enabled: ' , systemstatus['systemstatusenabled'])
        if 'runonce' in kwargs and kwargs['runonce']:
            break

        time.sleep(systemstatus['systemstatusfreq'])

    else:
        utility.log(pilib.dirs.logs.system, 'System status is disabled. Exiting. ', 0, pilib.loglevels.system)


if __name__ == '__main__':
    runonce = False
    debug = False
    if 'runonce' in sys.argv:
        print('run once selected')
        runonce = True
    if 'debug' in sys.argv:
        print('debug selected')
        debug = True
    run_system_status(runonce=runonce, debug=debug)
    # runsystemstatus()
