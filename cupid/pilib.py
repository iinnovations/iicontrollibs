#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2014, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'

# This library is for use by all other pi
# functions

# Global declarations of file locations

baselibdir = '/usr/lib/iicontrollibs/'
databasedir = '/var/www/data/'
onewiredir = '/var/1wire/'
outputdir = '/var/www/data/'
controldatabase = databasedir + 'controldata.db'
logdatabase = databasedir + 'logdata.db'
sessiondatabase = databasedir + 'authlog.db'
recipedatabase = databasedir + 'recipedata.db'
systemdatadatabase = databasedir + 'systemdata.db'

#############################################
## Utility Functions
#############################################

def parseoptions(optionstring):
    list = optionstring.split(',')
    optionsdict={}
    for item in list:
        split = item.split(':')
        optionsdict[split[0]] = split[1]
    return optionsdict


def gettimestring(timeinseconds=None):
    import time
    if timeinseconds:
        try:
            timestring = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeinseconds))
        except TypeError:
            timestring = ''
    else:
        timestring = time.strftime('%Y-%m-%d %H:%M:%S')
    return timestring


def timestringtoseconds(timestring):
    import time
    try:
        timeinseconds = time.mktime(time.strptime(timestring, '%Y-%m-%d %H:%M:%S'))
    except ValueError:
        timeinseconds = 0
    return timeinseconds


# This class defines actions taken on
class action:
    def __init__(self, actiondict):
        for key, value in actiondict.items():
            setattr(self, key, value)

    def onact(self):
        if self.actiontype == 'email':
            # process email action
            self.statusmsg += 'Processing email alert. '
            email = self.actiondetail
            message = 'Alert is active for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + self.criterion + ' with an operator of ' + self.operator + '. This alarm status has been on since ' + self.ontime + '.'
            subject = 'CuPID Alert : Alarm On - ' + self.name
            actionmail = gmail(message=message, subject=subject, recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.status += 'Processing indicator on action. '
            indicatorname = self.actiondetail
            sqlitequery(controldatabase, 'update indicators set status=1 where name = \'' + indicatorname + '\'')

    def offact(self):
        if self.actiontype == 'email':
            # process email action
            self.statusmsg +='Processing email alert.'
            email = self.actiondetail
            message = 'Alert has gone inactive for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + self.criterion + ' with an operator of ' + self.operator + '. This alarm status has been of since ' + self.offtime + '.'
            subject = 'CuPID Alert : Alarm Off - ' + self.name
            actionmail = gmail(message=message, subject=subject,recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.status +='Processing indicator off action.'
            indicatorname = self.actiondetail
            sqlitequery(controldatabase, 'update indicators set status=0 where name = ' + indicatorname)

    def publish(self):
        # reinsert updated action back into database
        valuelist=[]
        valuenames=[]
        for attr,value in self.__dict__.iteritems():
            valuelist.append(value)
            valuenames.append(attr)
        sqliteinsertsingle(controldatabase, 'actions', valuelist, valuenames)
        # setsinglevalue(controldatabase, 'actions', 'ontime', gettimestring(), 'rowid=' + str(self.rowid))


class gmail:
    def __init__(self, server='smtp.gmail.com', port=587, subject='default subject', message='default message',
                 login='cupidmailer@interfaceinnovations.org', password='cupidmail', recipient='info@interfaceinnovations.org', sender='CuPID Mailer'):
        self.server = server
        self.port = port
        self.message = message
        self.subject = subject
        self.sender = sender
        self.login = login
        self.password = password
        self.recipient = recipient
        self.sender = sender

    def send(self):
        import smtplib

        headers = ['From:' + self.sender,
                  'Subject:' + self.subject,
                  'To:' + self.recipient,
                  'MIME-Version: 1.0',
                  'Content-Type: text/html']
        headers = '\r\n'.join(headers)

        session = smtplib.SMTP(self.server, self.port)

        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.login, self.password)

        session.sendmail(self.sender, self.recipient, headers + '\r\n\r\n' + self.message)
        session.quit()


#############################################
## Authlog functions 
#############################################

def checklivesessions(authdb, user, expiry):
    import pilib, time

    activesessions = 0
    sessions = pilib.readalldbrows(authdb, 'sessions')
    for session in sessions:
        sessioncreation = pilib.timestringtoseconds(session['timecreated'])
        currenttime = time.mktime(time.localtime())
        if currenttime - sessioncreation < expiry:
            activesessions += 1

    return activesessions


#############################################
## Database tools
#############################################

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
            queryarray.append('update \'' + tablename + '\' set \'' + indextoorder + '\'=' + str(
                i + 1) + '  where \'' + uniqueindex + '\'=\'' + uniquevalue + '\'')

    print(queryarray)
    sqlitemultquery(databasename, queryarray)


#############################################
## Sqlite Functions
#############################################

# The beginning of our class development.
class database:
    def __init__(self, path):
        self.directory = directory

    def gettablenames(self):
        self.tablenames = gettablenames(self.path)

    def getdatameta(self):
        self.meta = gettablenames(self.path)


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
        queryarray.append('select count(*) from \'' + tablename + '\'')
    results = sqlitemultquery(database, queryarray)
    meta = []
    for result, tablename in zip(results, tablenames):
        meta.append([tablename, result[0][0]])
    return meta


def getandsetmetadata(database):
    meta = getdatameta(database)
    queryarray = []
    queryarray.append('drop table if exists metadata')
    queryarray.append('create table metadata ( name text, numpoints int)')
    for item in meta:
        queryarray.append('insert into metadata values (\'' + str(item[0]) + '\',' + '\'' + str(item[1]) + '\')')
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


def sqliteinsertsingle(database, table, valuelist, valuenames=None):
    import sqlite3 as lite
    #from pilib import makesqliteinsert 

    con = lite.connect(database)
    con.text_factory = str

    with con:
        cur = con.cursor()
        query = makesqliteinsert(table, valuelist, valuenames)
        cur.execute(query)


def sqlitemultquery(database, querylist):
    import sqlite3 as lite
    import sys

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
    query = 'select \'' + valuename + '\' from \'' + table + '\''
    if condition:
        query += ' where ' + condition
    print(query)
    response = sqlitedatumquery(database, query)
    return (response)


def setsinglevalue(database, table, valuename, value, condition=None):
    query = 'update ' + '\'' + table + '\' set \'' + valuename + '\'=\'' + value + '\''
    if condition:
        query += ' where ' + condition

    response = sqlitequery(database, query)
    return (response)


def readonedbrow(database, table, rownumber=0):
    data = sqlitequery(database, 'select * from \'' + table + '\'')
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


def readalldbrows(database, table):
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
# One location argument = single row
# Two arguments = range of rows

def dynamicsqliteread(database, table, start=None, length=None):
    if length is None and start is None:
        dictarray = readalldbrows(database, table)
    elif length is None:
        dictarray = readonedbrow(database, table, start)
    else:
        dictarray = readsomedbrows(database, table, start, length)

    return dictarray


def sizesqlitetable(databasename, tablename, size):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')

    if logsize > size:
        logexcess = logsize - size
        sqlitequery(databasename, 'delete from\'' + tablename + '\' order by time limit ' + str(logexcess))
    else:
        logexcess = -1

    return (logexcess)


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

