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

from cupid.pilib import readonedbrow, systemdatadatabase, writedatedlogmsg, networklog, networkloglevel, systemstatuslog, systemstatusloglevel


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
            writedatedlogmsg(networklog, 'Ending supplicant parse. ', 5, networkloglevel)
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            writedatedlogmsg(networklog, 'Beginning supplicant parse. ', 5, networkloglevel)
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
         writedatedlogmsg(networklog, 'Error reading netconfig data. ', 0, networkloglevel)
    else:
         writedatedlogmsg(networklog, 'Read netconfig data. ', 4, networkloglevel)

    try:
        wirelessauths = readalldbrows(safedatabase, 'wireless')
    except:
         writedatedlogmsg(networklog, 'Error reading wireless data. ', 0, networkloglevel)
    else:
         writedatedlogmsg(networklog, 'Read wireless data. ', 4, networkloglevel)

    password = ''

    writedatedlogmsg(networklog, 'Netconfig data: ' + str(netconfig), 2, networkloglevel)

    # we only update if we find the credentials
    for auth in wirelessauths:
        if auth['SSID'] == netconfig['SSID']:
            password = '"' + auth['password'] + '"'
            ssid = '"' + auth['SSID'] + '"'
            writedatedlogmsg(networklog, 'SSID ' + auth['SSID'] + 'found. ', 1, networkloglevel)
            configdata.data['psk'] = password
            configdata.data['ssid'] = ssid
    return configdata


def writesupplicantfile(filedata, filepath='/etc/wpa_supplicant/wpa_supplicant.conf'):
    writestring = ''
    writestring += filedata.header
    for key, value in filedata.data.items():
        writestring += key + '=' + value + '\n'
    writestring += filedata.tail
    writedatedlogmsg(networklog, 'Writing supplicant file. ', 1, networkloglevel)
    try:
        myfile = open(filepath, 'w')
        myfile.write(writestring)
    except:
        writedatedlogmsg(networklog, 'Error writing supplicant file. ', 1, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Supplicant file written. ', 3, networkloglevel)


def updatewpasupplicant():
    try:
        suppdata = getwpasupplicantconfig()
    except:
        writedatedlogmsg(networklog, 'Error getting supplicant data. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Supplicant data retrieved successfully. ', 3, networkloglevel)

    try:
        updateddata = updatesupplicantdata(suppdata)
    except:
        writedatedlogmsg(networklog, 'Error updating supplicant data. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Supplicant data retrieved successfully. ', 3, networkloglevel)

    try:
        writesupplicantfile(updateddata)
    except:
        writedatedlogmsg(networklog, 'Error writing supplicant data. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Supplicant data written successfully. ', 3, networkloglevel)


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
        writedatedlogmsg(networklog, 'Error opening interface file. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Interface file read successfully. ', 3, networkloglevel)

    try:
        myfile.write(writestring)
    except:
        writedatedlogmsg(networklog, 'Error writing interface file. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Interface file written successfully. ', 3, networkloglevel)
        writedatedlogmsg(networklog, 'Write string: ' + writestring, 3, networkloglevel)


def setstationmode(netconfigdata=None):
    writedatedlogmsg(networklog, 'Setting station mode. ', 3, networkloglevel)
    from time import sleep
    if not netconfigdata:
        writedatedlogmsg(networklog, 'Retrieving unfound netconfig data. ', 3, networkloglevel)
        try:
            netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
        except:
            writedatedlogmsg(networklog, 'Error reading netconfig data. ', 0, networkloglevel)
        else:
            writedatedlogmsg(networklog, 'Read netconfig data. ', 4, networkloglevel)

    killapservices()
    if netconfigdata['addtype'] == 'static':
        writedatedlogmsg(networklog, 'Configuring static address. ', 3, networkloglevel)

        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.static', '/etc/network/interfaces'])

        # update IP from netconfig
        writedatedlogmsg(networklog, 'Updating netconfig with ip ' + netconfigdata['address'], 3, networkloglevel)
        replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                               [netconfigdata['address'], netconfigdata['gateway']])
    elif netconfigdata['addtype'] == 'dhcp':
        writedatedlogmsg(networklog, 'Configuring dhcp. ', 3, networkloglevel)
        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.sta.dhcp', '/etc/network/interfaces'])

    writedatedlogmsg(networklog, 'Resetting wlan. ', 3, networkloglevel)
    resetwlan()
    sleep(1)


