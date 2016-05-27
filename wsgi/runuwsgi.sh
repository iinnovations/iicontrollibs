#!/bin/bash

echo "Kill all existing uwsgi processes"
killall uwsgi
echo "Starting uwsgi ... "
uwsgi --emperor /usr/lib/iicontrollibs/wsgi/ --daemonize /var/log/cupid/uwsgi.log
echo "all done!"
