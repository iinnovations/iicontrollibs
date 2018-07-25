#!/usr/bin/python3

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


def get_hostapd_status():
    import subprocess
    try:
        result = subprocess.check_output(['/usr/sbin/service', 'hostapd', 'status'], stderr=subprocess.PIPE)
    except:
        return {'status':1, 'status_message':'Error retrieving status.'}
    else:
        return {'status':0}


def get_dhcp_status(type='dnsmasq'):
    import subprocess
    try:
        result = subprocess.check_output(['/usr/sbin/service', 'dnsmasq', 'status'], stderr=subprocess.PIPE)
    except:
        return {'status':1, 'status_message':'Error retrieving status.'}
    else:
        return {'status':0}


def updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface='wlan0', gateway='192.168.8.1', dhcpstart='192.168.8.70', dhcpend='192.168.8.99'):
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
        subnet = '192.168.8.0'

    filestring = 'ddns-update-style none;\noption domain-name "example.org";\n'
    filestring += 'option domain-name-servers ns1.example.org, ns2.example.org;\n'
    filestring += 'default-lease-time 600;\nmax-lease-time 7200;\nauthoritative;\nlog-facility local7;\n'
    filestring += 'subnet ' + subnet + ' netmask 255.255.255.0 {\n'
    filestring += 'range ' + dhcpstart + ' ' + dhcpend + ';\n'
    filestring += '  option domain-name-servers 8.8.8.8, 8.8.4.4;\n  option routers ' + gateway + ';\n'
    filestring += ' interface ' + interface + ';\n}'

    myfile.write(filestring)


def update_dnsmasq_conf(**kwargs):
    settings = {
        'path':'/etc/dnsmasq.conf',
        'interface':'wlan0',
        'gateway':'192.168.8.1',
        'dhcpstart':'192.168.8.70',
        'dhcpend':'192.168.8.100',
        'leaseperiod':'24h',
        'netmask':'255.255.255.0'
    }
    settings.update(kwargs)

    myfile = open(settings['path'], 'w')

    filestring = 'interface={}\n'.format(settings['interface'])
    filestring += 'dhcp-range={},{},{},{}\n'.format(settings['dhcpstart'], settings['dhcpend'], settings['netmask'], settings['leaseperiod'])
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
        networkname = 'cupid_' + hostname
        networkpassword = hostname + '_pwd'

    rebuild_ap_data(SSID=networkname, password=networkpassword)


def updatewirelessnetworks(interface='wlan0'):
    from iiutilities.netfun import getwirelessnetworks
    from iiutilities.datalib import dicttojson
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
            reset_net_iface(interface=interface)
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
    from iiutilities import utility

    netconfig = []
    try:
        netconfig = pilib.dbs.system.read_table_row('netconfig')[0]
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading netconfig data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read netconfig data. ', 4, pilib.loglevels.network)

    wirelessauths = []
    try:
        wirelessauths = pilib.dirs.dbs.safe.read_table('wireless')
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading wireless data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read wireless data. ', 4, pilib.loglevels.network)

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

