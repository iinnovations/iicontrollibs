#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# sessioncontrol.py

# Colin Reese
# 9/9/2013

# This script updates the number of sessions currently
# active by deleting expired sessions (those that did
# not include a log out) and counting those that are
# active. Besides being able to tell who is online at
# any given time and from where, this will allow us to
# limit the number of sessions per user

import pilib
import time

# Determine whether this process is enabled:

enabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select sessioncontrolenabled from \'systemstatus\'')

while enabled:
    #print('enabled')
    polltime = pilib.sqlitedatumquery(pilib.sessiondatabase, 'select updatefrequency from \'settings\'')

    # Go through sessions and delete expired ones
    sessions = pilib.readalldbrows(pilib.sessiondatabase, 'sessions')
    arrayquery = []
    for session in sessions:
        sessionstart = pilib.timestringtoseconds(session['timecreated'])
        sessionlength = session['sessionlength']
        if time.time() - sessionstart > sessionlength:
            arrayquery.append('delete from sessions where sessionid=\'' + session['sessionid'] + '\'')

    # Delete offensive sessions 
    pilib.sqlitemultquery(pilib.sessiondatabase, arrayquery)

    # Reload surviving sessions and summarize
    sessions = pilib.readalldbrows(pilib.sessiondatabase, 'sessions')
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
    pilib.sqlitemultquery(pilib.sessiondatabase, queryarray)

    polltime = pilib.sqlitedatumquery(pilib.sessiondatabase, 'select updatefrequency from \'settings\'')

    time.sleep(polltime)
    enabled = pilib.sqlitedatumquery(pilib.controldatabase, 'select sessioncontrolenabled from \'systemstatus\'')

