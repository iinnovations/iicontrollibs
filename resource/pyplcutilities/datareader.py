#!/usr/bin/python
# datareader.py
#
# Colin Reese
# September 3, 2013
#
# This script lives on a boat. It does the following:
# 1. Reads the local datamap to see what should be read
# 2. Checks the datalog database to see if proper tables exist
# 3. Determines whether it is time to read the variables
# 4. Reads the data that needs to be read
# 5. Inserts records with the read data
# 6. Sleeps until next read


import time
import os
import subprocess

import datalib
import netfun


def readdata():
    try:
        controldict = datalib.readonedbrow(datalib.controldatabase, 'system', 0)[0]
    except:
        if datalib.datareaderloglevel > 0:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Error reading from ' + datalib.controldatabase + ". ")
        return

    try:
        datamap = datalib.readalldbrows(datalib.datamapdatabase, 'datamap')
    except:
        if datalib.datareaderloglevel > 0:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Error reading from ' + datalib.datamapdatabase + ". ")
        return

    if datalib.datareaderloglevel > 1:
        try:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, controldict['name'])
        except:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'No name present. ')

    # If enabled, run sequence

    while controldict['enabled']:

        currenttimestring = datalib.gettimestring()
        currenttime = datalib.timestringtotimestruct(currenttimestring)

        controldict = datalib.readonedbrow(datalib.controldatabase, 'system', 0)[0]

        # Get datamap
        datamap = datalib.readalldbrows(datalib.datamapdatabase, 'datamap')

        # Filter datamap for items that should be read (by enabled status and timestamp)
        readydatamap = datalib.datamapreadyfilter(datamap)

        # Block up reads of items to be read
        blockeddatamap = datalib.datamaptoblockreads(readydatamap)

        print(blockeddatamap)

        # Create hard-coded datalogname
        # Find if database file exist

        if os.path.isfile(datalib.datalogdatabase):  # This is not properly pythonic
            if datalib.datareaderloglevel > 1:
                datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                         'Log file ' + datalib.datareaderlogfile + ' exists. ')

            # check to see if log exists and isn't too old
            try:
                logcreatedtimestring = datalib.sqlitedatumquery(datalib.datalogdatabase,
                                                                "select \"timecreated\" from metadata")
                logcreatedtime = datalib.timestringtotimestruct(logcreatedtimestring)
                archivedb = False
            except:
                if datalib.datareaderloglevel > 0:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Error retrieving metadata. ')

                    # The database is probably malformed, but we save it anyway, just in case
                    archivedb = True
            else:
                if (currenttime - logcreatedtime).total_seconds() > controldict['logperiod']:
                    archivedb = True
                    if datalib.datareaderloglevel > 3:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                 'Archiving, based on comparison of currenttime' + currenttimestring + ' to logcreatedtime ' + logcreatedtimestring)
                        datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                 'Logperiod is ' + str(controldict['logperiod']) + '. Diff is ' + str(
                                                     (currenttime - logcreatedtime).total_seconds))
                else:
                    archivedb = False

            # archive log
            if archivedb:
                archivelogname = datalib.datalogdatabase.replace('.db', '') + '_' + currenttimestring.replace(' ',
                                                                                                              '_') + '.db'

                if datalib.datareaderloglevel > 1:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                             'Log file ' + datalib.datareaderlogfile + ' will be archived to ' + archivelogname + '. ')

                subprocess.call(['cp', datalib.datalogdatabase, archivelogname])
                initialize = True
            else:
                initialize = False
                datalib.sqlitequery(datalib.datalogdatabase,
                                    "update metadata set \"timelastaccessed\"='" + currenttimestring + "'")

            # print(
            #     'logcreated: ' + logcreatedtimestring + ' currenttime: ' + currenttimestring + ' initialize: ' + str(
            #         initialize))

        else:
            initialize = True

        if initialize:
            # initialize log
            querylist = []
            open(datalib.datalogdatabase, 'w').close()
            if datalib.datareaderloglevel > 0:
                datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Created loggy log ' + datalib.datalogdatabase)

            # Initialize created and accessed data
            querylist = []
            querylist.append('create table metadata (timecreated text, timelastaccessed text)')
            querylist.append("insert into metadata values('" + currenttimestring + "','" + currenttimestring + "')")
            datalib.sqlitemultquery(datalib.datalogdatabase, querylist)

        # For each item in datamap
        for item in blockeddatamap:
            # Hard-code table format, at least for now. We put this here to give handy error message details
            if item['inputtype'] in ['MBTCP']:
                try:
                    readlogtablename = item['datacategory']
                    for i in range(1, 4):
                        if item['datadescription' + str(i)]:
                            readlogtablename += '_' + item['datadescription' + str(i)]
                except KeyError:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Error category and name from data item in MBTCP')
                    continue
                else:
                    if datalib.datareaderloglevel > 3:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Processing MBTCP: ' + readlogtablename)
            elif item['inputtype'] in ['MBTCPblock']:
                try:
                    readlogtablename = 'MBTCPblock_' + item['ipaddress'] + '_' + str(item['start'])
                except KeyError:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Error category and name from data item in MBTCPblock')
                    continue
                else:
                    if datalib.datareaderloglevel > 3:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Processing MBTCPblock: ' + readlogtablename)

            # Read


            # We're going to separate read and log functions
            # Read everything, publish to datamap, and then iterate over map to put into log

            if item['inputtype'] == 'MBTCP':
                # Set last read attempt
                datalib.setsinglevalue(datalib.datamapdatabase, 'datamap', 'lastreadattempt', currenttimestring,
                                   "\"index\"='" + str(item['index']) + "'")

                IPAddy = item['inputid1']
                MBAddress = item['inputid2']
                datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                         'Reading: MBTCPIP : IPAddress: ' + IPAddy + ', MBAddress: ' + MBAddress + readlogtablename)

                readresult = netfun.readMBcodedaddresses(IPAddy, MBAddress, 1)

                # See if contained readresult contains data. If it is an exception response, it will be a dict
                # with items message and statuscode, but will throw an exception on attempt to read
                # an indexed entry

                try:
                    dataresult = readresult[0]
                except:
                    readstatus = 0
                    if datalib.datareaderloglevel > 0:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile, 'MBTCP Exception')
                        try:
                            datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                     dataresult['message'] + str(dataresult['statuscode']))
                        except:
                            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'unknown error format')
                    if datalib.datareaderloglevel > 1:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                 'Unsuccessful read of item ' + itemlogtablename)
                else:
                    readstatus = 1
                    # Update current values in table
                    querylist = []
                    querylist.append(datalib.makesinglevaluequery('datamap', 'readvalue', dataresult,
                                                                  "\"index\"='" + item['index'] + "'"))
                    querylist.append(datalib.makesinglevaluequery('datamap', 'valuereadtime', currenttimestring,
                                                                  "\"index\"='" + item['index'] + "'"))
                    try:
                        datalib.sqlitemultquery(datalib.datamapdatabase, querylist)
                    except:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                 'Error in sqlitequery: ' + ','.join(querylist))

                # Set readstatus
                datalib.setsinglevalue(datalib.datamapdatabase, 'datamap', 'readstatus', readstatus,
                                               "\"index\"='" + str(item['index']) + "'")
                if readstatus:
                     if datalib.datareaderloglevel > 3:
                            datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                     'Successfully read item ' + readlogtablename + ': ' + str(
                                                         dataresult))
                            datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                     'publish result: ' + str(dataresult))

            elif item['inputtype'] == 'MBTCPblock':
                IPAddy = item['ipaddress']
                startregister = item['start']
                readlength = item['length']

                # Set last read attempt
                for index in item['indices']:
                    datalib.setsinglevalue(datalib.datamapdatabase, 'datamap', 'lastreadattempt', currenttimestring,
                                   "\"index\"='" + str(index) + "'")

                readresult = netfun.readMBcodedaddresses(IPAddy, startregister, readlength)
                querylist = []
                try:
                    dataresults = readresult
                except:
                    readstatus = 0
                    querylist.append(datalib.sqlitemakesetvaluequery('datamap', 'readstatus', readstatus,
                                                       "\"index\"='" + str(item['index']) + "'"))
                    querylist.append(datalib.sqlitemakesetvaluequery('datamap', 'lastreadfail', currenttimestring,
                               "\"index\"='" + str(item['index']) + "'"))

                    if datalib.datareaderloglevel > 0:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile, 'MBTCP Exception')
                        try:
                            datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                     dataresult['message'] + str(dataresult['statuscode']))
                        except:
                            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'unknown error format')

                    if datalib.datareaderloglevel > 1:
                        datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                                 'Unsuccessful read of item ' + readlogtablename)

                else:
                    readstatus = 1
                    # Update current values in table

                    for dataresult, index in zip(dataresults, item['indices']):
                        querylist.append(datalib.makesinglevaluequery('datamap', 'readvalue', dataresult,
                                                                      "\"index\"='" + str(index) + "'"))
                        querylist.append(datalib.makesinglevaluequery('datamap', 'valuereadtime', currenttimestring,
                                                                      "\"index\"='" + str(index) + "'"))
                        # Set readstatus
                        querylist.append(datalib.sqlitemakesetvaluequery('datamap', 'readstatus', readstatus,
                                                       "\"index\"='" + str(index) + "'"))
                        querylist.append(datalib.sqlitemakesetvaluequery('datamap', 'lastreadfail', currenttimestring,
                               "\"index\"='" + str(index) + "'"))

                try:
                    datalib.sqlitemultquery(datalib.datamapdatabase, querylist)
                except:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                             'Error in sqlitequery: ' + ','.join(querylist))
            else:
                readstatus = 0

            if readstatus:
                if datalib.datareaderloglevel > 3:
                    datalib.writedatedlogmsg(datalib.datareaderlogfile,
                                             'Successfully read item ' + readlogtablename + ': ' + str(
                                                 dataresult))

        # updatelogs()
        time.sleep(int(controldict['pollfrequency']))

    print('exiting gracefully, presumable due to logging not being enabled')

