#!/usr/bin/python

import os,sys,inspect,subprocess
top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0,top_folder)

from cupid.pilib import readonedbrow

database='/var/www/data/controldata.db'

# Read the config from the database

netsettings=readonedbrow(database,'network')[0]

args = sys.argv
if len(args)>1:
    arg = args[1]
else:
    arg = 'restartinit'

reboot=True
if len(args)>2:
    arg2 = args[2]
    if args='noreboot':
        reboot=False

print('arguments passed')
print(arg)

if arg=='reinit':

    # Copy the correct interfaces file
    if netsettings['nettype']=='station':
        print('station mode')
        if netsettings['addtype']=='static':
            subprocess.call(['cp','/etc/network/interfaces.sta.static','/etc/network/interfaces']) 
        elif netsettings['addtype']=='dhcp':
            subprocess.call(['cp','/etc/network/interfaces.sta.dhcp','/etc/network/interfaces']) 
        print('rebooting to enact changes')
        if reboot:
            print('time to reboot')
            subprocess.call(['reboot'])
    elif netsettings['nettype']=='ap':
        print('access point mode')
        subprocess.call(['cp','/etc/network/interfaces.ap','/etc/network/interfaces']) 
        print('rebooting to enact changes')
        if reboot:
            print('time to reboot')
            subprocess.call(['reboot'])
    else:
        print('mode error')

elif arg=='restartinit':
    # Run hostapd if necessary
    if netsettings['nettype']=='ap':
        print('*********************************')
        print('starting hostapd and dhcp server')
        print('*********************************')
        subprocess.call(['hostapd','-B', '/etc/hostapd/hostapd.conf'])
        subprocess.call(['service','isc-dhcp-server','start'])
    print('bringing down wlan0')
    subprocess.call(['ifdown','wlan0'])
    print('bringing up wlan0')
    subprocess.call(['ifup','wlan0'])
    
else:
    print(' invalid argument passed')
    print(' valid arguments are:')
    print(' reinit: reset with reboot')
    print(' restartinit: initialize hostapd and dhcp')
    print('   if specified by controldb')
