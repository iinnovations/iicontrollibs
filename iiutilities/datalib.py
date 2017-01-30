#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


# File operations

def delimitedfiletoarray(filename, delimiter=','):
    import csv

    with open(filename, 'rU') as delimitedfile:
        data = csv.reader(delimitedfile, delimiter=delimiter)
        array = []
        try:
            for row in data:
                # print(row)
                try:
                    array.append(row)
                except:
                    print('error in row')
        except:
            print('uncaught row error')
    return array


def datawithheaderstodictarray(dataarray, headerrows=1, strip=True, keystolowercase=False):
    # we assume the first row is full of dict keys

    dictarray = []
    for i in range(headerrows, len(dataarray)):
        datadict = {}
        for j in range(0, len(dataarray[0])):
            if strip:
                dataarray[i][j]=dataarray[i][j].strip()

            if keystolowercase:
                datadict[dataarray[0][j].lower()] = dataarray[i][j]
            else:
                datadict[dataarray[0][j]] = dataarray[i][j]

        dictarray.append(datadict)

    return dictarray


# Data functions

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
        timeinseconds = time.mktime(timestring_to_struct(timestring))
    except:
        timeinseconds = 0
    return timeinseconds


def timestring_to_struct(timestring=None):
    import time
    try:
        time_struct = time.strptime(timestring, '%Y-%m-%d %H:%M:%S')
    except:
        time_struct = time.strptime(gettimestring(), '%Y-%m-%d %H:%M:%S')
    return time_struct


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


def setprecision(number, precision):
    number = float(int(float(number) * (10 ** precision))) / 10 ** precision
    return number


def checkfloat(number):
    # Not functional
    bytes = valuetofloat32bytes(number, type='double')
    print(bytes)
    value = float32bytestovalue(bytes)
    print(value)
    print(number)


def typetoreadlength(type):
    if type in ['word', 'word16', 'float16','word16rb', 'float16rb', 'bit']:
        readlength = 1
    elif type in ['word32', 'word32rw', 'word32sw','word32rwrb', 'word32rwsb', 'word32swrb', 'word32swsb',
                  'float32', 'float32rw', 'float32sw','float32rwrb', 'float32rwsb', 'float32swrb', 'float32swsb']:
        readlength = 2
    else:
        # print('READLENGTH NOT FOUND for "' + type + '". RETURNING DEFAULT 1 to be nice.')
        readlength = 1
    return readlength


def float32bytestovalue(values, wordorder='standard', byteorder='standard'):
    import struct

    if wordorder == 'reverse':
        word0 = values[1]
        word1 = values[0]
    else:
        word0 = values[0]
        word1 = values[1]

    if byteorder == 'reverse':
        byte1 = word0 % 256
        byte2 = (word0 - byte1) / 256
        byte3 = word1 % 256
        byte4 = (word1 - byte3) / 256
    else:
        byte2 = word0 % 256
        byte1 = (word0 - byte2) / 256
        byte4 = word1 % 256
        byte3 = (word1 - byte4) / 256

    byte1hex = chr(byte1)
    byte2hex = chr(byte2)
    byte3hex = chr(byte3)
    byte4hex = chr(byte4)
    hexstring = byte1hex + byte2hex + byte3hex + byte4hex
    returnvalue = struct.unpack('>f', hexstring)[0]

    return returnvalue


def bytestovalue(bytes, format='word32'):
    # Standard word order
    # MSW, LSW

    # Standard byte order
    # MSB, LSB

    # Standard is byteorder=standard, wordorder=standard
    if format in ['float32', 'float32swsb', 'float32sw', 'float32sb']:
        value = float32bytestovalue(bytes)
    elif format in ['float32rw', 'float32rwsb']:
        value = float32bytestovalue(bytes, wordorder='reverse')
    elif format in ['float32rb', 'float32swrb']:
        value = float32bytestovalue(bytes, byteorder='reverse')
    elif format in ['float32rwrb']:
        value = float32bytestovalue(bytes, byteorder='reverse', wordorder='reverse')

    elif format == 'word32':
        value = bytes[1] * 65536 + bytes[0]
    elif format == 'word32rw':
        value = bytes[0] * 65536 + bytes[1]
    elif format == 'boolean':
        value = int(bytes[0])

    # no provision for reverse bytes in word yet
    else:
        value = bytes[0]

    return value


def valuetobytes(value, format='beword32'):
    if format in ['beword32', 'leword32']:
        bigbyte = value / 65536
        smallbyte = value % 65536
        if format == 'beword32':
            bytes = [bigbyte, smallbyte]
        else:
            bytes = [smallbyte, bigbyte]
    elif format=='float32':
        pass
    return bytes


def valuetofloat32bytes(value, type='float', endian='big', byteorder='standard'):
    import struct
    if type == 'float':
        mybytearray = struct.pack("!f", value)
    elif type == 'double':
        mybytearray = struct.pack("!d", value)
    else:
        return

    integers = [ord(c) for c in mybytearray]
    print(integers)
    print(mybytearray)

    byte0 = mybytearray[0]*256 + mybytearray[1]
    byte1 = mybytearray[2]*256 + mybytearray[2]

    returnvalue = [byte0, byte1]

    return returnvalue


def calcastevalformula(formula, x=None):

    """
    This takes a formula, such as 9**8 + sin(19)
    Optionally, provide the formula with x included and a value for x, e.g.
     calcastevalformula(x**2 =5, x=18)
    """

    from asteval import Interpreter
    if x or x==0:
        # print('we found x with value ' + str(x))
        formula = formula.replace('x',str(x))

    # print(formula)
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


# Auth functions

def gethashedentry(user, password, salt='randomsalt'):

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