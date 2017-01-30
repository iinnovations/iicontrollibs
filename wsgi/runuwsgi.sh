#!/bin/bash

pkill uwsgi
uwsgi --emperor /usr/lib/iicontrollibs/wsgi/ --daemonize /var/log/cupid/uwsgi.log