def updatewpasupplicant(**kwargs):
    from cupid import pilib
    from iiutilities import dblib
    from iiutilities import utility

    settings = {
        'station_interface': 'wlan0',
        # 'network_select':['name','strongest'],
        'network_select':['strongest'],
        'network_ssid':'leHouse',
        'path' : '/etc/wpa_supplicant/wpa_supplicant.conf',
        'debug': False
    }
    settings.update(kwargs)

    # Update networks to see what is available to attach to
    # try:
    networks = updatewirelessnetworks(settings['station_interface'])

    if settings['debug']:
        network_dict = {}
        for network in networks:
            network_dict[network['ssid']] = network

        print('all networks by strength: ')
        networks_with_strength = [
            {'ssid': network['ssid'], 'signallevel': int(network['signallevel'].split('dB')[0].strip())} for
            network_name, network in network_dict.items()]

        from operator import itemgetter
        networks_by_strength = sorted(networks_with_strength, key=itemgetter('signallevel'), reverse=True)
        print(networks_by_strength)

    # except:
    # utility.log(pilib.dirs.logs.network, 'Error finding network interface. Is interface down?', 0, pilib.loglevels.network)

    # availablessids = []
    # for network in networks:
    #     availablessids.append(network['ssid'])

    # At first pass, this could be as simple as checking the last SSID and trying the other one

    try:
        wirelessauth_list = pilib.dbs.safe.read_table('wireless')
    except:
         utility.log(pilib.dirs.logs.network, 'Error reading wireless data. ', 0, pilib.loglevels.network)
    else:
         utility.log(pilib.dirs.logs.network, 'Read wireless data. ', 4, pilib.loglevels.network)

    auths = {}
    for auth_element in wirelessauth_list:
        auths[auth_element['SSID']] = auth_element

    # Get paired lists of networks and auths that match
    matchnetworks = {}
    for network in networks:
        this_ssid = network['ssid']
        if this_ssid in auths:
            matchnetworks[this_ssid] = network
            matchnetworks[this_ssid]['auths'] = auths[this_ssid]

    # So now the matchnetworks are available and we have credentials for them
    print('*** AVAILABLE NETWORKS ***')
    print(matchnetworks)

    newnetwork = {}
    if len(matchnetworks.items()) > 0:
        # matchnetwork_names = [matchnetwork['name'] for matchnetwork in matchnetworks]

        utility.log(pilib.dirs.logs.network, str(len(matchnetworks)) + ' matching networks found. ', 1, pilib.loglevels.network)

        """
        Choose network
        
        This is written such that if you have 'name' selected and not 'by strength' as secondary choice, no network
        will be selected. This is potentially a valid option.
        
        """
        #        TODO: Add in possibility of sorting by priority as stored in credentials.

        for network_method in settings['network_select']:
            if network_method == 'name':
                utility.log(pilib.dirs.logs.network, 'Using method name with name {}. ', 2, pilib.loglevels.network)

                if settings['network_ssid'] in matchnetworks:
                    utility.log(pilib.dirs.logs.network, 'Selected network {} found. ', 2, pilib.loglevels.network)
                    newnetwork = matchnetworks[settings['network_ssid']]
                    break
                else:
                    utility.log(pilib.dirs.logs.network, 'Selected network {} NOT found. ', 2, pilib.loglevels.network)
            elif network_method == 'strongest':
                utility.log(pilib.dirs.logs.network, 'Using method strongest. ', 2, pilib.loglevels.network)

                networks_with_strength = [{'ssid':network['ssid'],'signallevel':int(network['signallevel'].split('dB')[0].strip()), 'network':network} for network_name, network in matchnetworks.items()]
                print(networks_with_strength)

                from operator import itemgetter
                networks_by_strength = sorted(networks_with_strength, key=itemgetter('signallevel'), reverse=True)
                newnetwork = networks_by_strength[0]['network']
                print(networks_by_strength)
                break

        if newnetwork:
            print('NEW NETWORK')
            print(newnetwork)
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'SSID', newnetwork['ssid'])

            utility.log(pilib.dirs.logs.network, 'Network "' + newnetwork['ssid'] + '" selected', 1,
                        pilib.loglevels.network)

            myfile = open(settings['path'], 'w')

            filestring = 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\n\n'
            filestring += 'network={\n'
            filestring += 'psk="' + newnetwork['auths']['password'] + '"\n'
            filestring += 'ssid="' + newnetwork['ssid'] + '"\n'
            filestring += 'proto=RSN\nauth_alg=OPEN\npairwise=CCMP\nkey_mgmt=WPA-PSK\n}'

            myfile.write(filestring)
            myfile.close()

        else:
            dblib.setsinglevalue(pilib.dirs.dbs.system, 'netconfig', 'SSID', '')
            utility.log(pilib.dirs.logs.network, 'No network found with method selected and auths/ssids available. ', 1, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'No available ssids found with saved auths.', 1, pilib.loglevels.network)


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
    if netconfigdata['mode'] == 'staticeth0_stationdhcp':
        utility.log(pilib.dirs.logs.network, 'Configuring static eth0 and dhcp wlan0. ', 3, pilib.loglevels.network)

        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.eth0staticwlan0dhcp', '/etc/network/interfaces'])
        reset_net_iface(interface='eth0')


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
    reset_net_iface()
    sleep(1)
    reset_net_iface()


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


def killdhcpserver(type='dnsmasq'):
    from subprocess import call
    if type == 'isc':
        call(['/usr/sbin/service', 'isc-dhcp-server', 'stop'])
        call(['pkill','isc-dhcp-server'])
    else:
        call(['/usr/sbin/service', 'dnsmasq', 'stop'])
        call(['pkill', 'dnsmasq'])
    return


def startapservices(interface='wlan0', type='dnsmasq'):
    from time import sleep
    import subprocess
    from cupid import pilib
    from iiutilities import utility

    try:
        # We name the file by the interfae. This way when we pgrep, we know we're running AP on the right interface
        hostapdfilename = '/etc/hostapd/hostapd{}.conf'.format(interface)
        updatehostapd(path=hostapdfilename, interface=interface)
        subprocess.call(['/usr/sbin/hostapd', '-B', hostapdfilename])
    except:
        utility.log(pilib.dirs.logs.network, 'Error starting hostapd. ', 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Started hostapd without error. ', 3, pilib.loglevels.network)

    sleep(1)

    try:
        if type == 'isc':
            updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface=interface)
            subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'start'])
        elif type == 'dnsmasq':
            update_dnsmasq_conf()
            subprocess.call(['/usr/sbin/service', 'dnsmasq', 'start'])
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
    reset_net_iface()
    startapservices(interface)


