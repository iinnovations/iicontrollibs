#!/usr/bin/python
#
# Colin Reese
# August 28, 2013
#
# Datamanager.py
# This is the standalone updater for network status
# data synchronization, and other hygienic functions

import os
from subprocess import Popen
from time import sleep

import datalib
from iiutilities import netfun

dirs.dbs.control = '/var/boatdata/controldata/vmscontrol.db'
boatstablename= 'boats'
systemstablename = 'systemstatus'

datapollenabled = datalib.sqlitesinglevaluequery(dirs.dbs.control,systemstablename,'datapollenabled')
datapollfreq = datalib.sqlitesinglevaluequery(dirs.dbs.control,systemstablename,'datapollfreq')

while datapollenabled:
    # get a dictarray of the hamachi data and autogenerate a table
    hamachidata = netfun.gethamachidata()
   
    datalib.dropcreatetexttablefromdict(dirs.dbs.control,'netstatus',hamachidata)

    # synchronize netstatus and boats tables
    datalib.synctablesbyname(dirs.dbs.control,'netstatus',boatstablename,['clientid','connipport','conntype','hamachiip','alias','onlinestatus'])
    datalib.sqlitequery(dirs.dbs.control,'update \"' + boatstablename + '\" set statustime=\"' + datalib.gettimestring() + '\"')
    #print('updating status of ' + boatstablename)

    # mount all online shares if we're supposed to 
    boatdata = datalib.dynamicsqliteread(dirs.dbs.control,boatstablename)

    for boatdict in boatdata:
         
        # create path

        sharepath="//" + boatdict['hamachiip'] + "/" + boatdict['remotesharepath'].replace("\\","/")

        # check if mounted

        #print(sharepath)
        mountstatus = netfun.checksharemount(sharepath)
        if mountstatus:
            #print(' mounted')
            pass
        else: 
            #print(' not mounted')
            if boatdict['enabled'] and boatdict['onlinestatus']=='online':

                # Attempt to mount and then recheck
                #print('attempting to mount ' + sharepath + ' to ' + boatdict['localmountpoint'])
                os.system('mount -t cifs -o username=' + boatdict['username'] + ',password=' + boatdict['password'] + ' ' + sharepath + ' ' +  boatdict['localmountpoint'])
                
                mountstatus = netfun.checksharemount(sharepath)

        # Set mounted status in table
        datalib.sqlitequery(dirs.dbs.control,'update \"' + boatstablename + '\" set mounted=' + str(int(mountstatus)) + ' where name=\"' + boatdict['name'] + '\"')
    
        # Set last online time if online
        if mountstatus:
            datalib.sqlitequery(dirs.dbs.control,'update \"' + boatstablename + '\" set lastonlinetime=\"' + datalib.gettimestring() + '\" where name=\"' + boatdict['name'] + '\"')
	    
            # perform data sync operation on data folder, but not datamap folder. This will likely be conditional at some point to limit data rate
            print('syncing')
           
            print('-aP --log-file=/var/log/rsync ' + boatdict['localmountpoint'] + ' ' + boatdict['localsyncpath'] + '/data/')
            Popen(['rsync','-aP','--log-file=/var/log/rsync',boatdict['localmountpoint'] + 'data/',boatdict['localsyncpath'] + '/data/'])
           
            # Set last sync time in log
            datalib.sqlitequery(dirs.dbs.control,'update \"' + boatstablename + '\" set lastsynctime=\"' + datalib.gettimestring() + '\" where name=\"' + boatdict['name'] + '\"')




    # process alerts and/or summary report for online statuses


    # refresh these so that if they change while the daemon is running
    # they will be reflected accordingly
    datapollenabled = datalib.sqlitesinglevaluequery(dirs.dbs.control,systemstablename,'datapollenabled')
    datapollfreq = datalib.sqlitesinglevaluequery(dirs.dbs.control,systemstablename,'datapollfreq')

    sleep(datapollfreq)
