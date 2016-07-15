#!/bin/bash

uwsgi --emperor /usr/lib/iicontrollibs/inventory/ --daemonize /var/log/uwsgi.log
