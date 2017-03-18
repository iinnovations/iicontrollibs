#!/usr/bin/python
# datalib.py
# This library is the master function and global library

###########################################
# Define globals
from iiutilities import netfun

dataroot = '/var/boatdata/'
procdirs.log = '/var/log/vmslogger/'
controldir = dataroot + 'controldata/'
datadirs.log = dataroot + 'logdata/'

readstatus = True
readstatuspoints = 100

try:
    filename = controldir + 'boatname.txt'
    with open(filename) as file:
        boatname = file.readline().rstrip()
except:
    print('Read of boatname failed. Aborting.')
    exit()

datareaderlogfile = procdirs.log + boatname + 'datareader.log'
datareaderloglevel = 4
maxlogsize = 100000
maxnumlogs = 10

logperiod = 24 * 60 * 60  # Seconds in log for rollover

dirs.dbs.control = controldir + boatname + 'control.db'
datamapdatabase = controldir + boatname + 'datamap.db'
datadirs.dbs.log = datadirs.log + boatname + 'datalog.db'
readstatusdatabase = datadirs.log + boatname + 'readstatus.db'

readstatusentries = 20

systemstablename = 'systemstatus'

###########################################
# Raw file functions
###########################################

def csvfiletoarray(filename):
    import csv

    with open(filename, 'rU') as csvfile:
        data = csv.reader(csvfile, delimiter=',')
        array = []
        for row in data:
            array.append(row)
    return array


def datawithheaderstodictarray(dataarray, headerrows=1):
    # we assume the first row is full of dict keys

    dictarray = []
    for i in range(headerrows, len(dataarray)):
        dict = {}
        for j in range(0, len(dataarray[0])):
            dict[dataarray[0][j]] = dataarray[i][j]
        dictarray.append(dict)

    return dictarray


# This is a function to take a csv data map file, e.g. HYAK22datamab.csv
# and a system file, e.g. HYAK22system.csv and use them to create databases. 
# The datalogging script datareader.py may then do as it sees fit with it

def csvdatamaptodatabase(dirs.outputectory, csvdatamapfilename):
    name = raw_input('And what, pray tell, is the name of your vessel, good sir? ')

    # Read csv datamap file
    datamapdictarray = datawithheaderstodictarray(csvfiletoarray(csvdatamapfilename), 1)

    # Make datamap database
    datamapdbname = name + 'datamap.db'

    datamapdbpath = dirs.outputectory + '/' + datamapdbname
    # (re)Create the datamap
    dropcreatetexttablefromdict(datamapdbpath, 'datamap', datamapdictarray)


# this particular function is deprecated, but i'm leaving it here until the
# entire structure is complete. We used to take the datamap and control 
# information and put it all in one file. Since, we've separated these into
# two separate files, HULLXXdatamap.db and HULLXXcontrol.db. So we don't need # to jam them into the same database

def csvcontroltemplatefiletodirs.dbs.control(csvsystemfilename, csvdatamapfilename):
    ############################
    ##############deprecated
    ###########################

    import os

    from datalib import dropcreatetexttablefromdict
    # Read csv system file
    csvsystemdict = datawithheaderstodictarray(csvfiletoarray(csvsystemfilename))

    # Read csv datamap file
    datamapdictarray = datawithheaderstodictarray(csvfiletoarray(csvdatamapfilename))

    # Make dirs.dbs.control
    controldbname = csvsystemdict[0]['name'] + 'control.db'
    directory = os.path.dirname(csvsystemfilename)
    controldbpath = directory + '/' + controldbname
    # (re)Create the datamap
    dropcreatetexttablefromdict(controldbpath, 'datamap', datamapdictarray)
    dropcreatetexttablefromdict(controldbpath, 'system', csvsystemdict)


########################################
# This is a way to upload data and create a log database from a csv file

def csvdatatodirs.dbs.log(csvfile, databasefile):
    # Read csv file into array
    alldata = csvfiletoarray(csvfile)

    querylist = []
    # Read array into database
    # For each table
    for i in range(len(alldata) / 2):
        dict = {}
        tablename = alldata[i * 2][0]
        print(tablename)
        times = alldata[i * 2][2:]
        values = alldata[i * 2 + 1][2:]
        querylist.append('drop table if exists \"' + tablename + '\"')
        querylist.append('create table \"' + tablename + '\" (time text, value text)')
        #for each time value pair
        for time, value in zip(times, values):
            querylist.append(
                'INSERT into \"' + tablename + '\" (time, value) VALUES (\"' + time + '\",\"' + value + '\")')
    print(querylist)
    sqlitemultquery(databasefile, querylist)
    #return alldata


