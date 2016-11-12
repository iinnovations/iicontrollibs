#!/usr/bin/env python

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


"""

Database tools

"""


def switchtablerows(database, table, rowid1, rowid2, uniqueindex):
    unique1 = sqlitedatumquery(database,
                               'select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid1))
    unique2 = sqlitedatumquery(database,
                               'select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid2))
    # print('select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid1))
    # print(unique1 + ' ' +  unique2)
    queryarray = []
    index = 'rowid'
    # Assumes there is no rowid=9999
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        9999) + ' where \'' + uniqueindex + '\'=\'' + unique2 + '\'')
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        rowid2) + ' where \'' + uniqueindex + '\'=\'' + unique1 + '\'')
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        rowid1) + ' where \'' + uniqueindex + '\'=\'' + unique2 + '\'')

    # print(queryarray)
    sqlitemultquery(database, queryarray)


def removeandreorder(database, table, rowid, indicestoorder=None, uniqueindex=None):
    sqlitequery(database, ' from \'' + table + '\' where rowid=' + rowid)
    if indicestoorder and uniqueindex:
        ordertableindices(database, table, indicestoorder, uniqueindex)


def ordertableindices(databasename, tablename, indicestoorder, uniqueindex):
    table = readalldbrows(databasename, tablename)
    uniquearray = []
    for row in table:
        uniquearray.append(row[uniqueindex])
    queryarray = []
    for i, uniquevalue in enumerate(uniquearray):
        for indextoorder in indicestoorder:
            queryarray.append('update \'' + tablename + '\' set "' + indextoorder + '"=\'' + str(
                i + 1) + '\'  where "' + uniqueindex + '"=\'' + str(uniquevalue) + '\'')

    # print(queryarray)
    # print(queryarray)
    sqlitemultquery(databasename, queryarray)


def logtimevaluedata(database, tablename, timeinseconds, value, logsize=5000, logfrequency=0):
    from iiutilities.datalib import gettimestring, isvalidtimestring, timestringtoseconds
    timestring= gettimestring(timeinseconds)
    if isvalidtimestring(timestring):

        # Get last polltime to determine if we should log again yet.
        # lastpolltimestring = getlasttimerow(database, tablename)['time']
        try:
            lastpolltimestring = getlasttimevalue(database, tablename)
        except:
            lastpolltimestring = ''
        else:
            # print lastpolltimestring
            pass
        if timeinseconds- timestringtoseconds(lastpolltimestring) > logfrequency:

            # Create table if it doesn't exist

            query = 'create table if not exists \'' + tablename + '\' ( value real, time text primary key)'
            sqlitequery(database, query)

            # Enter row
            sqliteinsertsingle(database, tablename, valuelist=[value, timestring],
                                     valuenames=['value', 'time'])

            # Clean log
            cleanlog(database, tablename)

            # Size log based on specified size

            sizesqlitetable(database, tablename, logsize)
        else:
            # print('not time yet')
            pass
    else:
        # print('not enabled')
        pass


def gettablenames(database):
    result = sqlitequery(database, 'select name from sqlite_master where type=\'table\'')
    tables = []
    for element in result:
        tables.append(element[0])
    return tables


def getdatameta(database):
    tablenames = gettablenames(database)
    queryarray = []
    for tablename in tablenames:
        queryarray.append("select count(*) from '" + tablename + "'")
    results = sqlitemultquery(database, queryarray)
    meta = []
    for result, tablename in zip(results, tablenames):
        meta.append({'tablename':tablename, 'numpoints':result[0][0]})
    return meta


def getandsetmetadata(database):
    meta = getdatameta(database)
    queryarray = []
    queryarray.append('drop table if exists metadata')
    queryarray.append('create table metadata ( name text, numpoints int)')
    for metaitem in meta:
        queryarray.append("insert into metadata values ('" + str(metaitem['tablename']) + "','" + str(metaitem['numpoints']) + "')")
        #print(queryarray)
    sqlitemultquery(database, queryarray)


def getpragma(database, table):
    pragma = sqlitequery(database, 'pragma table_info ( \'' + table + '\')')
    return pragma


def getpragmanames(database, table):
    pragma = getpragma(database, table)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item[1])
    return pragmanames


def getpragmatypes(database, table):
    pragma = getpragma(database, table)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item[2])
    return pragmanames


def getpragmanametypedict(database, table):
    pragma = getpragma(database, table)
    pragmadict = {}
    for item in pragma:
        pragmadict[item[1]] = item[2]
    return pragmadict


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