def reset_net_iface(interface='wlan0'):
    from iiutilities import utility
    import subprocess
    from cupid import pilib

    utility.log(pilib.dirs.logs.network, 'Resetting ' + interface + ' . ', 3, pilib.loglevels.network)
    try:
        subprocess.call(['/sbin/ifdown', interface], stderr=subprocess.PIPE)
        subprocess.call(['/sbin/ifup', interface], stderr=subprocess.PIPE)
    except:
        import traceback
        utility.log(pilib.dirs.logs.network, 'Error resetting ' + interface + ' : ' +  traceback.format_exc(), 0, pilib.loglevels.network)
    else:
        utility.log(pilib.dirs.logs.network, 'Completed resetting ' + interface + '. ', 3, pilib.loglevels.network)


def make_ifconfig_file(**kwargs):
    settings = {
        'path':'/etc/network/interfaces',
        'write':True,
        'debug':False,
        'config': {
            'eth0':
               {
                   'mode':'dhcp'
               },
            'wlan0':
                {
                    'mode':'station',
                    'network-select':'name',
                    'network':'leHouse'
                }
        },
        'default_static_address':'192.168.8.25'
    }
    settings.update(kwargs)

    filestring = ''
    return_dict = {'status': 0, 'status_message': '', 'filestring': filestring, 'config': settings['config']}

    if settings['write']:
        if settings['debug']:
            print('Preparing file {} for write. '.format(settings['path']))
        myfile = open(settings['path'], 'w')


    filestring += 'auto lo\n'
    filestring += 'iface lo inet loopback\n'

    for interface_name, interface_config in settings['config'].items():
        this_config = settings['config'][interface_name]

        filestring += '\nauto {}\n'.format(interface_name)

        if this_config['mode'] in ['station', 'ap']:
            filestring += 'allow-hotplug {}\n'.format(interface_name)

        # eth0 modes. should do some error-checking in here.
        if this_config['mode'] == 'dhcp':
            filestring += 'iface {} inet dhcp\n'.format(interface_name)

        elif this_config['mode'] in ['static', 'ap']:
            filestring += 'iface {} inet static\n'.format(interface_name)
            if 'address' not in this_config['config']:
                if settings['debug']:
                    print('Address not provided for {}. Defaulting to {}'.format(interface_name, settings['default_static_address']))
                this_config['address'] = settings['default_static_address']

            filestring += '    address {}\n'.format(this_config['config']['address'])
            filestring += '    netmask 255.255.255.0\n\n'

        # wlan station mode. should do error-checking here.
        elif this_config['mode'] == 'station':
            filestring += 'iface {} inet dhcp\n'.format(interface_name)
            filestring += 'wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf\n'

        else:
            if not 'mode' in this_config:
                this_config['mode'] = None
            message = 'error: valid mode not found for interface {}. Mode: {}. '.format(interface_name,
                                                                                        this_config['mode'])
            if settings['debug']:
                print(message)
            return {'status':1, 'status_message':message}

    return_dict['filestring'] = filestring

    if settings['write']:
        if settings['debug']:
            print('Complete filestring : \n {}\n'.format(filestring))
        try:
            myfile.write(filestring)
        except:
            return_dict['status_message'] = 'Error writing file. '
            return_dict['status'] = 1
            return return_dict
        else:
            return_dict['status_message'] += 'File written successfully. '
            return return_dict

    else:
        message = 'Not writing \n. '
        if settings['debug']:
            print(message)
        return_dict['status_message'] += message
        return return_dict


