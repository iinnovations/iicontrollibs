#!/usr/bin/python
# Colin Reese
# 08/27/2013 (modification of CuPID Control script)
#  
#
# This script resets the vmscontrol.db database 

import os
import time
from datalib import sqlitemultquery
 

filedir = ""
outputdir = "/var/boatdata/controldata/"

# Create databases entries or leave them empty?    
addentries=True

############################
# vmscontrol.db
############################

rebuild=''
rebuild=raw_input("rebuild vmscontrol.db? (y/N)")

if rebuild=='y':

    database = outputdir + 'vmscontrol.db'

    querylist=[]

    ### Netstatus table

    table='netstatus'
    querylist.append('drop table if exists ' + table)

    # This table is generated on the fly, so no need to create here ad-hoc

    ### SystemStatus table 

    table='systemstatus'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (datapollenabled real default 0, datapollstatus real default 0, datapollfreq real default 15 , lastdatapoll text, adminemail text,systemmessage text)")

    if addentries:
        querylist.append("insert into " + table + " values (1,0,15,'','creese@hyakelectroworks.com','It is a joyous day')")

    ### Boats 

    table='boats'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (name text primary key, enabled real, alias text,hamachiip text, remotesharepath text, localmountpoint text, localsyncpath text, username text, password text, conntype text, connipport text, clientid text, syncstatus real default 0, onlinestatus text, status real default 0, statusmessage text, mounted real, statustime text, lastonlinetime text, lastsynctime text)")

    if addentries:
        querylist.append("insert into " + table + " values ('HYAK22',1,'','','Users/creese/fakedata','/var/boatdata/remotedata/HYAK22','/var/boatdata/localdata/HYAK22','hyakinstall','hyakinstaller','','','','0','0','3','All ok.',0,'','','')")
        querylist.append("insert into " + table + " values ('HYAK09',1,'','','Users/creese/fakedata','/var/remotedata/HYAK09','/var/localdata/HYAK09','hyakinstall','hyakinstaller','','','','0','0','3','All ok.',0,'','','')")


    sqlitemultquery(database,querylist)

##################################
# datamap.db 
##################################

rebuild=''

# This is deprecated. I am leaving it here for table format 
# reference only. Each hull will get its own database.
# An importer will import csv data


#rebuild=raw_input("rebuild datamap.db? (y/N)")

if rebuild=='y':

    database = outputdir + 'datamap.db'

    querylist=[]

    ### No default tables. Create a table as an example 

    table='hull36'
    if addentries:
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " ( IP text,address text,category,description text,value text,datatype text,units text, logpoints real, logfrequency real)")

    sqlitemultquery(database,querylist)

#####################################
# HULLXXcontrol.db
#####################################

rebuild=''

rebuild=raw_input("hullXXcontrol.db? (y/N)")

if rebuild=='y':
    name=raw_input("name?")
    if name:
        querylist=[]
        table='system'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (enabled int, name text,pollfrequency int, lastpoll int,logperiod int)")
        querylist.append("insert into " + table + " values(1,\'" + name + "\',30,0,120)")
    sqlitemultquery(outputdir + name + "control.db",querylist) 