def insertstringdicttablelist(database, tablename, datadictarray, droptable=False):
    querylist = []
    if droptable:
        querylist.append('drop table if exists "' + tablename + '"')

        addquery = 'create table "' + tablename + '" ('
        for key in datadictarray[0]:
            addquery += '\'' + key + '\' text,'

        addquery = addquery[:-1]
        addquery += ')'
        querylist.append(addquery)

    for datadict in datadictarray:
        valuelist=[]
        valuenames=[]
        for key in datadict:
            valuelist.append(datadict[key])
            valuenames.append(key)
        insertquery = makesqliteinsert(tablename, valuelist, valuenames)
        # print(insertquery)
        querylist.append(insertquery)

    result = {'query': querylist}

    # try:
    sqlitemultquery(database, querylist)
    # except:
    #     import sys, traceback
    #     result['tb'] = traceback.format_exc()
    #     result['status'] = 1
    # else:
    #     result['status'] = 0

    return result


def sqlitecreateemptytable(database, tablename, valuenames, valuetypes, valueoptions=None, dropexisting=True,
                           removequotes=True, removeslashes=True):
    if len(valuenames) != len(valuetypes):
        print('Names and types are not of same length. Cannot continue. ')
        return None
    else:
        if valueoptions:
            if len(valuenames) != len(valueoptions):
                print('Valueoptions were delivered but do not appear to be the correct length. Cannot continue. ')
                return None

    existingtablenames = gettablenames(database)
    if tablename in existingtablenames:
        if dropexisting:
            sqlitedroptable(database, tablename)
        else:
            # Check to see if this will work out? Match fields, etc.
            pass

    constructor = ''
    for index, valuename in enumerate(valuenames):
        try:
            if removequotes:
                valuename = valuename.replace("'", '').replace('"', '')
            if removeslashes:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + valuetypes[index]

        # limited. multiple options in the future.
        if 'primary' == valueoptions[index]:
            constructor += ' primary key'
        elif 'unique' == valueoptions[index]:
            constructor += ' unique'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    sqlitequery(database, constructorquery)


def dropcreatetexttablefromdict(databasename, tablename, dictordictarray, removequotes=True, removeslashes=True, primarykey=None):
    querylist = []
    constructor = ''
    querylist.append('drop table if exists "' + tablename + '"')

    # just make it an array if not so we can handle the array
    if isinstance(dictordictarray, dict):
        dictarray = [dictordictarray]
    else:
        dictarray = dictordictarray

    for key, value in dictarray[0].items():
        try:
            if removequotes:
                key = key.replace("'", '').replace('"', '')
            if removeslashes:
                key = key.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(key))

        constructor = constructor + "'" + key + "' text"
        if primarykey:
            if key == primarykey:
                constructor += ' primary key'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    # print(constructorquery)
    querylist.append(constructorquery)

    for singledict in dictarray:
        valuelist = ''
        for key, value in singledict.items():
            if removequotes:
                value = str(value).replace("'", '').replace('"', '')
            if removeslashes:
                value = str(value).replace("\\", '').replace("/", "")

            valuelist = valuelist + '\"' + value + '\",'
        querylist.append('insert or replace into \"' + tablename + '\" values (' + valuelist[:-1] + ')')

    # print(querylist)
    sqlitemultquery(databasename, querylist)


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
        strvalue = str(value).replace("'","''")
        query += '\'' + strvalue + '\','
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


def sqlitequery(database, query):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    try:
        with con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
    except:
        data = ''
    return data


def sqlitedatumquery(database, query):
    datarow = sqlitequery(database, query)
    if datarow:
        datum = datarow[0][0]
    else:
        datum = ''
    return datum


def getsinglevalue(database, table, valuename, condition=None):
    query = makegetsinglevaluequery(table, valuename, condition)
    # print(query)
    response = sqlitedatumquery(database, query)
    return response


def makegetsinglevaluequery(table, valuename, condition=None):
    query = 'select \"' + valuename + '\" from \'' + table + '\''
    if isinstance(condition, dict):
        try:
            conditionnames = condition['conditionnames']
            conditionvalues = condition['conditionvalues']
        except:
            # print('oops')
            pass
        else:
            query += ' where '
            numconditions = len(conditionnames)
            for index, (name, value) in enumerate(zip(conditionnames, conditionvalues)):
                query += "\"" + name + "\"='" + value + "'"
                if index < numconditions-1:
                    query += ' and '
            # print(query)
    elif isinstance(condition, basestring):
        query += ' where ' + condition
    return query