def runconfig(**kwargs):
    from iiutilities import utility
    from cupid import pilib
    from iiutilities.datalib import gettimestring
    from iiutilities import dblib

    """
    Interfaces and modes

    Interfaces:         eth0 | wlan0 | wlan1
    Modes:        dhcp|  ok  |  --   |  --
                static|  ok  |  --   |  --

               station|  --  |  ok   |  ok
                    ap|  --  |  ok   |  ok 
    """

    settings = {
        'debug':False,
        'onboot':False,
        'config_all':False,
        'ifaces_to_configure':['wlan0'],
        'config': {
            'eth0':
               {
                   'enabled':True,
                   'mode':'dhcp'
               },
            'wlan0':
                {
                    'enabled':True,
                    'mode':'station',
                    'config':
                        {
                            'network_select':['name','strongest'],
                            'network':'leHouse'
                        }
                }
        },
        'use_default':False
    }
    settings.update(kwargs)
    if settings['debug']:
        pilib.set_debug()


    # Get from database
    # TODO : Used passed configuration data.

    if not settings['use_default']:
        import json
        netiface_config = pilib.dbs.system.read_table('netifaceconfig')

        if not netiface_config:
            message = 'netifaceconfig table empty or not found ! '
            utility.log(pilib.dirs.logs.network, message, 0, pilib.loglevels.network)
            return {'status':1, 'status_message': message}

        settings['config'] = {}
        for iface_config in netiface_config:
            settings['config'][iface_config['name']] = iface_config

            # unpack json dump of config details
            try:
                settings['config'][iface_config['name']]['config'] = json.loads(iface_config['config'])
            except:
                message = 'Config entry for interface {} is empty or cannot be unpacked as json: {}. '.format(iface_config['name'], iface_config['config'])
                # print(settings['config'][iface_config['name']])
                utility.log(pilib.dirs.logs.network, message, 3, pilib.loglevels.network)

    utility.log(pilib.dirs.logs.network, 'Updating ifconfig file. ', 0, pilib.loglevels.network)

    print('MAKING CONFIG FILE WITH CONFIG')
    print(settings['config'])
    make_ifconfig_file(config=settings['config'])

    # For now, we are going to assume that we are only using one wireless interface at most as a network station
    station_interface = None
    for interface_name, interface in settings['config'].items():
        if interface['mode'] == 'station':
            station_interface = interface['name']

    utility.log(pilib.dirs.logs.network, 'Running network reconfig (setting lastnetreconfig). ', 0, pilib.loglevels.network)
    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'lastnetreconfig', gettimestring())

    try:
        netconfigdata = dblib.readonedbrow(pilib.dirs.dbs.system, 'netconfig')[0]
        if settings['debug']:
            print("NETCONFIG:\n{}".format(netconfigdata))
    except:
        utility.log(pilib.dirs.logs.network, 'Error reading netconfig data. ', 0, pilib.loglevels.network)
        return {'status':1, 'status_message':'Error reading netconfig data. '}
    else:
        utility.log(pilib.dirs.logs.network, 'Successfully read netconfig data', 3, pilib.loglevels.network)

    dblib.setsinglevalue(pilib.dirs.dbs.system, 'netstatus', 'mode', netconfigdata['mode'])

    utility.log(pilib.dirs.logs.network, 'Netconfig is enabled', 3, pilib.loglevels.network)

    # This will grab the specified SSID and the credentials and update
    # the wpa_supplicant file. At the moment, it also looks to see if the network is available.

    if station_interface:
        utility.log(pilib.dirs.logs.network, 'Updating wpa_supplicant', 3, pilib.loglevels.network)
        updatewpasupplicant(station_interface=station_interface)

    if settings['config_all']:
        utility.log(pilib.dirs.logs.network, 'Configuring all interfaces. ', 3, pilib.loglevels.network)
        settings['ifaces_to_configure'] = [interface_name for interface_name in settings['config']]

    for interface_name in settings['ifaces_to_configure']:
        utility.log(pilib.dirs.logs.network, 'Configuring interface: {}'.format(interface_name), 3, pilib.loglevels.network)

        if interface_name not in settings['config']:
            message = 'Configuration not present for interface {}. '.format(interface_name)
            utility.log(pilib.dirs.logs.network, message, 1, pilib.loglevels.network)
            continue

        this_config = settings['config'][interface_name]
        if settings['debug']:
            print('CONFIG: \n{}'.format(this_config))

        if this_config['mode'] == 'ap':
            killapservices()
            reset_net_iface(interface=interface_name)
            startapservices(interface_name)
        else:
            reset_net_iface(interface=interface_name)

    # Bridges require ipv4 being enabled in /etc/sysctl.conf
    # Here we are going to auto-bridge, but I think we should probably manually specify that the bridge should exist

    mode = None
    if all(interface in settings['config'] for interface in ['eth0', 'wlan0']):
        if settings['config']['wlan0']['mode'] == 'ap':
            mode = 'eth0wlan0bridge'
    if all(interface in settings['config'] for interface in ['wlan0', 'wlan1']):
        if settings['config']['wlan0']['mode'] == 'dhcp' and settings['config']['wlan1']['mode'] == 'ap':
            mode = 'wlan0wlan1bridge'
    if all(interface in settings['config'] for interface in ['wlan0', 'wlan1']):
        if settings['config']['wlan1']['mode'] == 'dhcp' and settings['config']['wlan0']['mode'] == 'ap':
            mode = 'wlan1wlan0bridge'

    if mode:
        utility.log(pilib.dirs.logs.network, 'Setting bridge for mode {}'.format(mode), 1, pilib.loglevels.network)
        runIPTables(mode)


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