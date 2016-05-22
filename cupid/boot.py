#!/usr/bin/env python

import subprocess
from time import sleep

import pilib
import spilights
import utilities.dblib
from utilities import utility, dblib

interfaces = dblib.readalldbrows(pilib.controldatabase, 'interfaces')
systemstatus = dblib.readonedbrow(pilib.controldatabase, 'systemstatus')[0]

# Start pigpiod

subprocess.call(['killall','pigpiod'])
sleep(1)
utility.log(pilib.syslog, 'boot: starting pigpio daemon', 3, pilib.sysloglevel)
subprocess.call(['/usr/local/bin/pigpiod'])

# Start webserver

subprocess.call(['killall','nginx'])
subprocess.call(['killall','uwsgi'])
subprocess.call(['killall','apache2'])

if systemstatus['webserver'] == 'apache':
    utility.log(pilib.syslog, 'boot: starting apache', 3, pilib.sysloglevel)
    subprocess.call(['service', 'apache2', 'start'])
elif systemstatus['webserver'] == 'nginx':
    utility.log(pilib.syslog, 'boot: starting nginx', 3, pilib.sysloglevel)
    subprocess.call(['service', 'nginx', 'start'])

# Run uwsgi daemon if nginx is running

try:
    result = subprocess.check_output(['service', 'nginx', 'status'])
except subprocess.CalledProcessError as e:
    result = ''
    # print('I AM FAILING')
    # print e.output

if result:
    utility.log(pilib.syslog, 'boot: starting uwsgi based on nginx call', 0)
    subprocess.call(['uwsgi', '--emperor', '/usr/lib/iicontrollibs/wsgi/', '--daemonize', '/var/log/cupid/uwsgi.log'])
else:
    # print(' I KNOW NGINX IS NOT RUNNING')
    pass
# Mount 1wire master

subprocess.call(['killall','owfs'])
subprocess.call(['killall','owserver'])
subprocess.call(['killall','owhttpd'])

runi2cowfs = True
runusbowfs = False

mightyboost = True
if mightyboost:
    subprocess.Popen(['/usr/lib/iicontrollibs/misc/mightyboost.sh','&'])


for interface in interfaces:
    if interface['enabled']:
        if interface['interface'] == 'I2C' and interface['type'] == 'DS2483':
            runi2cowfs = True
        if interface['interface'] == 'USB' and interface['type'] == 'DS9490':
            runusbowfs = True

        if interface['interface'] == 'SPI1' and type == 'CuPIDlights':
            spilights.updatelightsfromdb(pilib.controldatabase, 'indicators', 1)
        if interface['interface'] == 'SPI0' and type == 'CuPIDlights':
            spilights.updatelightsfromdb(pilib.controldatabase, 'indicators', 0)

if runi2cowfs or runusbowfs:
    if runi2cowfs:
        utility.log(pilib.syslog, 'boot: Running i2c owserver', 3, pilib.sysloglevel)
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
        except:
            utility.log(pilib.syslog, 'boot: error running i2c owserver', 1, pilib.sysloglevel)
    if runusbowfs:
        utility.log(pilib.syslog, 'boot: Running usb owserver', 3, pilib.sysloglevel)
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '-u', '-p', '4304'])
        except:
            utility.log(pilib.syslog, 'error running usb owserver', 1, pilib.sysloglevel)

    utility.log(pilib.syslog, 'boot: Running owfs/owserver mount', 3, pilib.sysloglevel)
    try:
        subprocess.call(['/opt/owfs/bin/owfs', '-F', '-s', '4304', '/var/1wire/'])
    except:
        utility.log(pilib.syslog, 'boot: error running owfs', 1, pilib.sysloglevel)

    utility.log(pilib.syslog, 'boot: Running owhttpd/owserver mount', 3, pilib.sysloglevel)
    try:
        subprocess.call(['/opt/owfs/bin/owhttpd', '-F', '-s', '4304', '-p', '4305'])
    except:
        utility.log(pilib.syslog, 'boot: error running owhttpd', 1, pilib.sysloglevel)

else:
    utility.log(pilib.syslog, 'boot: not running owfs', 3, pilib.sysloglevel)

# Run netstart script if enabled
if systemstatus['netconfigenabled']:
    from netconfig import runconfig
    utility.log(pilib.syslog, 'boot: running boot netconfig', 2, pilib.sysloglevel)
    runconfig(onboot=True)

# Run daemon
from cupiddaemon import rundaemon

rundaemon()

# Update hardware version in table
from systemstatus import readhardwarefileintoversions

readhardwarefileintoversions()

