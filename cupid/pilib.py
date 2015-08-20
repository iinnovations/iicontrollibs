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
motesdatabase = databasedir + 'motes.db'

safedatabase = '/var/wwwsafe/safedata.db'
usersdatabase = '/var/wwwsafe/users.db'

logdir = '/var/log/cupid/'

networklog = logdir + 'network.log'
iolog = logdir + 'io.log'
remotelog = logdir + 'remotes.log'
systemstatuslog = logdir + 'systemstatus.log'
controllog = logdir + 'control.log'
daemonlog = logdir + 'daemon.log'

daemonproclog = logdir + '/daemonproc.log'
errorlog = logdir + '/error.log'

salt = 'a bunch of random characters and symbols for security'

maxlogsize = 1024  # kB
numlogs = 5


networkloglevel = 5
iologlevel = 3
systemstatusloglevel = 4
controlloglevel = 3
daemonloglevel = 3

daemonprocs = ['cupid/periodicupdateio.py', 'cupid/picontrol.py', 'cupid/systemstatus.py', 'cupid/sessioncontrol.py', 'mote/serialhandler.py']


#############################################
## Utility Functions
#############################################


def getgpiostatus():

    from subprocess import check_output

    gpiolist=[]
    alloutput = check_output(['gpio','readall'])
    lines = alloutput.split('\n')[3:18]
    for line in lines:
        BCM1 = line[4:6].strip()
        wpi1 = line[10:12].strip()
        name1 = line[15:22].strip()
        mode1 = line[25:30].strip()
        val1 = line[32:34].strip()
        phys1 = line[36:39].strip()

        phys2 = line[42:44].strip()
        val2 = line[46:48].strip()
        mode2 = line[50:55].strip()
        name2 = line[57:65].strip()
        wpi2 = line[68:70].strip()
        BCM2 = line[74:76].strip()

        if BCM1 and BCM1 != '--':
            # print(BCM1 + ':' + wpi1 + ':' + name1 + ':' + mode1 + ':' + val1 + ':' + phys1)
            gpiolist.append({'BCM': BCM1, 'wpi': wpi1, 'name': name1, 'mode': mode1, 'value': val1, 'phys': phys1})
        if BCM2 and BCM2 != '--':
            # print(BCM2 + ':' + wpi2 + ':' + name2 + ':' + mode2 + ':' + val2 + ':' + phys2)
            gpiolist.append({'BCM': BCM2, 'wpi': wpi2, 'name': name2, 'mode': mode2, 'value': val2, 'phys': phys2})

    return gpiolist


def writedatedlogmsg(logfile, message, reqloglevel=1, currloglevel=1):
    if currloglevel >= reqloglevel:
        logfile = open(logfile, 'a')
        logfile.writelines([gettimestring() + ' : ' + message + '\n'])
        logfile.close()


def gethashedentry(user, password):
    import hashlib
     # Create hashed, salted password entry
    hpass = hashlib.new('sha1')
    hpass.update(password)
    hashedpassword = hpass.hexdigest()
    hname = hashlib.new('sha1')
    hname.update(user)
    hashedname = hname.hexdigest()
    hentry = hashlib.new('md5')
    hentry.update(hashedname + salt + hashedpassword)
    hashedentry = hentry.hexdigest()
    return hashedentry


def rotatelogs(logname, numlogs=5, logsize=1024):
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
        if currlogsize > logsize * 1000:
            for i in range(numlogs - 1):
                oldlog = logname + '.' + str(numlogs - i - 2)
                newlog = logname + '.' + str(numlogs - i - 1)
                try:
                    os.rename(oldlog, newlog)
                except:
                    logmessage += 'file error. log ' + oldlog + ' does not exist?\n'

            try:
                os.rename(logname, logname + '.1')
                os.chmod(logname + '.1', 744)
                open(logname, 'a').close()
                os.chmod(logname, 764)

            except:
                logmessage += 'original doesn\'t exist\?\n'
                returnmessage = "error in "
        else:
            logmessage += 'log not big enough\n'
            returnmessage = 'logs not rotated'
    return {'message': returnmessage, 'logmessage': logmessage, 'statuscode': statuscode}


def parseoptions(optionstring):
    optionsdict = {}
    if optionstring:
        try:
            list = optionstring.split(',')
            for item in list:
                split = item.split(':')
                optionsdict[split[0].strip()] = split[1].strip()
        except:
            pass

    return optionsdict


def dicttojson(dict):
    jsonentry = ''
    for key, value in dict.iteritems():
        jsonentry += key + ':' + value.replace('\x00','') + ','
    jsonentry = jsonentry[:-1]
    return jsonentry

#####################################
# Time functions
#####################################

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


def isvalidtimestring(timestring):
    if timestring == '':
        return False
    else:
        return True


