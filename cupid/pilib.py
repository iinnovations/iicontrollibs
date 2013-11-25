#!/usr/bin/python

# This library is for use by all other fermostat pi
# functions

#############################################
## Utility Functions
#############################################

def gettimestring(timeinseconds=None):
    import time
    if timeinseconds:
        try:
            timestring = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timeinseconds))
        except TypeError:
            timestring=''
    else:
        timestring = time.strftime("%Y-%m-%d %H:%M:%S")
    return timestring

def timestringtoseconds(timestring):
    import time

    try:
        timeinseconds=time.mktime(time.strptime(timestring,"%Y-%m-%d %H:%M:%S"))
    except ValueError:
        timeinseconds=0
    return timeinseconds

#############################################
## Authlog functions 
#############################################

def checklivesessions(authdb,user, expiry):
    import pilib, time 
    activesessions=0
    sessions=pilib.readalldbrows(authdb,'sessions')
    for session in sessions:
        sessioncreation=pilib.timestringtoseconds(session['timecreated'])
        currenttime=time.mktime(time.localtime())
        if currenttime-sessioncreation<expiry:
            activesessions+=1

    return activesessions

#############################################
## Sqlite Functions
#############################################

def getpragma(database,table):
    pragma = sqlitequery(database,'pragma table_info ( \'' + table + '\')')
    return pragma

def getpragmanames(database,table):
    pragma = getpragma(database,table)
    pragmanames=[]
    for item in pragma:
        pragmanames.append(item[1])
    return pragmanames

def datarowtodict(database,table,datarow):
    pragma = getpragma(database,table)
    #print(pragma)

    pragmanames=[]
    for item in pragma:
        pragmanames.append(item[1])

    dict={}
    index=0
    for datum in datarow:
        dict[pragmanames[index]]=datum
        index+=1
    return dict

def makesqliteinsert(database, table, valuelist,insert=True):
    if insert:
        query = 'insert or replace into \'' + table + '\' values('
    else:
        query = 'insert into \'' + table + '\' values('
    for value in valuelist:
        query = query + "'" + str(value) + "'," 
    query = query[:-1] + ")"
    return query

def sqliteinsertsingle(database,table,valuelist):
    import sqlite3 as lite
    #from pilib import makesqliteinsert 

    con = lite.connect(database)
    con.text_factory = str

    with con:

        cur = con.cursor()
        query = makesqliteinsert(database,table,valuelist) 
        cur.execute(query)
    
def sqlitemultquery(database,querylist):
    import sqlite3 as lite
    import sys

    con = lite.connect(database)
    con.text_factory = str

    with con:

        cur = con.cursor()
        data=[]
        for query in querylist:
            cur.execute(query)
            dataitem=cur.fetchall()
            data.append(dataitem)
    
        con.commit() 
    return data

def sqlitequery(database,query):
    import sqlite3 as lite
    import sys

    con = lite.connect(database)
    con.text_factory = str

    try:
        with con:

            cur = con.cursor()
            cur.execute(query)
    
            data = cur.fetchall()
    except: 
        data=''

    return data

def sqlitedatumquery(database,query):
    datarow=sqlitequery(database,query)
    if datarow:
        datum=datarow[0][0]
    else:
        datum=''
    return datum

def readonedbrow(database,table,rownumber):
    data = sqlitequery(database,'select * from \'' + table + '\'')
    datarow = data[rownumber]
    
    dict=datarowtodict(database,table,datarow)
    dictarray=[dict]

    return dictarray

def readsomedbrows(database,table,start,length):
    data = sqlitequery(database,'select * from \'' + table + '\'')
    datarows = data[int(start):int(start+length)]
    pragmanames=getpragmanames(database,table)

    dictarray=[]
    for row in datarows:
        dict={}
        index=0
        for datum in row:
            dict[pragmanames[index]]=datum
            index+=1
        dictarray.append(dict)

    return dictarray

def readalldbrows(database,table):
    data = sqlitequery(database,'select * from \'' + table + '\'')

    pragmanames=getpragmanames(database,table)

    dictarray=[]
    for row in data:
        dict={}
        index=0
        for datum in row:
            dict[pragmanames[index]]=datum
            index+=1
        dictarray.append(dict)

    return dictarray

# Now we put them together into a dynamically typed function
# that we specify operation based on what arguments we send
# No location argument = entire database
# One location argument = single row
# Two arguments = range of rows

def dynamicsqliteread(database,table,start = None,length = None):
    if length is None and start is None:
        dictarray = readalldbrows(database,table)
    elif length is None:
        dictarray = readonedbrow(database,table,start)
    else:
        dictarray = readsomedbrows(database,table,start,length)

    return dictarray

def sizesqlitetable(databasename,tablename,size):
    logsize = sqlitedatumquery(databasename,'select count(*) from \'' + tablename + '\'')

    if logsize > size:
        logexcess = logsize - size 
        sqlitequery(databasename,'delete from\'' + tablename +'\' order by time limit ' + str(logexcess))
    else:
        logexcess=-1

    return(logexcess)

def sqlitedatadump(databasename,tablelist,outputfilename,limit=None):
    import csv
    queryarray=[]

    # These are for csv file headers
    allpragmanames=[]
    alltablelist=[]

    for tablename in tablelist:
        pragmanames=getpragmanames(databasename,tablename)
        for pragmaname in pragmanames:
            alltablelist.append(tablename)
            allpragmanames.append(pragmaname)
            if limit is not None:
                queryarray.append('select ' + pragmaname + ' from \"' + tablename + '\" limit ' + str(limit))
            else:
                queryarray.append('select ' + pragmaname + ' from \"' + tablename + '\"')
    data=sqlitemultquery(databasename,queryarray)
    #print(data)
    newdata=[]
    for outerlist in data:
        newinnerlist=[]
        for innerlist in outerlist:
            newinnerlist.append(innerlist[0])
        newinnerlist.insert(0,allpragmanames.pop(0))
        newinnerlist.insert(0,alltablelist.pop(0))
        newdata.append(newinnerlist)

    #print(newdata)
    with open(outputfilename,"wb") as f:
        writer = csv.writer(f)
        writer.writerows(newdata)

