#!/usr/bin/env python

# Mount 1wire master

import subprocess
import pilib
import spilights

interfaces = pilib.readalldbrows(pilib.controldatabase,'interfaces')

runi2cowfs = False
runusbowfs = False
for interface in interfaces:
    if interface['interface'] == 'I2C' and type == 'DS2483':
        runi2cowfs = True
    if interface['interface'] == 'USB' and type == 'DS9490':
        runusbowfs = True

    if interface['interface'] == 'SPI1' and type == 'CuPIDlights':
        spilights.updatelightsfromdb(pilib.controldatabase, 'indicators', 1)
    if interface['interface'] == 'SPI0' and type == 'CuPIDlights':
        spilights.updatelightsfromdb(pilib.controldatabase, 'indicators', 0)


if runi2cowfs or runusbowfs:
    if runi2cowfs:
        subprocess.call(['/opt/owfs/bin/owserver', '-F ', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
    if runusbowfs:
        subprocess.call(['/opt/owfs/bin/owserver', '-F ', '-u', '-p', '4304'])

    subprocess.call(['/opt/owfs/bin/owfs', '-F', '-s', '4304', '/var/1wire/'])
    subprocess.call(['/opt/owfs/bin/owhttpd', '-F', '-s', '4304', '-p', '4305'])


# Run netstart script
from netconfig import runconfig
runconfig(onboot=True)
