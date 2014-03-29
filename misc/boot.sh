#!/bin/sh -e

# Mount 1wire master

/opt/owfs/bin/owserver --debug -F --i2c=/dev/i2c-1:ALL -p 4304 
/opt/owfs/bin/owfs --debug -F -s 4304 /var/1wire/
/opt/owfs/bin/owhttpd --debug -F -s 4304 -p 4305

# Turn off the lights
printf "turning off lights\n"
/usr/lib/iicontrollibs/cupid/spilights.py

# Run netstart script
printf "running netstart\n"
/usr/lib/iicontrollibs/misc/netrestart.py

exit 0
