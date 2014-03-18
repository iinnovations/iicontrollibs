#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# do this stuff to access stuff in other directories
import os,sys,inspect

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0,top_folder)

import misc.pyiface.iface as pyiface
from cupid.pilib import sqlitemultquery, systemdatadatabase
import subprocess



# Networking check

querylist=[]
table = 'netifaces'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (name text, hwaddr text, address text, ifaceindex integer, bcast text, mask text, flags text)")

allIfaces = pyiface.getIfaces()
for iface in allIfaces:
    querylist.append("insert into " + table + " values ( \'" + iface.name + "\' , \'" + iface.hwaddr + "\' , \'" + iface._Interface__sockaddrToStr(iface.addr) + "\' , \'" +  str(iface.index) + "\' , \'" + iface._Interface__sockaddrToStr(iface.broadaddr) + "\' , \'" +  iface._Interface__sockaddrToStr(iface.netmask) + "\' , \'" +  pyiface.flagsToStr(iface.flags) + "\')")
    #print(querylist)
    sqlitemultquery(systemdatadatabase, querylist)


# Interfaces check
status = subprocess.call(['service', 'hostapd', 'status'])

# Other stuff