def sqlitedeleteitem(database, table, condition):
    sqlitequery(database, makedeletesinglevaluequery(table, condition))


def makedeletesinglevaluequery(table, condition=None):
    query = 'delete from \'' + table + '\''
    if isinstance(condition, dict):
        try:
            conditionnames = condition['conditionnames']
            conditionvalues = condition['conditionvalues']
        except:
            print('oops')
        else:
            query += ' where '
            numconditions = len(conditionnames)
            for index, (name, value) in enumerate(zip(conditionnames, conditionvalues)):
                query += "\"" + name + "\"='" + value + "'"
                if index < numconditions-1:
                    query += ' and '
    elif isinstance(condition, basestring):
        query += ' where ' + condition
    return query


def readalldbrows(database, table, condition=None, includerowids=True):

    query = 'select * from \'' + table + '\''
    if condition:
        query += ' where ' + condition

    data = sqlitequery(database, query)

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


def makegetallrowsquery(tablename):
    query = "select * from '" + tablename + "'"
    return query


def getentiredatabase(databasename, method='nometa'):
    # Get names of all tables in database
    tablenames = gettablenames(databasename)
    databasequery = []

    # Construct a query for each table
    for tablename in tablenames:
        databasequery.append(makegetallrowsquery(tablename))

    # Execute multiple query to return data
    alldatabasedata = sqlitemultquery(databasename, databasequery)
    reconstructeddatabase=[]
    tables = []

    # This method blindly produces lists
    if method == 'nometa':
        # reconstruct without tuples

        for index, table in enumerate(alldatabasedata):
            newtable = []
            for row in table:
                newtable.append(list(row))
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data': newtable})

    # This method puts meta from each table into a dictionary entry
    elif method == 'metameta':
        for index, table in enumerate(alldatabasedata):
            newtable = []

            # print(tablenames[index])
            meta = getpragmanames(databasename, tablenames[index])
            for row in table:
                newtable.append(list(row))
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data':newtable, 'meta':meta})

    # This method produces a list of dictionaries so all data is self-described (but big)
    else:

        for index, table in enumerate(alldatabasedata):
            newtable = []

            # print(tablenames[index])
            pragmanames = getpragmanames(databasename, tablenames[index])
            for row in table:
                newrow = {}

                for name, value in zip(pragmanames, row):
                    newrow[name] = value
                newtable.append(newrow)
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data':newtable})

    return {'data': reconstructeddatabase, 'dictarray': tables, 'tablenames': tablenames}


def sqliteemptytable(database, tablename):
    querylist = []
    querylist.append('delete from \'' + tablename + '\'')
    sqlitemultquery(database, querylist)


def emptyandsetdefaults(database, tablename):
    querylist = []
    querylist.append('delete from \'' + tablename + '\'')
    querylist.append('insert into \'' + tablename + '\' default values')
    sqlitemultquery(database, querylist)


# Now we put them together into a dynamically typed function
# that we specify operation based on what arguments we send
# No location argument = entire database
# One location argument = single row
# Two arguments = range of rows


def dynamicsqliteread(database, table, start=None, length=None, condition=None):
    if length is None and start is None:
        dictarray = readalldbrows(database, table, condition)
    elif length is None:
        dictarray = readonedbrow(database, table, start, condition)
    else:
        dictarray = readsomedbrows(database, table, start, length, condition)

    return dictarray


def cleanlog(databasename, logname):
    sqlitequery(databasename, "delete from '" + logname + "' where time =''")


def sqliteduplicatetable(database, oldname, newname):
    # Get pragma to create table
    oldcreatequery = sqlitequery(database, "SELECT sql FROM sqlite_master WHERE type='table' AND name='" + oldname + "'")[0][0]
    # print(oldcreatequery)

    # Check to see if it was created with quotes or not
    # Gotta use quotes on new name for safety
    index = oldcreatequery.find('"' + oldname + '"')
    if index >= 0:
        newcreatequery = oldcreatequery.replace('"' + oldname + '"', '"' + newname + '"')
    else:
        newcreatequery = oldcreatequery.replace(oldname, '"' + newname + '"')

    # print(newcreatequery)
    sqlitequery(database, newcreatequery)

    # Now get all the old data and insert it
    data=readalldbrows(database, oldname)

    # We have to drop all records and insert string without the droptable, just in case it already exists.
    # This way we retain the table structure
    sqlitedeleteallrecords(database, newname)
    insertstringdicttablelist(database, newname, data, droptable=False)


