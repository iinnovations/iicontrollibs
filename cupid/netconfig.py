#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os, sys, inspect, subprocess

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from cupid.pilib import readonedbrow, systemdatadatabase


def getwpaclientstatus():
    import subprocess

    result = subprocess.Popen(['wpa_cli', 'status'], stdout=subprocess.PIPE)
    # prune interface ID
    resultdict = {}

    for result in result.stdout:
        if result.find('=') > 0:
            split = result.split('=')
            resultdict[split[0]] = split[1].strip()
    # print(resultdict)
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
            print('parsing ended')
            readbody = False
            readtail = True
        if readbody:
            datalines.append(line)
        if readtail:
            tail = tail + line
        if '{' in line:
            print('starting parse')
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

    netconfig = readalldbrows(systemdatadatabase, 'netconfig')[0]
    wirelessauths = readalldbrows(safedatabase, 'wireless')
    password = ''
    print(netconfig)
    # we only update if we find the credentials
    for auth in wirelessauths:
        if auth['SSID'] == netconfig['SSID']:
            password = '"' + auth['password'] + '"'
            ssid = '"' + auth['SSID'] + '"'
            # print(password)
            print('found')
            configdata.data['psk'] = password
            configdata.data['ssid'] = ssid
    return configdata


def writesupplicantfile(filedata, filepath='/etc/wpa_supplicant/wpa_supplicant.conf'):
    writestring = ''
    writestring += filedata.header
    for key, value in filedata.data.items():
        writestring += key + '=' + value + '\n'
    writestring += filedata.tail
    myfile = open(filepath, 'w')
    myfile.write(writestring)


def updatewpasupplicant():
    suppdata = getwpasupplicantconfig()
    updateddata = updatesupplicantdata(suppdata)
    writesupplicantfile(updateddata)


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
    myfile = open(iffileout, 'w')
    myfile.write(writestring)
    print(writestring)


def setstationmode(netconfigdata=None):
    if not netconfigdata:
        netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
    killapservices()
    if netconfigdata['addtype'] == 'static':

        subprocess.call(['cp', '/etc/network/interfaces.sta.static', '/etc/network/interfaces'])
        # update IP from netconfig
        print(netconfigdata['address'])
        replaceifaceparameters('/etc/network/interfaces', '/etc/network/interfaces', 'wlan0', ['address', 'gateway'],
                               [netconfigdata['address'], netconfigdata['gateway']])
    elif netconfigdata['addtype'] == 'dhcp':
        subprocess.call(['cp', '/etc/network/interfaces.sta.dhcp', '/etc/network/interfaces'])
    resetwlan()


def killapservices():
    subprocess.call(['service', 'hostapd', 'stop'])
    subprocess.call(['service', 'isc-dhcp-server', 'stop'])


def startapservices():
    from time import sleep

    subprocess.call(['hostapd', '-B', '/etc/hostapd/hostapd.conf'])
    sleep(1)
    subprocess.call(['service', 'isc-dhcp-server', 'start'])


def setapmode(netconfig=None):
    if not netconfig:
        netconfig = readonedbrow(systemdatadatabase, 'netconfig')[0]
    subprocess.call(['cp', '/etc/network/interfaces.ap', '/etc/network/interfaces'])
    killapservices()
    resetwlan()
    # Run hostapd
    print('*********************************')
    print('starting hostapd and dhcp server')
    print('*********************************')
    startapservices()


def resetwlan():
    from time import sleep

    print('resetting wlan0')
    subprocess.call(['ifdown', '--force', 'wlan0'])
    sleep(2)
    subprocess.call(['ifup', 'wlan0'])


def runconfig(onboot=False):
    import subprocess

    netconfigdata = readonedbrow(systemdatadatabase, 'netconfig')[0]
    if netconfigdata['enabled']:
        # This will grab the specified SSID and the credentials and update
        # the wpa_supplicant file
        updatewpasupplicant()
        # Copy the correct interfaces file
        if netconfigdata['mode'] == 'station':
            print('station mode')
            setstationmode(netconfigdata)
        elif netconfigdata['mode'] in ['ap', 'tempap']:
            print('access point mode')
            setapmode()

            # Unfortunately, we currently need to reboot prior to setting
            # ap mode to get it to stick unless we are doing it at bootup
            if not onboot:
                print('time to reboot')
                subprocess.call(['reboot'])

    else:
        print('automatic net configuration disabled')


if __name__ == "__main__":
    # This will run the configuration script (if netconfig is enabled) and set
    # ap or station mode, and finally bring down and up wlan0
    runconfig()
    # updatewpasupplicant()