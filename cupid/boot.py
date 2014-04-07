#!/usr/bin/env python

# Mount 1wire master

import subprocess
subprocess.call(['/opt/owfs/bin/owserver','-F ','--i2c=/dev/i2c-1:ALL','-p','4304'])
subprocess.call(['/opt/owfs/bin/owfs','-F','-s','4304','/var/1wire/'])
subprocess.call(['/opt/owfs/bin/owhttpd','-F','-s','4304','-p','4305'])

# Turn off the lights
# printf "turning off lights\n"
subprocess.call(['/usr/lib/iicontrollibs/cupid/spilights.py'])

# Run netstart script
# printf "running netstart\n"
subprocess.call(['/usr/lib/iicontrollibs/misc/netconfig.py'])