def sqlitemovetable(database, oldname, newname):
    sqliteduplicatetable(database, oldname, newname=newname)
    sqlitedroptable(database, oldname)


def sqlitedeleteallrecords(database, table):
    sqlitequery(database, 'delete from "' + table + '"')


def sqlitedroptable(database, table):
    sqlitequery(database, 'drop table "' + table + '"')


def gettablesize(databasename, tablename):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')
    return logsize


def sizesqlitetable(databasename, tablename, size):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')

    if logsize and (logsize > size):
        logexcess = int(logsize) - int(size)
        sqlitequery(databasename, 'delete from\'' + tablename + '\' order by time limit ' + str(logexcess))
    else:
        logexcess = -1

    return (logexcess)


def getfirsttimerow(database, tablename, timecolname='time'):
    query = 'select * from \'' + tablename + '\' order by \'' + timecolname + '\' limit 1'
    data = sqlitequery(database, query)[0]
    try:
        dict = datarowtodict(database, tablename, data)
        dictarray = [dict]
    except:
        # print('no row here')
        dictarray = {}
        pass

    return dictarray


def getlasttimerows(database, tablename, numrows=1):
    query = 'select * from \'' + tablename + '\' order by time desc limit ' + str(int(numrows))
    data = sqlitequery(database, query)
    try:
        dictarray = []
        for datum in data:
            dict = datarowtodict(database, tablename, datum)
            dictarray.append(dict)
    except:
        # print('no row here')
        dictarray = {}
        pass
    return dictarray


def getlasttimevalue(database, tablename):
    query = 'select time from \'' + tablename + '\' order by time desc limit 1'
    data = sqlitequery(database, query)[0][0]
    return data


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
                queryarray.append('select ' + pragmaname + ' from \'' + tablename + '\' limit ' + str(limit))
            else:
                queryarray.append('select ' + pragmaname + ' from \'' + tablename + '\'')
    data = sqlitemultquery(databasename, queryarray)
    #print(data)
    newdata = []
    for outerlist in data:
        newinnerlist = []
        for innerlist in outerlist:
            newinnerlist.append(innerlist[0])
        newinnerlist.insert(0, allpragmanames.pop(0))
        newinnerlist.insert(0, alltablelist.pop(0))
        newdata.append(newinnerlist)

    #print(newdata)
    with open(outputfilename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(newdata)


def setsinglevalue(database, table, valuename, value, condition=None):
    query = makesinglevaluequery(table, valuename, value, condition)
    response = sqlitequery(database, query)
    return response


def makesinglevaluequery(table, valuename, value, condition=None):
    query = 'update ' + "'" + table + '\' set "' + valuename + '"=\'' + str(value) + "'"
    if condition:
        query += ' where ' + condition
    return query


def readonedbrow(database, table, rownumber=0, condition=None):
    query = "select * from '" + table + "'"
    if condition:
        query += ' where ' + condition
    data = sqlitequery(database, query)
    try:
        datarow = data[rownumber]

        dict = datarowtodict(database, table, datarow)
        dictarray = [dict]
    except:
        dictarray = []

    return dictarray


def readsomedbrows(database, table, start, length, condition=None):

    # User specifies length of data, and where to start, in terms of row index
    # If a negative number is the start argument, data is retrieved from the end of the data

    if start >= 0:
        query = "select * from '" + table + "' limit " + str(start) + ',' + str(length)
    else:
        query = "select * from '" + table + "' order by rowid desc " + " limit " + str(length)
    # print(query)
    if condition:
        query += ' where ' + condition

    datarows = sqlitequery(database, query)

    # This is the old code. Requires retrieving the entire table

    # Start < 0 retrieves from end of list
    # if start < 0:
    #     datarows = data[len(data)-length:len(data)-1]
    # else:
    #     datarows = data[int(start):int(start + length)]

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


def dbvntovalue(dbvn, interprettype=False):

    from iiutilities.datalib import parsedbvn, getvartype
    dbvndict = parsedbvn(dbvn)

    # try:

    value = getsinglevalue(dbvndict['dbpath'], dbvndict['tablename'], dbvndict['valuename'], dbvndict['condition'])
    # except:
    #     print('error getting value')
    #     print(dbvndict)
    #     return None

    if interprettype:
        # get type

        vartype = getvartype(dbvndict['dbpath'], dbvndict['tablename'], dbvndict['valuename'])

        if vartype == 'boolean':
            return bool(value)
        elif vartype == 'float':
            return float(value)
        elif vartype == 'int':
            return int(value)

    return value