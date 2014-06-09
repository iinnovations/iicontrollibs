#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

try:
    import os
    import sys
    import inspect
    import subprocess
except ImportError:
    print('Import error. Exiting.')
    exit

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from cupid.pilib import readonedbrow, systemdatadatabase, writedatedlogmsg, netconfiglog, netconfigloglevel, systemstatuslog, systemstatusloglevel


def getwpaclientstatus():
    import subprocess

    try:
        result = subprocess.Popen(['/sbin/wpa_cli', 'status'], stdout=subprocess.PIPE)
        writedatedlogmsg(netconfiglog, 'Error reading wpa client status. ')
    except:
        writedatedlogmsg(netconfiglog, 'Error reading wpa client status. ', 0, netconfigloglevel)


    # prune interface ID
    resultdict = {}

    for result in result.stdout:
        if result.find('=') > 0:
            split = result.split('=')
            resultdict[split[0]] = split[1].strip()
    return resultdict


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
            writedatedlogmsg(netconfiglog, 'Ending supplicant parse. ', 5, netconfigloglevel)
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            writedatedlogmsg(netconfiglog, 'Beginning supplicant parse. ', 5, netconfigloglevel)
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

    try:
        netconfig = readalldbrows(systemdatadatabase, 'netconfig')[0]
    except:
         writedatedlogmsg(netconfiglog, 'Error reading netconfig data. ', 0, netconfigloglevel)
    else:
         writedatedlogmsg(netconfiglog, 'Read netconfig data. ', 4, netconfigloglevel)

    try:
        wirelessauths = readalldbrows(safedatabase, 'wireless')
    except:
         writedatedlogmsg(netconfiglog, 'Error reading wireless data. ', 0, netconfigloglevel)
    else:
         writedatedlogmsg(netconfiglog, 'Read wireless data. ', 4, netconfigloglevel)

    password = ''

    writedatedlogmsg(netconfiglog, 'Netconfig data: ' + str(netconfig), 2, netconfigloglevel)

    # we only update if we find the credentials
    for auth in wirelessauths:
        if auth['SSID'] == netconfig['SSID']:
            password = '"' + auth['password'] + '"'
            ssid = '"' + auth['SSID'] + '"'
            writedatedlogmsg(netconfiglog, 'SSID ' + auth['SSID'] + 'found. ', 1, netconfigloglevel)
            configdata.data['psk'] = password
            configdata.data['ssid'] = ssid
    return configdata


def writesupplicantfile(filedata, filepath='/etc/wpa_supplicant/wpa_supplicant.conf'):
    writestring = ''
    writestring += filedata.header
    for key, value in filedata.data.items():
        writestring += key + '=' + value + '\n'
    writestring += filedata.tail
    writedatedlogmsg(netconfiglog, 'Writing supplicant file. ', 1, netconfigloglevel)
    try:
        myfile = open(filepath, 'w')
        myfile.write(writestring)
    except:
        writedatedlogmsg(netconfiglog, 'Error writing supplicant file. ', 1, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Supplicant file written. ', 3, netconfigloglevel)


def updatewpasupplicant():
    try:
        suppdata = getwpasupplicantconfig()
    except:
        writedatedlogmsg(netconfiglog, 'Error getting supplicant data. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Supplicant data retrieved successfully. ', 3, netconfigloglevel)
    try:
        updateddata = updatesupplicantdata(suppdata)
    except:
        writedatedlogmsg(netconfiglog, 'Error updating supplicant data. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Supplicant data retrieved successfully. ', 3, netconfigloglevel)
    try:
        writesupplicantfile(updateddata)
    except:
        writedatedlogmsg(netconfiglog, 'Error writing supplicant data. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Supplicant data written successfully. ', 3, netconfigloglevel)

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
        writedatedlogmsg(netconfiglog, 'Error opening interface file. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Interface file read successfully. ', 3, netconfigloglevel)

    try:
        myfile.write(writestring)
    except:
        writedatedlogmsg(netconfiglog, 'Error writing interface file. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Interface file written successfully. ', 3, netconfigloglevel)
        writedatedlogmsg(netconfiglog, 'Write string: ' + writestring, 3, netconfigloglevel)


def setstationmode(netconfigdata=None):
    writedatedlogmsg(netconfiglog, 'Setting station mode. ', 3, netconfigloglevel)
    from time import sleep
    if not netconfigdata:
        writedatedlogmsg(netconfiglog, 'Retrieving unfound netconfig data. ', 3, netconfigloglevel)
        try:
            netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
        except:
            writedatedlogmsg(netconfiglog, 'Error reading netconfig data. ', 0, netconfigloglevel)
        else:
            writedatedlogmsg(netconfiglog, 'Read netconfig data. ', 4, netconfigloglevel)

    killapservices()
    if netconfigdata['addtype'] == 'static':
        writedatedlogmsg(netconfiglog, 'Configuring static address. ', 3, netconfigloglevel)

        subprocess.call(['cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.static', '/etc/network/interfaces'])

        # update IP from netconfig
        writedatedlogmsg(netconfiglog, 'Updating netconfig with ip ' + netconfigdata['address'], 3, netconfigloglevel)
        replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                               [netconfigdata['address'], netconfigdata['gateway']])
    elif netconfigdata['addtype'] == 'dhcp':
        writedatedlogmsg(netconfiglog, 'Configuring dhcp. ', 3, netconfigloglevel)
        subprocess.call(['cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.dhcp', '/etc/network/interfaces'])

    writedatedlogmsg(netconfiglog, 'Resetting wlan. ', 3, netconfigloglevel)
    resetwlan()
    sleep(1)
    resetwlan()


