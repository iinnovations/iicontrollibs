#!/usr/bin/env python

# Mount 1wire master

import subprocess
import pilib
import spilights

interfaces = pilib.readalldbrows(pilib.controldatabase, 'interfaces')
systemstatus = pilib.readonedbrow(pilib.controldatabase, 'systemstatus')[0]


if systemstatus['webserver'] == 'apache':
    subprocess.call(['service', 'apache2', 'start'])
elif systemstatus['webserver'] == 'nginx':
    subprocess.call(['service', 'nginx', 'start'])


runi2cowfs = False
runusbowfs = False
for interface in interfaces:
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
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
        except:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'error running i2c owserver', 1, pilib.systemstatusloglevel)
    if runusbowfs:
        try:
            subprocess.call(['/opt/owfs/bin/owserver', '-F', '-u', '-p', '4304'])
        except:
            pilib.writedatedlogmsg(pilib.systemstatuslog, 'error running usb owserver', 1, pilib.systemstatusloglevel)
    try:
        subprocess.call(['/opt/owfs/bin/owfs', '-F', '-s', '4304', '/var/1wire/'])
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'error running owfs', 1, pilib.systemstatusloglevel)

    try:
        subprocess.call(['/opt/owfs/bin/owhttpd', '-F', '-s', '4304', '-p', '4305'])
    except:
        pilib.writedatedlogmsg(pilib.systemstatuslog, 'error running owhttpd', 1, pilib.systemstatusloglevel)


# Run netstart script if enabled
if systemstatus['netconfigenabled']:
    from netconfig import runconfig

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
    pilib.writedatedlogmsg(pilib.systemstatuslog, 'Starting uwsgi based on nginx call', 0)
    subprocess.call(['uwsgi', '--emperor', '/usr/lib/iicontrollibs/wsgi/', '--daemonize', '/var/log/cupid/uwsgi.log'])