def updatelogs():
    datamap = datalib.readalldbrows(datalib.datamapdatabase, 'datamap')

    for item in datamap:

        # Make sure we have a valid piece of data
        if not item['value']:
            continue

        # Check to see if a log exists.
        # If yes, get last time and check to see if we should log
        # If no, automatically create log and add to it
        itemlogtablename = item['datacategory']
        for i in range(1, 4):
            if item['datadescription' + str(i)]:
                itemlogtablename += '_' + item['datadescription' + str(i)]

        valuetimestring = item['valuereadtime']
        valuetime = datalib.timestringtotimestruct(valuetimestring)

        # Find if log table exists
        if datalib.doestableexist(datalib.datalogdatabase, itemlogtablename):

            # Get last time read from datalog
            lasttimestring = datalib.sqlitedatumquery(datalib.datalogdatabase,
                                        "select \"time\" from '" + itemlogtablename + "' order by 'time' desc limit 1")

        else:
            # Create table in datalog
            datalib.sqlitequery(datalib.datalogdatabase,
                                'create table \"' + itemlogtablename + '\"(time text primary key, value text)')

            if datalib.datareaderloglevel > 3:
                datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Creating table : ' + itemlogtablename)

            # Set to zero to ensure read
            lastlogtimestring = ''

    lastlogtime = datalib.timestringtotimestruct(lastlogtimestring)

    # Enter into log if it's time
    if not lastlogtimestring or (valuetime - lastlogtime).total_seconds() > int(
            item['logfrequency']):
        if datalib.datareaderloglevel > 2:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Logging data datalog')
        datalib.sqliteinsertsingle(datalib.datalogdatabase, itemlogtablename, valuetimestring, item['readvalue'])
    else:
        if datalib.datareaderloglevel > 3:
            datalib.writedatedlogmsg(datalib.datareaderlogfile, 'Not logging')

    # Log result of read in readstatusdatabase

    # See if table exists and create if not
    if not datalib.doestableexist(datalib.readstatusdatabase, itemlogtablename):
        datalib.sqlitequery(datalib.readstatusdatabase,
                        'create table \"' + itemlogtablename + '\" (time text primary key, readstatus boolean, valueiszero boolean)')
    datalib.sqliteinsertsingle(datalib.readstatusdatabase, itemlogtablename, [currenttimestring, str(int(publishresult)), str(int(dataiszero))])

    # Size readstatus log
    datalib.sizesqlitetable(datalib.readstatusdatabase, itemlogtablename, datalib.readstatusentries)

    # Refresh metadata
    if not datalib.doestableexist(datalib.readstatusdatabase, 'metadata'):
        datalib.sqlitequery(datalib.readstatusdatabase,
                        'create table \"metadata\" (item text primary key, failfraction real, zerofraction real)')

    readstatusdata = datalib.readalldbrows(datalib.readstatusdatabase, itemlogtablename)
    datalength = len(readstatusdata)
    zerosum = 0
    failsum = 0
    for row in readstatusdata:
        zerosum += row['readstatus']
        failsum += row['valueiszero']
    zerofraction = 1 - zerosum / float(datalength)
    failfraction = failsum / float(datalength)

    try:
        datalib.sqliteinsertsingle(datalib.readstatusdatabase, 'metadata', [itemlogtablename, failfraction, zerofraction])
    except:
        print('bad stuff. i should log this.')


    # If we are in auto mode, set logpoints to retain enough points so
    # a complete archive period's worth. In other words, if we archive
    # every day, we need to save a day's worth of points

    # if item['logpoints'] == 'auto':
    #     logpoints = ceil(datalib.logperiod / item['logfrequency'])
    # else:
    #     logpoints = item['logpoints']
    # currlogpoints = datalib.getlogsize(datalib.datalogdatabase, itemlogtablename)

    # Size log whether or not we added to it
    # This is disabled, but the log is being rotated. We need to sync the rotation

    # datalib.sizesqlitetable(datalib.datalogdatabase, itemlogtablename, logpoints)
    # currlogpoints = datalib.getlogsize(datalib.datalogdatabase, itemlogtablename)
    # datalib.sqlitesetvalue(datalib.datamapdatabase, 'datamap', 'currlogpoints', str(currlogpoints),
    #                        'index=' + str(item['index']))

        # rotate logs
        datalib.rotatelogs(datalib.datareaderlogfile, datalib.maxnumlogs, datalib.maxlogsize)

if __name__ == '__main__':
    print('running readalldata')
    readdata()