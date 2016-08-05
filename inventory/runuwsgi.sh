#!/bin/bash

pkill uwsgi
uwsgi --emperor /usr/lib/iicontrollibs/inventory/ --daemonize /var/log/uwsgi.log