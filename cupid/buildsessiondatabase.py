#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


import os
import time
from pilib import sqlitemultquery
 

filedir = ""
outputdir = "/var/www/data/"
databasename = 'authlog.db'
database=outputdir+databasename

querylist=[]

### Session limits 

table='sessionlimits'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (username text primary key, sessionsallowed real default 5 )")

querylist.append("insert into " + table + " values ('viewer', 5)")
querylist.append("insert into " + table + " values ('controller', 5)")
querylist.append("insert into " + table + " values ('administrator', 5)")
querylist.append("insert into " + table + " values ('colin', 3)")

### Settings table 

table='settings'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (sessionlength real default 600, sessionlimitsenabled real default 1, updatefrequency real)")

querylist.append("insert into " + table + " values (600,1,30)")

### Session table 

table='sessions'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (username text, sessionid text, sessionlength real, timecreated text, apparentIP text , realIP text)")

### Sessions summary

table='sessionsummary'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (username text,  sessionsactive real)")

querylist.append("insert into " + table + " values ('viewer', 0)")
querylist.append("insert into " + table + " values ('controller', 0)")
querylist.append("insert into " + table + " values ('administrator', 0)")

### Session log

table='sessionlog'
querylist.append('drop table if exists ' + table)
querylist.append("create table " + table + " (username text, sessionid text, time text, action text, apparentIP text, realIP text)")


#print(querylist)
sqlitemultquery(database,querylist)
