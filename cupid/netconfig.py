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


def updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface='wlan0', gateway='192.168.0.1', dhcpstart='192.168.0.70', dhcpend='192.168.0.99'):
    from iiutilities import dblib
    from cupid import pilib
    try:
        netconfigdata = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]
        dhcpstart = netconfigdata['dhcpstart']
        dhcpend = netconfigdata['dhcpend']
        gateway = netconfigdata['gateway']
    except:
        # print('we had an error')
        pass


    myfile = open(path, 'w')

    try:
        subnet = '.'.join(gateway.split['.'][:-1]) + '.0'
    except:
        subnet = '192.168.0.0'

    filestring = 'ddns-update-style none;\noption domain-name "example.org";\n'
    filestring += 'option domain-name-servers ns1.example.org, ns2.example.org;\n'
    filestring += 'default-lease-time 600;\nmax-lease-time 7200;\nauthoritative;\nlog-facility local7;\n'
    filestring += 'subnet ' + subnet + ' netmask 255.255.255.0 {\n'
    filestring += 'range ' + dhcpstart + ' ' + dhcpend + ';\n'
    filestring += '  option domain-name-servers 8.8.8.8, 8.8.4.4;\n  option routers ' + gateway + ';\n'
    filestring += ' interface ' + interface + ';\n}'

    myfile.write(filestring)


def updatehostapd(path='/etc/hostapd/hostapd.conf', interface='wlan0'):

    from iiutilities import dblib
    from cupid import pilib

    piversion = dblib.getsinglevalue(pilib.dirs.dbs.system, 'versions', 'versionname')
    try:
        apsettings = dblib.readonedbrow(pilib.dirs.dbs.safe, 'apsettings')[0]
        print(apsettings)
        SSID = apsettings['SSID']
        password = apsettings['password']
    except:
        SSID = 'cupidwifi'
        password = 'cupidpassword'

    # print(SSID)
    myfile = open(path, 'w')
    filestring = 'interface=' + interface + '\n'

    # In these versions, we had to use an alternate driver. No more!! Built-in RPi 3 fixes this garbage.
    # Hostapd works out of the box. About time.

    if piversion in ['Pi 2 Model B', 'Model B Revision 2.0', 'Model B+']:
        filestring += 'driver=rtl871xdrv\nssid='
    else:
        filestring += 'driver=nl80211\nssid='

    filestring += SSID
    filestring += '\nchannel=6\nwmm_enabled=1\nwpa=1\nwpa_passphrase=' + password + '\nwpa_key_mgmt=WPA-PSK\n'
    filestring += 'wpa_pairwise=TKIP\nrsn_pairwise=CCMP\nauth_algs=1\nmacaddr_acl=0'

    myfile.write(filestring)


def setdefaultapsettings():
    import socket
    from rebuilddatabases import rebuild_ap_data
    hostname = socket.gethostname()
    if hostname == 'raspberrypi':
        networkname = 'cupidwifi'
        networkpassword = 'cupidpassword'
    else:
        networkname = 'cupid' + hostname
        networkpassword = hostname + '_pwd'

    rebuild_ap_data(SSID=networkname, password=networkpassword)


def updatewirelessnetworks(interface='wlan0'):
    from iiutilities.netfun import getwirelessnetworks
    from iiutilities.utility import dicttojson
    from iiutilities.utility import log
    from iiutilities.dblib import dropcreatetexttablefromdict, sqliteemptytable
    from pilib import dirs

    networks = []
    for i in range(2):
        try:
            networks = getwirelessnetworks(interface)
        except:
            log('Error getting wireless interface networks. Setting empty networks for restart on catch', dirs.logs.network)

        if not networks:
            log('No networks returned or error in retrieving, restarting interface ' + interface, dirs.logs.network)
            resetwlan(interface=interface)
        else:
            break

    if networks:
        netinsert = []
        for network in networks:
            # print(network)
            netinsert.append({'ssid':network['ssid'],'strength':network['signallevel'], 'data':dicttojson(network)})

        dropcreatetexttablefromdict(dirs.dbs.system, 'wirelessnetworks', netinsert)
    else:
        sqliteemptytable(dirs.dbs.system, 'wirelessnetworks')
    return networks


