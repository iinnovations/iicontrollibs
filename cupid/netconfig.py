#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


import subprocess
import pilib


def updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface='wlan0', gateway='192.168.0.1', dhcpstart='192.168.0.70', dhcpend='192.168.0.99'):
    try:
        netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
        dhcpstart = netconfigdata['dhcpstart']
        dhcpend = netconfigdata['dhcpend']
        gateway = netconfigdata['gateway']
    except:
        print('we had an error')
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
    # try:
    apsettings = pilib.readonedbrow(pilib.safedatabase, 'apsettings')[0]
    SSID = apsettings['SSID']
    password = apsettings['password']
    # except:
    #     SSID = 'cupidwifi'
    #     password = 'cupidpassword'

    print(SSID)
    myfile = open(path, 'w')
    filestring = 'interface=' + interface + '\n'
    filestring += 'driver=rtl871xdrv\nssid='
    filestring += SSID
    filestring += '\nchannel=6\nwmm_enabled=1\nwpa=1\nwpa_passphrase=cupidpassword\nwpa_key_mgmt=WPA-PSK\n'
    filestring += 'wpa_pairwise=TKIP\nrsn_pairwise=CCMP\nauth_algs=1\nmacaddr_acl=0'

    myfile.write(filestring)


def setdefaultapsettings():
    import socket
    from rebuilddatabases import rebuildapdata
    hostname = socket.gethostname()
    if hostname == 'raspberrypi':
        networkname = 'cupidwifi'
        networkpassword = 'cupidpassword'
    else:
        networkname = 'cupid' + hostname
        networkpassword = hostname + '_pwd'

    rebuildapdata(SSID=networkname, password=networkpassword)


def getwpasupplicantconfig(conffile='/etc/wpa_supplicant/wpa_supplicant.conf'):
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
            pilib.writedatedlogmsg(pilib.networklog, 'Ending supplicant parse. ', 5, pilib.networkloglevel)
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            pilib.writedatedlogmsg(pilib.networklog, 'Beginning supplicant parse. ', 5, pilib.networkloglevel)
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
    from pilib import readalldbrows, safedatabase, systemdatadatabase

    netconfig = []
    try:
        netconfig = readalldbrows(systemdatadatabase, 'netconfig')[0]
    except:
         pilib.writedatedlogmsg(pilib.networklog, 'Error reading netconfig data. ', 0, pilib.networkloglevel)
    else:
         pilib.writedatedlogmsg(pilib.networklog, 'Read netconfig data. ', 4, pilib.networkloglevel)

    try:
        wirelessauths = readalldbrows(safedatabase, 'wireless')
    except:
         pilib.writedatedlogmsg(pilib.networklog, 'Error reading wireless data. ', 0, pilib.networkloglevel)
    else:
         pilib.writedatedlogmsg(pilib.networklog, 'Read wireless data. ', 4, pilib.networkloglevel)

    password = ''

    pilib.writedatedlogmsg(pilib.networklog, 'Netconfig data: ' + str(netconfig), 2, pilib.networkloglevel)

    # we only update if we find the credentials
    for auth in wirelessauths:
        if auth['SSID'] == netconfig['SSID']:
            password = '"' + auth['password'] + '"'
            ssid = '"' + auth['SSID'] + '"'
            pilib.writedatedlogmsg(pilib.networklog, 'SSID ' + auth['SSID'] + 'found. ', 1, pilib.networkloglevel)
            configdata.data['psk'] = password
            configdata.data['ssid'] = ssid
    return configdata


def writesupplicantfile(filedata, filepath='/etc/wpa_supplicant/wpa_supplicant.conf'):
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

    pilib.writedatedlogmsg(pilib.networklog, 'Writing supplicant file. ', 1, pilib.networkloglevel)
    try:
        myfile = open(filepath, 'w')
        myfile.write(writestring)
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error writing supplicant file. ', 1, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Supplicant file written. ', 3, pilib.networkloglevel)


def updatewpasupplicant(interface='wlan0'):
    # print('I AM UPDATING SUPPLICANT DATA')
    try:
        suppdata = getwpasupplicantconfig()
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error getting supplicant data. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Supplicant data retrieved successfully. ', 3, pilib.networkloglevel)

    try:
        updateddata = updatesupplicantdata(suppdata)
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error updating supplicant data. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Supplicant data retrieved successfully. ', 3, pilib.networkloglevel)

    try:
        writesupplicantfile(updateddata)
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error writing supplicant data. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Supplicant data written successfully. ', 3, pilib.networkloglevel)


