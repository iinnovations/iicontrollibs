#!/bin/sh -e

# Mount 1wire master

/opt/owfs/bin/owserver -F --i2c=/dev/i2c-1:ALL -p 4304 
/opt/owfs/bin/owfs -F -s 4304 /var/1wire/
/opt/owfs/bin/owhttpd -F -s 4304 -p 4305

# Turn off the lights
printf "turning off lights\n"
/usr/lib/iicontrollibs/cupid/turnoffthelights.py

# Run netstart script
printf "running netstart\n"
/usr/lib/iicontrollibs/misc/netrestart.py

exit 0
