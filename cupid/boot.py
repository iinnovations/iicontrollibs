#!/usr/bin/env python

# Mount 1wire master

import subprocess
import pilib
import spilights

interfaces = pilib.readalldbrows(pilib.controldatabase, 'interfaces')
systemstatus = pilib.readonedbrow(pilib.controldatabase, 'systemstatus')[0]

pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: starting pigpio daemon', 3, pilib.systemstatusloglevel)
subprocess.call(['pigpiod'])

if systemstatus['webserver'] == 'apache':
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: starting apache', 3, pilib.systemstatusloglevel)
    subprocess.call(['service', 'apache2', 'start'])
elif systemstatus['webserver'] == 'nginx':
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: starting nginx', 3, pilib.systemstatusloglevel)
    subprocess.call(['service', 'nginx', 'start'])


runi2cowfs = False
runusbowfs = False
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
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: Running i2c owserver', 3, pilib.systemstatusloglevel)
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
        except:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: error running i2c owserver', 1, pilib.systemstatusloglevel)
    if runusbowfs:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: Running usb owserver', 3, pilib.systemstatusloglevel)
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '-u', '-p', '4304'])
        except:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'error running usb owserver', 1, pilib.systemstatusloglevel)

    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: Running owfs/owserver mount', 3, pilib.systemstatusloglevel)
    try:
        subprocess.call(['/opt/owfs/bin/owfs', '-F', '-s', '4304', '/var/1wire/'])
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: error running owfs', 1, pilib.systemstatusloglevel)

    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: Running owhttpd/owserver mount', 3, pilib.systemstatusloglevel)
    try:
        subprocess.call(['/opt/owfs/bin/owhttpd', '-F', '-s', '4304', '-p', '4305'])
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: error running owhttpd', 1, pilib.systemstatusloglevel)

else:
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: not running owfs', 3, pilib.systemstatusloglevel)

# Run netstart script if enabled
if systemstatus['netconfigenabled']:
    from netconfig import runconfig
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: running boot netconfig', 2, pilib.systemstatusloglevel)
    runconfig(onboot=True)

# Run daemon
from cupiddaemon import rundaemon

rundaemon()

# Update hardware version in table
from systemstatus import readhardwarefileintoversions

readhardwarefileintoversions()

# Run uwsgi daemon if nginx is running
result = ''
result = subprocess.check_output(['service', 'nginx', 'status'])
if result:
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'boot: starting uwsgi based on nginx call', 0)
    subprocess.call(['uwsgi', '--emperor', '/usr/lib/iicontrollibs/wsgi/', '--daemonize', '/var/log/cupid/uwsgi.log'])