#############################################
## Utility Functions
#############################################

class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def gettimestring(datetimestruct=None):
    from datetime import datetime

    if datetimestruct:
        try:
            timestring = datetimestruct.strftime("%Y-%m-%d %H:%M:%S")
        except TypeError:
            timestring = ''
    else:
        datetimestruct = datetime.utcnow()
        timestring = datetimestruct.strftime("%Y-%m-%d %H:%M:%S")
    return timestring


def timestringtotimestruct(timestring=None):
    from datetime import datetime

    if timestring:
        try:
            timestruct = datetime.strptime(timestring, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestruct = datetime.utcnow()
    else:
        timestruct = datetime.utcnow()
    return timestruct


def writedatedlogmsg(logfile, message):
    logfile = open(logfile, 'a')
    logfile.writelines([gettimestring() + ' : ' + message + '\n'])
    logfile.close()


def rotatelogs(logname, numlogs, logsize):
    import os

    returnmessage = ''
    logmessage = ''
    try:
        currlogsize = os.path.getsize(logname)
    except:
        logmessage = 'Error sizing original log'
        returnmessage = logmessage
        statuscode = 1
    else:
        statuscode = 0
        if currlogsize > logsize:
            for i in range(numlogs - 1):
                oldlog = logname + '.' + str(numlogs - i - 2)
                newlog = logname + '.' + str(numlogs - i - 1)
                try:
                    os.rename(oldlog, newlog)
                except:
                    logmessage += 'file error. log ' + oldlog + ' does not exist?\n'

            try:
                os.rename(logname, logname + '.1')
            except:
                logmessage += 'original doesn\'t exist\?\n'
                returnmessage = "error in "
        else:
            logmessage += 'log not big enough\n'
            returnmessage = 'logs not rotated'
    return {'message': returnmessage, 'logmessage': logmessage, 'statuscode': 0}

def datamaptoblockreads(datamap):
    # This takes raw entries in the datamap and converts them into blockreads, special dictionaries that
    # tell datareader what to read and where to put it.

    maxwordblocksize = 24
    maxbitblocksize = 1024

    # We manipulate the datamap. We leave some stuff alone and block/manipulate other stuff.
    # First, we are going to block together the MB reads

    editedmap = []
    mapkeys = []
    for item in datamap:
        # Device a unique key for each readtype
        if item['inputtype'] == 'MBTCP':
            # For MB, this is IP address
            # We'll process types later
            mapkey = item['inputid1']
            if mapkey in mapkeys:
                dictindex = mapkeys.index(mapkey)

                # inputid2 is the MB address
                editedmap[dictindex]['addresses'].append(item['inputid2'])
                editedmap[dictindex]['indices'].append(item['index'])

            else:
                editedmap.append({'inputtype':'MBTCPblock','ipaddress':item['inputid1'],'addresses':[item['inputid2']],'indices':[item['index']]})
                mapkeys.append(mapkey)
        else:
            mapkey = item['inputid1'] + '_' + item['inputid2'] + '_' + item['inputid3']
            if mapkey in mapkeys:
                pass
            else:
                editedmap.append(item)
                mapkeys.append(mapkey)

    returnmap = []
    for item in editedmap:
        if item['inputtype'] == 'MBTCPblock':
            # Reorder MB addresses by number
            intaddresses = map(int, item['addresses'])
            sortedaddresses, sortedindices = zip(*sorted(zip(intaddresses,item['indices'])))

            print(sortedaddresses)
            print(sortedindices)
            newitems = []
            newitem = {}
            for address, index in zip(sortedaddresses, sortedindices):
                # If there isn't a new item, add one
                if not newitem:
                    newitem = {'inputtype':'MBTCPblock','ipaddress':item['ipaddress'],'addresses':[address],'indices':[index],'start':address,'length':1}

                # We check to see if we can just add to the existing item
                else:

                    FC = netfun.MBFCfromaddress(address)
                    lastFC = netfun.MBFCfromaddress(newitem['addresses'][len(newitem['addresses']) - 1])
                    if FC in [0,1]:
                        maxsize = maxbitblocksize
                    elif FC in [3,4]:
                        maxsize = maxwordblocksize
                    else:
                        print('ERROR')

                    # Are we in the same memory block type?
                    if FC != lastFC:
                        startnewitem = True

                    # Are within the max range?
                    elif address - newitem['addresses'][0] > maxsize:
                        startnewitem = True
                    else:
                        startnewitem = False

                    # If we can add to the existing item, do it.
                    if not startnewitem:
                        newitem['addresses'].append(address)
                        newitem['indices'].append(index)
                        newitem['length'] = address - newitem['addresses'][0] + 1
                    # Otherwise, add to newitems and start another
                    else:
                        newitems.append(newitem)
                        newitem = {'inputtype':'MBTCPblock','ipaddress':item['ipaddress'],'addresses':[address],'indices':[index],'start':address,'length':1}
            returnmap.extend(newitems)
        else:
            returnmap.append(item)

    return returnmap

def datamapreadyfilter(datamap):
    returnmap = []
    currenttimestring = gettimestring()
    currenttime = timestringtotimestruct(currenttimestring)

    for item in datamap:
        if item['enabled']:
            lastreadtime = timestringtotimestruct(item['valuereadtime'])
            # print(currenttime)
            # print(lastreadtime)
            # print((currenttime - lastreadtime).total_seconds())
            # print(item['pollfrequency'])
            if not item['valuereadtime'] or (currenttime - lastreadtime).total_seconds() > float(item['pollfrequency']):
                print('appending')
                returnmap.append(item)

    return returnmap

#############################################
## Sqlite Functions
#############################################

def doestableexist(database, tablename):
    result = sqlitedatumquery(database,
                              'select \"' + tablename + '\" FROM sqlite_master WHERE type=\'table\' AND name=\"' + tablename + '\"')
    if result == '':
        exists = False
    else:
        exists = True
    return exists


def getpragma(database, table):
    pragma = sqlitequery(database, 'pragma table_info ( \'' + table + '\')')
    return pragma


def getpragmanames(database, table):
    pragma = getpragma(database, table)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item[1])
    return pragmanames


