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
reboot=False
if len(args)>1:
    print('argument found')
    arg2 = args[1]
    print('argument ' + arg2)
    if args=='reboot':
        reboot=True
     

def runconfig(reboot):
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
        apinit()
        if reboot:
            print('time to reboot')
            subprocess.call(['reboot'])

def apinit():
    # Run hostapd 
    print('*********************************')
    print('starting hostapd and dhcp server')
    print('*********************************')
    subprocess.call(['hostapd','-B', '/etc/hostapd/hostapd.conf'])
    subprocess.call(['service','isc-dhcp-server','start'])

if __name__=="__main__":
    runconfig(reboot)