def replaceifaceparameters(iffilein, iffileout, iface, parameternames, parametervalues):
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
        pilib.writedatedlogmsg(pilib.networklog, 'Error opening interface file. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Interface file read successfully. ', 3, pilib.networkloglevel)

    try:
        myfile.write(writestring)
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error writing interface file. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Interface file written successfully. ', 3, pilib.networkloglevel)
        pilib.writedatedlogmsg(pilib.networklog, 'Write string: ' + writestring, 3, pilib.networkloglevel)


def setstationmode(netconfigdata=None):
    pilib.writedatedlogmsg(pilib.networklog, 'Setting station mode. ', 3, pilib.networkloglevel)
    from time import sleep
    if not netconfigdata:
        pilib.writedatedlogmsg(pilib.networklog, 'Retrieving unfound netconfig data. ', 3, pilib.networkloglevel)
        try:
            netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
        except:
            pilib.writedatedlogmsg(pilib.networklog, 'Error reading netconfig data. ', 0, pilib.networkloglevel)
        else:
            pilib.writedatedlogmsg(pilib.networklog, 'Read netconfig data. ', 4, pilib.networkloglevel)

    killapservices()
    if netconfigdata['addtype'] == 'static':
        pilib.writedatedlogmsg(pilib.networklog, 'Configuring static address. ', 3, pilib.networkloglevel)

        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.static', '/etc/network/interfaces'])

        # update IP from netconfig
        pilib.writedatedlogmsg(pilib.networklog, 'Updating netconfig with ip ' + netconfigdata['address'], 3, pilib.networkloglevel)
        replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                               [netconfigdata['address'], netconfigdata['gateway']])
    elif netconfigdata['addtype'] == 'dhcp':
        pilib.writedatedlogmsg(pilib.networklog, 'Configuring dhcp. ', 3, pilib.networkloglevel)
        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.dhcp', '/etc/network/interfaces'])

    pilib.writedatedlogmsg(pilib.networklog, 'Resetting wlan. ', 3,pilib.networkloglevel)
    resetwlan()
    sleep(1)
    resetwlan()


def killapservices():
    pilib.writedatedlogmsg(pilib.networklog, 'Killing AP Services. ', 1, pilib.networkloglevel)
    try:
        killhostapd()
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error killing hostapd. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Killed hostapd. ', 3, pilib.networkloglevel)

    try:
        killdhcpserver()
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error killing dhcp server. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Successfully killed dhcp server. ', 3, pilib.networkloglevel)


def killhostapd():
    subprocess.call(['/usr/sbin/service', 'hostapd', 'stop'])
    subprocess.call(['pkill','hostapd'])
    return


def killdhcpserver():
    subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'stop'])
    subprocess.call(['pkill','isc-dhcp-server'])
    return


def startapservices(interface='wlan0'):
    from time import sleep
    try:
        updatehostapd(path='/etc/hostapd/hostapd.conf', interface=interface)
        subprocess.call(['/usr/sbin/hostapd', '-B', '/etc/hostapd/hostapd.conf'])
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error starting hostapd. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Started hostapd without error. ', 3, pilib.networkloglevel)

    sleep(1)

    try:
        updatedhcpd(path='/etc/dhcp/dhcpd.conf', interface=interface)
        subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'start'])
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error starting dhcp server. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Started dhcp server without error. ', 3, pilib.networkloglevel)


def setapmode(interface='wlan0', netconfig=None):
    pilib.writedatedlogmsg(pilib.networklog, 'Setting ap mode for interface ' + interface, 1, pilib.networkloglevel)
    try:
        if interface == 'wlan0':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.ap', '/etc/network/interfaces'])
        elif interface == 'wlan0wlan1':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan0dhcp.wlan1cupidwifi', '/etc/network/interfaces'])
        elif interface == 'wlan1wlan0':
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan1dhcp.wlan0cupidwifi', '/etc/network/interfaces'])
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error copying network configuration file. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Copied network configuration file successfully. ', 3, pilib.networkloglevel)

    killapservices()
    resetwlan()
    startapservices(interface)