def datarowtodict(database, table, datarow):
    pragma = getpragma(database, table)
    #print(pragma)

    pragmanames = []
    for item in pragma:
        pragmanames.append(item[1])

    dict = {}
    index = 0
    for datum in datarow:
        dict[pragmanames[index]] = datum
        index += 1
    return dict


def makesqliteinsert(table, valuelist, valuenames=None, replace=True):
    if replace:
        query = 'insert or replace into '
    else:
        query = 'insert into '
    query += '\'' + table + '\''

    if valuenames:
        query += ' ('
        for valuename in valuenames:
            query += '\'' + str(valuename) + '\','
        query = query[:-1] + ')'

    query += ' values ('

    for value in valuelist:
        query += '\'' + str(value) + '\','
    query = query[:-1] + ')'
    return query

def sqliteinsertsingle(database, table, valuelist, valuenames=None, replace=True):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    with con:
        cur = con.cursor()
        query = makesqliteinsert(table, valuelist, valuenames, replace)
        cur.execute(query)


def sqlitemultquery(database, querylist):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    with con:
        cur = con.cursor()
        data = []
        for query in querylist:
            cur.execute(query)
            dataitem = cur.fetchall()
            data.append(dataitem)
        con.commit()

    return data


# This returns a 2D list
def sqlitequery(database, query):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    with con:
        cur = con.cursor()
        cur.execute(query)

        data = cur.fetchall()

    return data


# This returns a single value

def sqlitedatumquery(database, query):
    datarow = sqlitequery(database, query)
    if datarow:
        datum = datarow[0][0]
    else:
        datum = ''
    return datum


def sqlitesetvalue(database, table, valuename, stringvalue, condition=None):
    query = sqlitemakesetvaluequery(table, valuename, stringvalue, condition=None)
    sqlitequery(database, query)


def sqlitemakesetvaluequery(table, valuename, stringvalue, condition=None):
    if condition:
        query = "update '" + table + "' set '" + valuename + "'='" + stringvalue + "' where " + condition
    else:
        query = "update '" + table + "' set '" + valuename + "'='" + stringvalue + "'"
    return query


# This returns the first value without a structured query,
# so only really works for single row tables

def sqlitesinglevaluequery(database, table, valuename):
    query = 'select \"' + valuename + '\" from \"' + table + '\"'
    # print(query)
    datarow = sqlitequery(database, query)
    if datarow:
        value = datarow[0][0]
    else:
        value = ''
    return value


def setsinglevalue(database, table, valuename, value, condition=None):
    query = makesinglevaluequery(table, valuename, value, condition)
    # print(query)
    response = sqlitequery(database, query)
    return response


def makesinglevaluequery(table, valuename, value, condition=None):
    query = 'update ' + "'" + table + "' set \"" + valuename + "\"='" + str(value) + "'"
    if condition:
        query += ' where ' + condition
    return query


def readonedbrow(database, table, rownumber):
    data = sqlitequery(database, 'select * from \"' + table + '\"')
    datarow = data[rownumber]

    dict = datarowtodict(database, table, datarow)
    dictarray = [dict]

    return dictarray


