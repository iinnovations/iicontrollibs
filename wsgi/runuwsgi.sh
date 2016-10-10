#!/bin/bash

pkill uwsgi
uwsg --emperor /usr/lib/iicontrollibs/wsgi/ --daemonize /var/log/cupid/uwsgi.log