def resetwlan(interface='wlan0'):
    pilib.writedatedlogmsg(pilib.networklog, 'Resetting' + interface + ' . ', 3, pilib.networkloglevel)
    try:
        subprocess.check_output(['/sbin/ifdown', '--force', interface], stderr=subprocess.PIPE)
        subprocess.call(['/sbin/ifup', interface], stderr=subprocess.PIPE)
    except Exception, e:
        pilib.writedatedlogmsg(pilib.networklog, 'Error resetting ' + interface + ' : ' + str(e), 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Completed resetting '+ interface + '. ', 3, pilib.networkloglevel)


def runconfig(onboot=False):
    import subprocess
    try:
        netconfigdata = pilib.readonedbrow(pilib.systemdatadatabase, 'netconfig')[0]
        # print(netconfigdata)
    except:
        pilib.writedatedlogmsg(pilib.networklog, 'Error reading netconfig data. ', 0, pilib.networkloglevel)
    else:
        pilib.writedatedlogmsg(pilib.networklog, 'Successfully read netconfig data', 3, pilib.networkloglevel)

        pilib.setsinglevalue(pilib.systemdatadatabase, 'netstatus', 'mode', netconfigdata['mode'])

        pilib.writedatedlogmsg(pilib.networklog, 'Netconfig is enabled', 3, pilib.networkloglevel)

        # This will grab the specified SSID and the credentials and update
        # the wpa_supplicant file
        updatewpasupplicant()

        # Copy the correct interfaces file
        if netconfigdata['mode'] == 'station':
            setstationmode(netconfigdata)
        elif netconfigdata['mode'] in ['ap', 'tempap', 'eth0wlan0bridge']:
            pilib.writedatedlogmsg(pilib.networklog, 'Setting eth0wlan0 bridge (or bare ap mode). ', 0, pilib.networkloglevel)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.ap', '/etc/network/interfaces'])
            killapservices()
            resetwlan()
            startapservices('wlan0')

        # All of these require ipv4 being enabled in /etc/sysctl.conf
        # First interface is DHCP, second is CuPIDwifi
        elif netconfigdata['mode'] == 'wlan0wlan1bridge':
            pilib.writedatedlogmsg(pilib.networklog, 'Setting wlan0wlan1 bridge', 0, pilib.networkloglevel)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan0dhcp.wlan1cupidwifi', '/etc/network/interfaces'])
            killapservices()
            resetwlan('wlan0')
            resetwlan('wlan1')
            startapservices('wlan1')

        elif netconfigdata['mode'] == 'wlan1wlan0bridge':
            pilib.writedatedlogmsg(pilib.networklog, 'Setting wlan1wlan0 bridge', 0, pilib.networkloglevel)
            subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.wlan1dhcp.wlan0cupidwifi', '/etc/network/interfaces'])
            killapservices()
            resetwlan('wlan0')
            resetwlan('wlan1')
            startapservices('wlan0')

        runIPTables(netconfigdata['mode'])


def runIPTables(mode, flush=True):
    import pilib
    if flush:
        pilib.writedatedlogmsg(pilib.networklog, 'Flushing IPTables', 2, pilib.networkloglevel)
        flushIPTables()
    if mode == 'eth0wlan0bridge':
        pilib.writedatedlogmsg(pilib.networklog, 'Running eth0wlan0 bridge IPTables', 2, pilib.networkloglevel)
        runeth0wlan0bridgeIPTables()
    elif mode == 'wlan0wlan1bridge':
        pilib.writedatedlogmsg(pilib.networklog, 'Running wlan0wlan1 bridge IPTables', 2, pilib.networkloglevel)
        runwlan0wlan1bridgeIPTables()
    elif mode == 'wlan1wlan0bridge':
        pilib.writedatedlogmsg(pilib.networklog, 'Running wlan1wlan0 bridge IPTables', 2, pilib.networkloglevel)
        runwlan1wlan0bridgeIPTables()


def runeth0wlan0bridgeIPTables():
    # eth0 has ethernet connectivity. wlan0 is AP
    subprocess.call(['iptables','-t','nat','-A','POSTROUTING','-o','eth0','-j','MASQUERADE'])
    subprocess.call(['iptables','-A','FORWARD','-i','eth0','-o','wlan0','-m','state','--state','RELATED,ESTABLISHED','-j','ACCEPT'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan0','-o','eth0','-j','ACCEPT'])


def runwlan0wlan1bridgeIPTables():
    # wlan0 has ethernet connectivity. wlan1 is AP
    subprocess.call(['iptables', '-t', 'nat', '-A', 'POSTROUTING','-o', 'wlan0', '-j', 'MASQUERADE'])
    subprocess.call(['iptables', '-A', 'FORWARD', '-i', 'wlan0', '-o', 'wlan1', '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'])
    subprocess.call(['iptables', '-A', 'FORWARD', '-i', 'wlan1', '-o', 'wlan0', '-j', 'ACCEPT'])


def runwlan1wlan0bridgeIPTables():
    # wlan1 has ethernet connectivity. wlan0 is AP
    subprocess.call(['iptables','-t','nat','-A','POSTROUTING','-o','wlan1','-j','MASQUERADE'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan1','-o','wlan0','-m','state','--state','RELATED,ESTABLISHED','-j','ACCEPT'])
    subprocess.call(['iptables','-A','FORWARD','-i','wlan0','-o','wlan1','-j','ACCEPT'])


def flushIPTables():
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
    runconfig()
    # updatewpasupplicant()