def tail(f, n, offset=None):
    """Reads a n lines from f with an offset of offset lines.  The return
    value is a tuple in the form ``(lines, has_more)`` where `has_more` is
    an indicator that is `True` if there are more lines in the file.
    """
    avg_line_length = 74
    to_read = n + (offset or 0)

    while 1:
        try:
            f.seek(-(avg_line_length * to_read), 2)
        except IOError:
            # woops.  apparently file is smaller than what we want
            # to step back, go to the beginning instead
            f.seek(0)
        pos = f.tell()
        lines = f.read().splitlines()
        if len(lines) >= to_read or pos == 0:
            return lines[-to_read:offset and -offset or None], \
                   len(lines) > to_read or pos > 0
        avg_line_length *= 1.3


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
            message = 'Alert is active for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been on since ' + self.ontime + '.'
            subject = 'CuPID Alert : Alarm On - ' + self.name
            actionmail = gmail(message=message, subject=subject, recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.statusmsg += 'Processing indicator on action. '
            indicatorname = self.actiondetail
            sqlitequery(controldatabase, 'update indicators set status=1 where name = \'' + indicatorname + '\'')

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output on action. '
            setsinglevalue(controldatabase, 'outputs', 'value', '1', condition='"id"=\'' + self.actiondetail +"'")

    def offact(self):
        if self.actiontype == 'email':
            # process email action
            self.statusmsg +='Processing email alert.'
            email = self.actiondetail
            message = 'Alert has gone inactive for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been of since ' + self.offtime + '.'
            subject = 'CuPID Alert : Alarm Off - ' + self.name
            actionmail = gmail(message=message, subject=subject, recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.status +='Processing indicator off action.'
            indicatorname = self.actiondetail
            sqlitequery(controldatabase, 'update indicators set status=0 where name = ' + indicatorname)

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output off action. '
            setsinglevalue(controldatabase, 'outputs', 'value', '0', condition='"id"=\'' + self.actiondetail +"'")

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
    import pilib
    import time

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
            queryarray.append('update \'' + tablename + '\' set "' + indextoorder + '"=\'' + str(
                i + 1) + '\'  where "' + uniqueindex + '"=\'' + str(uniquevalue) + '\'')

    # print(queryarray)
    print(queryarray)
    sqlitemultquery(databasename, queryarray)

def logtimevaluedata(database, tablename, timeinseconds, value, logsize=5000, logfrequency=0):
    timestring=gettimestring(timeinseconds)
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
        if timeinseconds-timestringtoseconds(lastpolltimestring) > logfrequency:

            # Create table if it doesn't exist

            query = 'create table if not exists \'' + tablename + '\' ( value real, time text primary key)'
            sqlitequery(database, query)

            # Enter row
            sqliteinsertsingle(logdatabase, tablename, valuelist=[value, timestring],
                                     valuenames=['value', 'time'])

            # Clean log
            cleanlog(logdatabase, tablename)

            # Size log based on specified size

            sizesqlitetable(logdatabase, tablename, logsize)
        else:
            # print('not time yet')
            pass
    else:
        # print('not enabled')
        pass


#############################################
## Sqlite Functions
#############################################

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


def insertstringdicttablelist(database, tablename, datadictarray):
    querylist = []
    querylist.append('drop table if exists ' + tablename)


    addquery = 'create table ' + tablename + ' ('
    for key in datadictarray[0]:
        addquery += '\'' + key + '\' text,'

    addquery = addquery[:-1]
    addquery += ')'
    querylist.append(addquery)

    for datadict in datadictarray:
        valuelist=[]
        for key in datadict:
            valuelist.append(datadict[key])
        insertquery = makesqliteinsert(tablename, valuelist)
        querylist.append(insertquery)
    sqlitemultquery(database, querylist)


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
    query = 'select * from \'' + table + '\''
    if condition:
        query += ' where ' + condition
    data = sqlitequery(database, query)
    try:
        datarow = data[rownumber]

        dict = datarowtodict(database, table, datarow)
        dictarray = [dict]
    except:
        # print('no row here')
        dictarray = {}
        pass

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


def readalldbrows(database, table, condition=None):

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


def emptyandsetdefaults(database, tablename):
    querylist = []
    querylist.append('delete from \'' + tablename + '\'')
    querylist.append('insert into \'' + tablename + '\' default values')
    sqlitemultquery(database,querylist)


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


def getlasttimerow(database, tablename):
    query = 'select * from \'' + tablename + '\' order by time desc limit 1'
    data = sqlitequery(database, query)[0]
    try:
        dict = datarowtodict(database, tablename, data)
        dictarray = [dict]
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


def getlogconfig():
    logconfigdata = readonedbrow(controldatabase,'logconfig')[0]
    return logconfigdata
import logging


## Not used yet. Eventually convert to python logging module

# levels = getlogconfig()
#
# networklogger = logging.getLogger('networklogger')
# networklogger.propagate = False
# formatter = logging.Formatter('%(asctime)s - %(message)s')
#
# fh = logging.FileHandler('/var/log/cupid/samplelogger.log')
# fh.setLevel(10)
# fh.setFormatter(formatter)
# networklogger.addHandler(fh)