# This have no use anymore
def getwpasupplicantconfig(conffile='/etc/wpa_supplicant/wpa_supplicant.conf'):
    from iiutilities import utility
    from cupid import pilib
    class data():
        pass

    file = open(conffile)
    lines = file.readlines()
    header = ''
    tail = ''
    datalines = []
    readheader = True
    readbody = False
    readtail = False
    for line in lines:
        if readheader:
            header = header + line
        if '}' in line:
            utility.log(pilib.dirs.logs.network, 'Ending supplicant parse. ', 5, pilib.loglevels.network)
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            utility.log(pilib.dirs.logs.network, 'Beginning supplicant parse. ', 5, pilib.loglevels.network)
            readheader = False
            readbody = True

    datadict = {}
    for line in datalines:
        split = line.split('=')
        datadict[split[0].strip()] = split[1].strip()

    returndict = data()
    returndict.header = header
    returndict.tail = tail
    returndict.data = datadict
    return returndict


def updatesupplicantdata(configdata):
    from cupid import pilib
    from iiutilities.dblib import readalldbrows
    from iiutilities import utility

    netconfig = []
    try:
        netconfig = readalldbrows(pilib.dirs.dbs.system, 'netconfig')[0]
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading netconfig data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read netconfig data. ', 4, pilib.loglevels.network)

    wirelessauths = []
    try:
        wirelessauths = readalldbrows(pilib.dirs.dbs.safe, 'wireless')
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading wireless data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read wireless data. ', 4, pilib.loglevels.network)

    password = ''

    utility.log(pilib.dirs.logs.network, 'Netconfig data: ' + str(netconfig), 2, pilib.loglevels.network)

    # we only update if we find the credentials
    for auth in wirelessauths:
        if auth['SSID'] == netconfig['SSID']:
            password = '"' + auth['password'] + '"'
            ssid = '"' + auth['SSID'] + '"'
            utility.log(pilib.dirs.logs.network, 'SSID ' + auth['SSID'] + 'found. ', 1, pilib.loglevels.network)
            configdata.data['psk'] = password
            configdata.data['ssid'] = ssid
    return configdata


