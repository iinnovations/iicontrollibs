#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# do this stuff to access the pilib for sqlite
import os, sys, inspect
from time import sleep

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

import cupid.netfun as netfun

pingtime = netfun.runping('25.215.49.105')[0]

if ( pingtime > 1000 or pingtime == 0 ):
    from cupid.pilib import gmail
    message = 'Libation is restarting its Hamachi daemon. '
    subject = 'Keeping Hamachi online!'
    email = 'colin.reese@gmail.com'
    actionmail = gmail(message=message, subject=subject, recipient=email)
    actionmail.send()

    netfun.killhamachi()
    netfun.restarthamachi()