def killapservices():
    writedatedlogmsg(netconfiglog, 'Killing AP Services. ', 1, netconfigloglevel)
    try:
        subprocess.call(['service', 'hostapd', 'stop'])
    except:
        writedatedlogmsg(netconfiglog, 'Error killing hostapd. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Killed hostapd. ', 3, netconfigloglevel)

    try:
        subprocess.call(['service', 'isc-dhcp-server', 'stop'])
    except:
        writedatedlogmsg(netconfiglog, 'Error killing dhcp server. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Successfully killed dhcp server. ', 3, netconfigloglevel)


def startapservices():
    from time import sleep
    try:
        subprocess.call(['hostapd', '-B', '/etc/hostapd/hostapd.conf'])
    except:
        writedatedlogmsg(netconfiglog, 'Error starting hostapd. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Started hostapd without error. ', 3, netconfigloglevel)

    sleep(1)

    try:
        subprocess.call(['service', 'isc-dhcp-server', 'start'])
    except:
        writedatedlogmsg(netconfiglog, 'Error starting dhcp server. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Started dhcp server without error. ', 3, netconfigloglevel)


def setapmode(netconfig=None):
    writedatedlogmsg(netconfiglog, 'Setting ap mode. ', 1, netconfigloglevel)
    try:
        subprocess.call(['cp', '/etc/network/interfaces.ap', '/etc/network/interfaces'])
    except:
        writedatedlogmsg(netconfiglog, 'Error copying network configuration file. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Copied network configuration file successfully. ', 3, netconfigloglevel)

    killapservices()
    resetwlan()
    startapservices()


def resetwlan():
    from time import sleep
    writedatedlogmsg(netconfiglog, 'Resetting wlan. ', 3, netconfigloglevel)
    try:
        subprocess.call(['ifdown', '--force', 'wlan0'])
    except:
        writedatedlogmsg(netconfiglog, 'Error bringing down wlan0. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Completed bringing down wlan0 ', 3, netconfigloglevel)
    sleep(2)
    try:
        subprocess.call(['ifup', 'wlan0'])
    except:
        writedatedlogmsg(netconfiglog, 'Error bringing up wlan0. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Completed bringing up wlan0 ', 3, netconfigloglevel)


def runconfig(onboot=False):
    import subprocess
    try:
        netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
    except:
        writedatedlogmsg(netconfiglog, 'Error reading netconfig data. ', 0, netconfigloglevel)
    else:
        writedatedlogmsg(netconfiglog, 'Successfully read netconfig data', 3, netconfigloglevel)
        if netconfigdata['enabled']:
            writedatedlogmsg(netconfiglog, 'Netconfig is enabled', 3, netconfigloglevel)

            # This will grab the specified SSID and the credentials and update
            # the wpa_supplicant file
            updatewpasupplicant()
            # Copy the correct interfaces file
            if netconfigdata['mode'] == 'station':
                setstationmode(netconfigdata)
            elif netconfigdata['mode'] in ['ap', 'tempap']:
                setapmode()

                # Unfortunately, we currently need to reboot prior to setting
                # ap mode to get it to stick unless we are doing it at bootup
                if not onboot:
                    writedatedlogmsg(netconfiglog, 'Rebooting. ', 0, netconfigloglevel)
                    writedatedlogmsg(systemstatuslog, 'Rebooting. ', 0, systemstatusloglevel)
                    subprocess.call(['reboot'])

        else:
            writedatedlogmsg(netconfiglog, 'Netconfig is disabled', 3, netconfigloglevel)


if __name__ == "__main__":
    # This will run the configuration script (if netconfig is enabled) and set
    # ap or station mode, and finally bring down and up wlan0
    runconfig()
    # updatewpasupplicant()