def writesupplicantfile(filedata, filepath='/etc/wpa_supplicant/wpa_supplicant.conf'):
    import subprocess
    from iiutilities import utility
    from cupid import pilib
    writestring = ''

    supplicantfilepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
    # We are hard-coding this, as this will unfortunately propagate a mangled file
    subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/wpa_supplicant.conf', supplicantfilepath])

    # iterate over fed data
    ssid = 'not found'
    psk = 'not found'
    for key, value in filedata.data.items():
        if key == 'ssid':
            ssid=value
        elif key == 'psk':
            psk = value

    file = open(supplicantfilepath)
    lines = file.readlines()
    writestring = ''
    ifacename = None
    for line in lines:
        if line.find('psk=') >= 0:
            # insert our iface parameters
            try:
                writestring +='psk=' + psk + '\n'
            except:
                writestring +='psk=error'
        elif line.find('ssid=') >= 0:
            # insert our iface parameters
            try:
                writestring +='ssid=' + ssid + '\n'
            except:
                writestring +='psk=error'
        else:
            writestring += line

    utility.log(pilib.dirs.logs.network, 'Writing supplicant file. ', 1, pilib.loglevels.network)
    try:
        myfile = open(filepath, 'w')
        myfile.write(writestring)
    except:
        utility.log(pilib.dirs.logs.network, 'Error writing supplicant file. ', 1, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Supplicant file written. ', 3, pilib.loglevels.network)


def updatewpasupplicantOLD(interface='wlan0'):
    from iiutilities import utility
    from cupid import pilib
    # print('I AM UPDATING SUPPLICANT DATA')
    suppdata = None
    try:
        suppdata = getwpasupplicantconfig()
    except:
        utility.log(pilib.dirs.logs.network, 'Error getting supplicant data. ', 0, pilib.loglevels.network)
        return
    else:
        utility.log(pilib.dirs.logs.network, 'Supplicant data retrieved successfully. ', 3, pilib.loglevels.network)

    try:
        updateddata = updatesupplicantdata(suppdata)
    except:
        utility.log(pilib.dirs.logs.network, 'Error updating supplicant data. ', 0, pilib.loglevels.network)
        return
    else:
        utility.log(pilib.dirs.logs.network, 'Supplicant data retrieved successfully. ', 3, pilib.loglevels.network)

    try:
        writesupplicantfile(updateddata)
    except:
        utility.log(pilib.dirs.logs.network, 'Error writing supplicant data. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Supplicant data written successfully. ', 3, pilib.loglevels.network)

    return


# This function should be renamed or refactored. Update wpasupplicant should just write the file.
# This function does so much more.

def updatewpasupplicant(path='/etc/wpa_supplicant/wpa_supplicant.conf', netconfig=None):
    from cupid import pilib
    from iiutilities import dblib
    from iiutilities import utility

    if not netconfig:
        netconfig = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]

    if netconfig['mode'] in ['wlan1wlan0bridge']:
        stationinterface = 'wlan1'
    else:
        stationinterface = 'wlan0'


    # Update networks to see what is available to attach to
    # try:
    networks = updatewirelessnetworks(stationinterface)
    # except:
    # utility.log(pilib.dirs.logs.network, 'Error finding network interface. Is interface down?', 0, pilib.loglevels.network)

    availablessids = []
    for network in networks:
        availablessids.append(network['ssid'])


    # Check to see if netconfig wireless network is in existing networks. If not, switch to one with either highest
    # priority (with minimum signal strength, or to the one with the best signal.

    # TODO : make provision for moving on to the next network if we have multiple options and one isn't working out
    # At first pass, this could be as simple as checking the last SSID and trying the other one


    try:
        wirelessauths = dblib.readalldbrows(pilib.dirs.dbs.safe, 'wireless')
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading wireless data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read wireless data. ', 4, pilib.loglevels.network)

    authssids = []
    for auth in wirelessauths:
        authssids.append(auth['SSID'])

    # Get paired lists of networks and auths that match
    matchnetworks = []
    matchauths = []
    for ssid in availablessids:
        if ssid in authssids:
            availablessidsindex = availablessids.index(ssid)
            matchnetworks.append(networks[availablessidsindex])

            authindex = authssids.index(ssid)
            matchauths.append(wirelessauths[authindex])

    # So now the matchnetworks are available and we have credentials for them
    print('*** AVAILABLE NETWORKS ***')
    print(matchnetworks)

    psk = ''
    ssid = ''
    if len(matchnetworks) > 0:
        utility.log(pilib.dirs.logs.network, str(len(matchnetworks)) + ' matching networks found. ', 1, pilib.loglevels.network)

        if len(matchnetworks) > 1:
            # TODO: Choosing network algorithm
            newnetwork = matchnetworks[0]
            newauth = matchauths[0]
        else:
            newnetwork = matchnetworks[0]
            newauth = matchauths[0]

        utility.log(pilib.dirs.logs.network, 'Network "' + newnetwork['ssid'] + '" selected', 1, pilib.loglevels.network)

        netconfig['SSID'] = newnetwork['ssid']
        ssid = newnetwork['ssid']
        psk = newauth['password']

        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'SSID', newnetwork['ssid'])

        # print(' Chosen SSID: ' + ssid)
        # print(' Chosen PSK: ' + psk)

    # # we only update if we find the credentials
    # try:
    #     ssid = netconfig['SSID']
    # except KeyError:
    #     utility.log(pilib.dirs.logs.network, 'No SSID found in netconfig', 1, pilib.loglevels.system)
    #     # try to attach to first network by setting SSID to first network in wireless auths
    #     # this can help alleviate some headaches down the line, hopefully. What should really be done is a
    #     # network scan to see which are available
    #
    #     wirelessauths = dblib.readalldbrows(pilib.dirs.dbs.safe, 'wireless')
    #
    #     try:
    #         defaultauths = wirelessauths[0]
    #         currssid = defaultauths['SSID']
    #     except:
    #         utility.log(pilib.dirs.logs.system, 'No SSID in wireless table to default to. ', 1, pilib.loglevels.system)

    if ssid:
        if psk:

            myfile = open(path, 'w')

            filestring = 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\n\n'
            filestring += 'network={\n'
            filestring += 'psk="' + psk + '"\n'
            filestring += 'ssid="' + ssid + '"\n'
            filestring += 'proto=RSN\nauth_alg=OPEN\npairwise=CCMP\nkey_mgmt=WPA-PSK\n}'

            myfile.write(filestring)

        else:
            utility.log(pilib.dirs.logs.network, 'No auths recovered for SSID, so not writing wpa_supplicant', 1, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'No SSID found to write, so not writing wpa_supplicant', 1, pilib.loglevels.network)