def killapservices():
    writedatedlogmsg(networklog, 'Killing AP Services. ', 1, networkloglevel)
    try:
        subprocess.call(['/usr/sbin/service', 'hostapd', 'stop'])
    except:
        writedatedlogmsg(networklog, 'Error killing hostapd. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Killed hostapd. ', 3, networkloglevel)

    try:
        subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'stop'])
    except:
        writedatedlogmsg(networklog, 'Error killing dhcp server. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Successfully killed dhcp server. ', 3, networkloglevel)


def startapservices():
    from time import sleep
    try:
        subprocess.call(['/usr/sbin/hostapd', '-B', '/etc/hostapd/hostapd.conf'])
    except:
        writedatedlogmsg(networklog, 'Error starting hostapd. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Started hostapd without error. ', 3, networkloglevel)

    sleep(1)

    try:
        subprocess.call(['/usr/sbin/service', 'isc-dhcp-server', 'start'])
    except:
        writedatedlogmsg(networklog, 'Error starting dhcp server. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Started dhcp server without error. ', 3, networkloglevel)


def setapmode(netconfig=None):
    writedatedlogmsg(networklog, 'Setting ap mode. ', 1, networkloglevel)
    try:
        subprocess.call(['/bin/cp', '/usr/lib/iicontrollibs/misc/interfaces/interfaces.ap', '/etc/network/interfaces'])
    except:
        writedatedlogmsg(networklog, 'Error copying network configuration file. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Copied network configuration file successfully. ', 3, networkloglevel)

    killapservices()
    resetwlan()
    startapservices()


def resetwlan():
    writedatedlogmsg(networklog, 'Resetting wlan. ', 3, networkloglevel)
    try:
        subprocess.call(['/sbin/ifdown', '--force', 'wlan0'])
        subprocess.call(['/sbin/ifup', 'wlan0'])
    except Exception, e:
        writedatedlogmsg(networklog, 'Error resetting wlan0: ' + str(e), 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Completed resetting down wlan0 ', 3, networkloglevel)


def runconfig(onboot=False):
    import subprocess
    try:
        netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
        # print(netconfigdata)
    except:
        writedatedlogmsg(networklog, 'Error reading netconfig data. ', 0, networkloglevel)
    else:
        writedatedlogmsg(networklog, 'Successfully read netconfig data', 3, networkloglevel)
        if netconfigdata['enabled']:
            print('I AM ENABLED')
            writedatedlogmsg(networklog, 'Netconfig is enabled', 3, networkloglevel)

            # This will grab the specified SSID and the credentials and update
            # the wpa_supplicant file
            updatewpasupplicant()

            # Copy the correct interfaces file
            if netconfigdata['mode'] == 'station':
                print('I AM STATION MODE')
                setstationmode(netconfigdata)
            elif netconfigdata['mode'] in ['ap', 'tempap']:
                setapmode()

                # Unfortunately, we currently need to reboot prior to setting
                # ap mode to get it to stick unless we are doing it at bootup
                if not onboot:
                    writedatedlogmsg(networklog, 'Rebooting after set ap mode', 0, networkloglevel)
                    writedatedlogmsg(systemstatuslog, 'Rebooting after set ap mode ', 0, systemstatusloglevel)
                    # subprocess.call(['reboot'])

        else:
            writedatedlogmsg(networklog, 'Netconfig is disabled', 3, networkloglevel)


if __name__ == "__main__":
    # This will run the configuration script (if netconfig is enabled) and set
    # ap or station mode, and finally bring down and up wlan0
    runconfig()
    # updatewpasupplicant()