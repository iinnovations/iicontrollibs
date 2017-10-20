#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


from iiutilities import dblib
from iiutilities import datalib

from cupid import pilib
import time

"""
# sessioncontrol.py

This script updates the number of sessions currently
active by deleting expired sessions (those that did
not include a log out) and counting those that are
active. Besides being able to tell who is online at
any given time and from where, this will allow us to
limit the number of sessions per user

"""

# Determine whether this process is enabled:

enabled = dblib.sqlitedatumquery(pilib.dirs.dbs.system, 'select sessioncontrolenabled from \'systemstatus\'')

while enabled:
    #print('enabled')
    polltime = dblib.sqlitedatumquery(pilib.dirs.dbs.session, 'select updatefrequency from \'settings\'')

    # Go through sessions and delete expired ones
    sessions = dblib.readalldbrows(pilib.dirs.dbs.session, 'sessions')
    arrayquery = []
    for session in sessions:
        sessionstart = datalib.timestringtoseconds(session['timecreated'])
        sessionlength = session['sessionlength']
        if time.time() - sessionstart > sessionlength:
            arrayquery.append('delete from sessions where sessionid=\'' + session['sessionid'] + '\'')

    # Delete offensive sessions 
    dblib.sqlitemultquery(pilib.dirs.dbs.session, arrayquery)

    # Reload surviving sessions and summarize
    sessions = dblib.readalldbrows(pilib.dirs.dbs.session, 'sessions')
    sessiondictarray = []
    for session in sessions:
        found = 0
        for dict in sessiondictarray:
            if dict['username'] == session['username']:
                found = 1
                index = sessiondictarray.index(dict)
                dict['sessions'] += 1
                sessiondictarray[index] = dict
        if not found:
            sessiondictarray.append({'username': session['username'], 'sessions': 1})

    # Create sessions table 
    queryarray = []
    queryarray.append('drop table if exists sessionsummary')
    queryarray.append('create table sessionsummary (username text, sessionsactive real)')
    for dict in sessiondictarray:
        queryarray.append(
            'insert into sessionsummary values (\'' + dict['username'] + '\',\'' + str(dict['sessions']) + '\')')
    dblib.sqlitemultquery(pilib.dirs.dbs.session, queryarray)

    polltime = dblib.sqlitedatumquery(pilib.dirs.dbs.session, 'select updatefrequency from \'settings\'')

    time.sleep(polltime)
    enabled = dblib.sqlitedatumquery(pilib.dirs.dbs.system, 'select sessioncontrolenabled from \'systemstatus\'')