def replaceifaceparameters(iffilein, iffileout, iface, parameternames, parametervalues):
    from iiutilities import utility
    from cupid import pilib

    file = open(iffilein)
    lines = file.readlines()
    writestring = ''
    ifacename = None
    for line in lines:
        if line.find('iface') >= 0 > line.find('default'):
            # we are at an iface stanza beginning
            foundname = line[6:11].strip()
            ifacename = foundname

        if ifacename == iface:
            # do our replace
            for parametername, parametervalue in zip(parameternames, parametervalues):
                if line.find(parametername) > 0:
                    split = line.split(' ')
                    # We find where the parameter is, then assume the value is the
                    # next position. We then trim everything past the parameter
                    # This safeguards against whitespace at the end of lines creating problems.
                    index = split.index(parametername)
                    split[index + 1] = str(parametervalue) + '\n'
                    line = ' '.join(split[0:index + 2])

        writestring += line
    try:
        myfile = open(iffileout, 'w')
    except:
        utility.log(pilib.dirs.logs.network, 'Error opening interface file. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Interface file read successfully. ', 3, pilib.loglevels.network)

    try:
        myfile.write(writestring)
    except:
        utility.log(pilib.dirs.logs.network, 'Error writing interface file. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Interface file written successfully. ', 3, pilib.loglevels.network)
        utility.log(pilib.dirs.logs.network, 'Write string: ' + writestring, 3, pilib.loglevels.network)


def setstationmode(netconfigdata=None):
    import subprocess
    from iiutilities import utility
    from cupid import pilib
    from iiutilities import dblib

    utility.log(pilib.dirs.logs.network, 'Setting station mode. ', 3, pilib.loglevels.network)

    from time import sleep
    if not netconfigdata:
        utility.log(pilib.dirs.logs.network, 'Retrieving unfound netconfig data. ', 3, pilib.loglevels.network)
        try:
            netconfigdata = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]
        except:
            utility.log(pilib.dirs.logs.network, 'Error reading netconfig data. ', 0, pilib.loglevels.network)
        else:
            utility.log(pilib.dirs.logs.network, 'Read netconfig data. ', 4, pilib.loglevels.network)

    killapservices()
    if netconfigdata['mode'] == 'staticeth0stationdhcp':
        utility.log(pilib.dirs.logs.network, 'Configuring static eth0 and dhcp wlan0. ', 3, pilib.loglevels.network)

        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.eth0staticwlan0dhcp', '/etc/network/interfaces'])
        resetwlan(interface='eth0')


        # update IP from netconfig
        utility.log(pilib.dirs.logs.network, 'Updating netconfig with ip ' + netconfigdata['address'], 3, pilib.loglevels.network)
        replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                               [netconfigdata['address'], netconfigdata['gateway']])

    # This is the old mode for legacy purposes and backward compatibility
    elif netconfigdata['mode'] == 'station':

        if netconfigdata['addtype'] == 'static':
            utility.log(pilib.dirs.logs.network, 'Configuring static address. ', 3, pilib.loglevels.network)

            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.static', '/etc/network/interfaces'])

            # update IP from netconfig
            utility.log(pilib.dirs.logs.network, 'Updating netconfig with ip ' + netconfigdata['address'], 3, pilib.loglevels.network)
            replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                                   [netconfigdata['address'], netconfigdata['gateway']])
        elif netconfigdata['addtype'] == 'dhcp':
            utility.log(pilib.dirs.logs.network, 'Configuring dhcp. ', 3, pilib.loglevels.network)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.dhcp', '/etc/network/interfaces'])

    utility.log(pilib.dirs.logs.network, 'Resetting wlan. ', 3, pilib.loglevels.network)
    resetwlan()
    sleep(1)
    resetwlan()


def killapservices():
    from iiutilities import utility
    from cupid import pilib
    utility.log(pilib.dirs.logs.network, 'Killing AP Services. ', 1, pilib.loglevels.network)
    try:
        killhostapd()
    except:
        utility.log(pilib.dirs.logs.network, 'Error killing hostapd. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Killed hostapd. ', 3, pilib.loglevels.network)

    try:
        killdhcpserver()
    except:
        utility.log(pilib.dirs.logs.network, 'Error killing dhcp server. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Successfully killed dhcp server. ', 3, pilib.loglevels.network)