def readsomedbrows(database, table, start, length):
    data = sqlitequery(database, 'select * from \'' + table + '\'')
    datarows = data[int(start):int(start + length)]
    pragmanames = getpragmanames(database, table)

    dictarray = []
    for row in datarows:
        dict = {}
        index = 0
        for datum in row:
            dict[pragmanames[index]] = datum
            index += 1
        dictarray.append(dict)

    return dictarray


def readalldbrows(database, table, condition=None):
    if condition:
        data = sqlitequery(database, "select * from '" + table + "\'" + " where " + condition)
    else:
        data = sqlitequery(database, 'select * from \'' + table + '\'')

    pragmanames = getpragmanames(database, table)

    dictarray = []
    for row in data:
        dict = {}
        index = 0
        for datum in row:
            dict[pragmanames[index]] = datum
            index += 1
        dictarray.append(dict)

    return dictarray


# Now we put them together into a dynamically typed function
# that we specify operation based on what arguments we send
# No location argument = entire database
# One locaiton argument = single row
# Two arguments = range of rows

def dynamicsqliteread(database, table, start=None, length=None, condition=None):
    if length is None and start is None:
        dictarray = readalldbrows(database, table, condition)
    elif length is None:
        dictarray = readonedbrow(database, table, start)
    else:
        dictarray = readsomedbrows(database, table, start, length)

    return dictarray


def getlogsize(databasename, tablename):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')
    return logsize


def sizesqlitetable(databasename, tablename, size, orderby='time', order='asc'):
    logsize = getlogsize(databasename, tablename)

    if logsize > size:
        logexcess = logsize - size
        sqlitequery(databasename, 'delete from \"' + tablename + '\" where \"' + orderby + '\" in  ( select \"' + orderby + '\" from \"' + tablename + '\" order by \"' + orderby + '\" ' + order + ' limit ' + str(logexcess) + ')')
    else:
        logexcess = -1

    return (logexcess)


# This will actually take a dict or dictarray. This does not, however
# prevent errors if you pass dictionaries with keys that do not exist
# after the first dictionary. That said, proceed.

def dropcreatetexttablefromdict(databasename, tablename, dictordictarray):
    querylist = []
    constructor = ''
    querylist.append('drop table if exists \"' + tablename + '\"')

    # just make it an array if not so we can handle the array
    if isinstance(dictordictarray, dict):
        dictarray = [dictordictarray]
    else:
        dictarray = dictordictarray
    for key, value in dictarray[0].items():
        constructor = constructor + '\"' + key + '\" text,'
    querylist.append('create table \"' + tablename + '\" (' + constructor[:-1] + ')')
    for singledict in dictarray:
        valuelist = ''
        for key, value in singledict.items():
            valuelist = valuelist + '\"' + value + '\",'
        querylist.append('insert into \"' + tablename + '\" values (' + valuelist[:-1] + ')')

    #print(querylist)
    sqlitemultquery(databasename, querylist)


def synctablesbyname(database, fromname, toname, fields=None):
    from datalib import readalldbrows

    dbdictarray = readalldbrows(database, fromname)
    querylist = []
    for dbdict in dbdictarray:
        if fields is None:  # Do all
            for key, value in dbdict.items():
                querylist.append(
                    'update \"' + toname + '\" set \"' + key + '\"=\"' + value + '\" where name=\"' + dbdict[
                        'name'] + '\"')
                #print(querylist)
        else:
            for key in fields:
                querylist.append(
                    'update \"' + toname + '\" set \"' + key + '\"=\"' + dbdict[key] + '\" where name=\"' + dbdict[
                        'name'] + '\"')
    sqlitemultquery(database, querylist)


def sqlitedatadump(databasename, tablelist, outputfilename, limit=None):
    import csv

    queryarray = []

    # These are for csv file headers
    allpragmanames = []
    alltablelist = []

    for tablename in tablelist:
        pragmanames = getpragmanames(databasename, tablename)
        for pragmaname in pragmanames:
            alltablelist.append(tablename)
            allpragmanames.append(pragmaname)
            if limit is not None:
                queryarray.append('select ' + pragmaname + ' from \"' + tablename + '\" limit ' + str(limit))
            else:
                queryarray.append('select ' + pragmaname + ' from \"' + tablename + '\"')
    data = sqlitemultquery(databasename, queryarray)
    newdata = []
    for outerlist in data:
        newinnerlist = []
        for innerlist in outerlist:
            newinnerlist.append(innerlist[0])
        newinnerlist.insert(0, allpragmanames.pop(0))
        newinnerlist.insert(0, alltablelist.pop(0))
        newdata.append(newinnerlist)

    print(newdata)
    with open(outputfilename, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(newdata)


