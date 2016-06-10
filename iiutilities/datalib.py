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

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def parseoptions(optionstring):
    optionsdict = {}
    if optionstring:
        try:
            list = optionstring.split(',')
            for item in list:
                # print(item)
                split = item.split(':')
                valuename = split[0].strip()
                # Need to allow for colons in the value.
                stringvalue = ':'.join(split[1:]).replace('"','').strip()
                optionsdict[valuename] = stringvalue
        except:
            pass
    return optionsdict


def dicttojson(dict):
    jsonentry = ''
    for key, value in dict.iteritems():
        jsonentry += key + ':' + str(value).replace('\x00','') + ','
    jsonentry = jsonentry[:-1]
    return jsonentry


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


def timestringtoseconds(timestring=None):
    import time
    try:
        timeinseconds = time.mktime(time.strptime(timestring, '%Y-%m-%d %H:%M:%S'))
    except:
        timeinseconds = 0
    return timeinseconds


def getnexttime(timestring, unit, increment):
    from datetime import datetime, timedelta
    actiontime = datetime.fromtimestamp(timestringtoseconds(timestring))
    currenttime = datetime.fromtimestamp(timestringtoseconds(gettimestring()))

    if unit == 'second':
        nextactiontime = datetime(currenttime.year, currenttime.month, currenttime.day, currenttime.hour, currenttime.minute, currenttime.second)
        nextactiontime = nextactiontime + timedelta(seconds=increment)
    elif unit == 'minute':
        nextactiontime = datetime(currenttime.year, currenttime.month, currenttime.day, currenttime.hour, currenttime.minute + increment, actiontime.second)
    elif unit == 'hour':
        nextactiontime = datetime(currenttime.year, currenttime.month, currenttime.day, currenttime.hour + increment, actiontime.minute, actiontime.second)
    elif unit == 'day':
        nextactiontime = datetime(currenttime.year, currenttime.month, currenttime.day + increment, actiontime.hour, actiontime.minute, actiontime.second)
    elif unit == 'month':
        nextactiontime = datetime(currenttime.year, currenttime.month + increment, actiontime.day, actiontime.hour, actiontime.minute, actiontime.second)
    else:
        nextactiontime = currenttime
    # print(nextactiontime)
    return(nextactiontime)


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


def calcastevalformula(formula):
    from asteval import Interpreter
    aeval = Interpreter()
    result = aeval(formula)
    # print('RESULT: ' + str(result))
    return result


def calcinputrate(input, numentries=2):

    from iiutilities import dblib
    from cupid import pilib

    # just grab last entries of log, create point averaged around
    # also average time

    logname = 'input_' + input + '_log'
    entries = dblib.getlasttimerows(pilib.dirs.dbs.log, logname, numentries)
    # print(entries)

    if len(entries) == numentries:
        lastentry = entries[numentries-1]
        firstentry = entries[0]

        dvalue = float(lastentry['value'])-float(firstentry['value'])
        dtime = timestringtoseconds(lastentry['time'])-timestringtoseconds(firstentry['time'])

        rate = dvalue/dtime
        ratetime = (timestringtoseconds(lastentry['time'])+timestringtoseconds(firstentry['time'])) / 2
        ratetimestring = gettimestring(ratetime)

        result = {'rate':rate, 'ratetime':ratetimestring}
    else:
        result = None
    return result


def evaldbvnformula(formula, type='value'):

    from iiutilities.dblib import dbvntovalue

    #if type == 'value':
    # first we need to get all the values that are provided as db-coded entries.
    # We put the dbvn inside of brackets, e.g. [dbnmae:dbtable:dbvaluename:condition]
    try:
        split = formula.split('[')
    except:
        return None

    textform = ''
    for index, splitlet in enumerate(split):
        # print('splitlet: ' + splitlet)
        if index == 0:
            textform += splitlet
        else:
            splitletsplit = splitlet.split(']')
            dbvn = splitletsplit[0]
            # print('dbvn: ' + dbvn)
            try:
                value = dbvntovalue(dbvn)
            except:
                return None
            # print('value: ' + str(value))
            textform += str(value) + splitletsplit[1]

    # print('EQN Text:')
    # print('"' + textform + '"')
    result = calcastevalformula(textform)
    return result


def getvartype(dbpath, tablename, valuename):
    from iiutilities import dblib
    variablestypedict = dblib.getpragmanametypedict(dbpath, tablename)
    vartype = variablestypedict[valuename]
    return vartype


def parsedbvn(dbvn):

    from cupid import pilib
    # print('DBVN: ')
    # print(dbvn)
    """
    databasename:tablename:valuename:condition
    """

    split = dbvn.split(':')
    dbname = split[0].strip()
    dbpath = pilib.dbnametopath(dbname)
    if not dbpath:
        # print("error getting dbpath, for dbname: " + dbname)
        return None

    tablename = split[1].strip()
    valuename = split[2].strip()
    if len(split) == 4:
        condition = split[3]
    else:
        condition = None

    return {'dbname':dbname,'dbpath':dbpath,'tablename':tablename,'valuename':valuename,'condition':condition}