def killhostapd():
    from subprocess import call
    call(['/usr/sbin/service', 'hostapd', 'stop'])
    call(['pkill','hostapd'])
    return


def killdhcpserver():
    from subprocess import call
    call(['/usr/sbin/service', 'isc-dhcp-server', 'stop'])
    call(['pkill','isc-dhcp-server'])
    return


def startapservices(interface='wlan0'):
    from time import sleep
    import subprocess
    from cupid import pilib
    from iiutilities import utility

    try:
        # We name the file by the interfae. This way when we pgrep, we know we're running AP on the right interface
        hostapdfilename = '/etc/hostapd/hostapd' + interface + '.conf'
        updatehostapd(path=hostapdfilename, interface=interface)
        subprocess.call(['/usr/sbin/hostapd', '-B', hostapdfilename])
    except:
        utility.log(pilib.dirs.logs.network, 'Error starting hostapd. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Started hostapd without error. ', 3, pilib.loglevels.network)

    sleep(1)

    try:
        updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface=interface)
        subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'start'])
    except:
        utility.log(pilib.dirs.logs.network, 'Error starting dhcp server. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Started dhcp server without error. ', 3, pilib.loglevels.network)


def setapmode(interface='wlan0', netconfig=None):
    from iiutilities import utility
    import subprocess
    from cupid import pilib

    utility.log(pilib.dirs.logs.network, 'Setting ap mode for interface ' + interface, 1, pilib.loglevels.network)
    try:
        if interface == 'wlan0':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.ap', '/etc/network/interfaces'])
        elif interface == 'wlan0wlan1':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan0dhcp.wlan1cupidwifi', '/etc/network/interfaces'])
        elif interface == 'wlan1wlan0':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan1dhcp.wlan0cupidwifi', '/etc/network/interfaces'])
    except:
        utility.log(pilib.dirs.logs.network, 'Error copying network configuration file. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Copied network configuration file successfully. ', 3, pilib.loglevels.network)

    killapservices()
    resetwlan()
    startapservices(interface)


def resetwlan(interface='wlan0'):
    from iiutilities import utility
    import subprocess
    from cupid import pilib

    utility.log(pilib.dirs.logs.network, 'Resetting ' + interface + ' . ', 3, pilib.loglevels.network)
    try:
        subprocess.check_output(['/sbin/ifdown', '--force', interface], stderr=subprocess.PIPE)
        subprocess.call(['/sbin/ifup', interface], stderr=subprocess.PIPE)
    except Exception, e:
        utility.log(pilib.dirs.logs.network, 'Error resetting ' + interface + ' : ' + str(e), 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Completed resetting ' + interface + '. ', 3, pilib.loglevels.network)


def runconfig(**kwargs):
    import subprocess
    from iiutilities import utility
    from cupid import pilib
    from iiutilities.datalib import gettimestring
    from iiutilities import dblib

    settings = {
        'debug':False, 'onboot':False
    }
    settings.update(kwargs)

    utility.log(pilib.dirs.logs.network, 'Running network reconfig (setting lastnetreconfig). ', 0, pilib.loglevels.network)
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'lastnetreconfig', gettimestring())

    try:
        netconfigdata = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]
        # print(netconfigdata)
    except:
        utility.log(pilib.dirs.logs.network, 'Error reading netconfig data. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Successfully read netconfig data', 3, pilib.loglevels.network)

        dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'mode', netconfigdata['mode'])

        utility.log(pilib.dirs.logs.network, 'Netconfig is enabled', 3, pilib.loglevels.network)

        # This will grab the specified SSID and the credentials and update
        # the wpa_supplicant file. At the moment, it also looks to see if the network is available.
        # This functionality should be present elsewhere.

        updatewpasupplicant()

        # Copy the correct interfaces file
        if netconfigdata['mode'] == 'station':
            setstationmode(netconfigdata)
        elif netconfigdata['mode'] == 'staticeth0stationdhcp':
            setstationmode(netconfigdata)
        elif netconfigdata['mode'] in ['ap', 'tempap', 'eth0wlan0bridge']:
            utility.log(pilib.dirs.logs.network, 'Setting eth0wlan0 bridge (or bare ap mode). ', 0, pilib.loglevels.network)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.ap', '/etc/network/interfaces'])
            killapservices()
            resetwlan()
            startapservices('wlan0')

        # All of these require ipv4 being enabled in /etc/sysctl.conf
        # First interface is DHCP, second is CuPIDwifi
        elif netconfigdata['mode'] == 'wlan0wlan1bridge':
            utility.log(pilib.dirs.logs.network, 'Setting wlan0wlan1 bridge', 0, pilib.loglevels.network)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan0dhcp.wlan1cupidwifi', '/etc/network/interfaces'])
            killapservices()
            resetwlan('wlan0')
            resetwlan('wlan1')
            startapservices('wlan1')

        elif netconfigdata['mode'] == 'wlan1wlan0bridge':
            utility.log(pilib.dirs.logs.network, 'Setting wlan1wlan0 bridge', 0, pilib.loglevels.network)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan1dhcp.wlan0cupidwifi', '/etc/network/interfaces'])
            killapservices()
            resetwlan('wlan0')
            resetwlan('wlan1')
            startapservices('wlan0')

        runIPTables(netconfigdata['mode'])


def runIPTables(mode, flush=True):
    import pilib
    from iiutilities import utility
    if flush:
        utility.log(pilib.dirs.logs.network, 'Flushing IPTables', 2, pilib.loglevels.network)
        flushIPTables()
    if mode == 'eth0wlan0bridge':
        utility.log(pilib.dirs.logs.network, 'Running eth0wlan0 bridge IPTables', 2, pilib.loglevels.network)
        runeth0wlan0bridgeIPTables()
    elif mode == 'wlan0wlan1bridge':
        utility.log(pilib.dirs.logs.network, 'Running wlan0wlan1 bridge IPTables', 2, pilib.loglevels.network)
        runwlan0wlan1bridgeIPTables()
    elif mode == 'wlan1wlan0bridge':
        utility.log(pilib.dirs.logs.network, 'Running wlan1wlan0 bridge IPTables', 2, pilib.loglevels.network)
        runwlan1wlan0bridgeIPTables()


def runeth0wlan0bridgeIPTables():
    import subprocess
    # eth0 has ethernet connectivity. wlan0 is AP
    subprocess.call(['iptables','-t','nat','-A','POSTROUTING','-o','eth0','-j','MASQUERADE'])
    subprocess.call(['iptables','-A','FORWARD','-i','eth0','-o','wlan0','-m','state','--state','RELATED,ESTABLISHED','-j','ACCEPT'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan0','-o','eth0','-j','ACCEPT'])


def runwlan0wlan1bridgeIPTables():
    import subprocess
    # wlan0 has ethernet connectivity. wlan1 is AP
    subprocess.call(['iptables', '-t', 'nat', '-A', 'POSTROUTING','-o', 'wlan0', '-j', 'MASQUERADE'])
    subprocess.call(['iptables', '-A', 'FORWARD', '-i', 'wlan0', '-o', 'wlan1', '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'])
    subprocess.call(['iptables', '-A', 'FORWARD', '-i', 'wlan1', '-o', 'wlan0', '-j', 'ACCEPT'])


def runwlan1wlan0bridgeIPTables():
    import subprocess
    # wlan1 has ethernet connectivity. wlan0 is AP
    subprocess.call(['iptables','-t','nat','-A','POSTROUTING','-o','wlan1','-j','MASQUERADE'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan1','-o','wlan0','-m','state','--state','RELATED,ESTABLISHED','-j','ACCEPT'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan0','-o','wlan1','-j','ACCEPT'])


def flushIPTables():
    import subprocess
    subprocess.call(['iptables', '-F'])
    subprocess.call(['iptables', '-X'])
    subprocess.call(['iptables', '-t', 'nat', '-F'])
    subprocess.call(['iptables', '-t', 'nat', '-X'])
    subprocess.call(['iptables', '-t', 'mangle', '-F'])
    subprocess.call(['iptables', '-t', 'mangle', '-X'])
    subprocess.call(['iptables', '-P', 'INPUT', 'ACCEPT'])
    subprocess.call(['iptables', '-P', 'FORWARD', 'ACCEPT'])
    subprocess.call(['iptables', '-P', 'OUTPUT', 'ACCEPT'])

if __name__ == "__main__":
    # This will run the configuration script (if netconfig is enabled) and set
    # ap or station mode, and finally bring down and up wlan0
    runconfig(debug=True)
    # updatewpasupplicant()