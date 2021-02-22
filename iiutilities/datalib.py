#!/usr/bin/python3

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

time_format_string = '%Y-%m-%d %H:%M:%S'
ms_time_format_string = "%Y-%m-%d %H:%M:%S.%f"

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

def string_to_boolean(string):
    try:
        boolean=bool(int(string))
    except:
        if string.tolower() in ['f', 'false'] or not string:
            boolean=False
        else:
            boolean=True
    return boolean

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


# opposite of above
def dicttojson(pass_dict):
    jsonentry = ''
    for key in pass_dict:
        value = pass_dict[key]
        jsonentry += key + ':' + str(value).replace('\x00','') + ','
    jsonentry = jsonentry[:-1]
    return jsonentry


def get_illegal_text_items(**kwargs):
    settings = {
        'brackets_ok': False,
        'colons_ok':False,
        'spaces_ok':False,
        'hyphens_ok':True,
        'slashes_ok':False,
        'commas_ok':False,
        'periods_ok':False,
        'arithmetic_ok':False
    }
    settings.update(kwargs)
    bad_characters = ['"', "'"]
    if not settings['brackets_ok']:
        bad_characters.extend(['{', '}', '[', ']'])
    if not settings['colons_ok']:
        bad_characters.extend([':', ';'])
    if not settings['spaces_ok']:
        bad_characters.append(' ')
    if not settings['slashes_ok']:
        bad_characters.extend(['\\','/'])
    if not settings['periods_ok']:
        bad_characters.append('.')
    if not settings['commas_ok']:
        bad_characters.append(',')
    if not settings['arithmetic_ok']:
        bad_characters.extend(['*','-','+','='])

    return bad_characters


def find_all_string_locations(text, match_string, start_position=0):
    match_positions = []
    while text.find(match_string, start_position) >=0:
        match_position = text.find(match_string, start_position)
        match_positions.append(match_position)
        start_position = match_position+1
        # print(start_position)
    return match_positions


def clean_dirty_text(dirty_text, **kwargs):

    test_results = test_questionable_text(dirty_text, **kwargs)
    # print(test_results)
    if test_results['isdirty']:
        for match in test_results['matches']:
            # print('replacing "' + match['character'] + '"')
            dirty_text = dirty_text.replace(match['character'], '')

    clean_text = dirty_text
    return clean_text


def test_questionable_text(text, **kwargs):
    bad_characters = get_illegal_text_items(**kwargs)
    questionable = False
    questionable_matches = []
    for character in bad_characters:
        match_positions = find_all_string_locations(text, character)
        if match_positions:
            questionable = True
            # print('Illegal character ' + character + ' found at position(s)' + str(match_positions))
            questionable_matches.append({'character':character, 'match_positions':match_positions})

    return {'isdirty':questionable, 'matches':questionable_matches}


def getmstimestring():
    import datetime
    timestring = datetime.datetime.now().strftime(ms_time_format_string)
    return timestring

#  datetime.date.strftime(now,'%Y-%m-%d %H:%M:%S')
# datetime.datetime.strptime('2017-12-26 22:30:34', '%Y-%m-%d %H:%M:%S')


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


def getutctimestring(timeinseconds=None):
    import time
    if timeinseconds:
        try:
            timestring = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timeinseconds))
        except TypeError:
            timestring = ''
    else:
        timestring = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    return timestring


def timestrings_diff_in_seconds(time1, time2):
    import ciso8601
    time_diff = (ciso8601.parse_datetime(time2)-ciso8601.parse_datetime(time1)).total_seconds()
    return time_diff


def localize_utc_timestring(timestring, timezone=None, timezone_name='US/Pacific', timeformat='%Y-%m-%d %H:%M:%S'):
    import pytz, datetime

    if type(timestring) == str:
        import datetime
        timestring = datetime.datetime.strptime(timestring, timeformat)

    aware_time = pytz.utc.localize(timestring)

    if not timezone:
        timezone = pytz.timezone(timezone_name)

    local_time = aware_time.astimezone(timezone)
    local_timestring = datetime.datetime.strftime(local_time, timeformat)
    return local_timestring


def localtimestring_to_utc_timestring(timestring, timezone=None, timezone_name='US/Pacific', timeformat='%Y-%m-%d %H:%M:%S'):
    import pytz, datetime

    if type(timestring) == str:
        import datetime
        timestring = datetime.datetime.strptime(timestring, timeformat)

    if not timezone:
        timezone = pytz.timezone(timezone_name)

    aware_time = timezone.localize(timestring)

    utc_time = aware_time.astimezone(pytz.utc)
    utc_timestring = datetime.datetime.strftime(utc_time,timeformat)

    return utc_timestring


def timestringtoseconds(timestring=None, defaulttozero=None, **kwargs):

    settings = {
        'useciso':False,
        'debug':False
    }
    settings.update(kwargs)

    from calendar import timegm
    timestring = str(timestring)

    if settings['debug']:
        print('Using CISO: {}'.format(settings['useciso']))
    import time
    if not timestring and defaulttozero:
        return 0

    # Ok, for now we are going to hack our old, non-compliant data format just to see if this helps.
    timeinseconds = 0
    try:
        if settings['useciso']:
            try:
                import ciso8601, datetime
                parsed_time = ciso8601.parse_datetime(timestring)
                epoch = datetime.datetime.utcfromtimestamp(0)
                timeinseconds = (parsed_time-epoch).total_seconds()
                # timeinseconds = parsed_time.replace(tzinfo=datetime.timezone.utc).timestamp()
            except:
                if settings['debug']:
                    import traceback
                    print('We encountered this exception: {}'.format(traceback.format_exc()))

                timeinseconds = timegm(timestring_to_struct(timestring))
        else:
            timeinseconds = timegm(timestring_to_struct(timestring))
    except:
        if settings['debug']:
            import traceback
            print('We encountered this exception: {}'.format(traceback.format_exc()))

    return timeinseconds


def mstimestringtoseconds(timestring=None, defaulttozero=False):
    import time
    if not timestring and defaulttozero:
        return 0
    try:
        timeinseconds = time.mktime(mstimestring_to_struct(timestring))
    except:
        timeinseconds = 0
    return timeinseconds


def timestring_to_struct(timestring=None):
    import time
    try:
        time_struct = time.strptime(timestring, time_format_string)
    except:
        time_struct = time.strptime(gettimestring(), time_format_string)
    return time_struct


def mstimestring_to_struct(timestring=None):
    import time
    try:
        time_struct = time.strptime(timestring, ms_time_format_string)
    except:
        time_struct = time.strptime(getmstimestring(), ms_time_format_string)
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
    # print(bytes)
    value = float32bytestovalue(bytes)
    # print(value)
    # print(number)


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
    # print('VALUES')
    # print(values)
    # for value in values:
    #     print(type(value))

    if wordorder == 'reverse':
        word0 = values[1]
        word1 = values[0]
    else:
        word0 = values[0]
        word1 = values[1]

    if byteorder == 'reverse':
        byte1 = int(word0 % 256)
        byte2 = int((word0 - byte1) / 256)
        byte3 = int(word1 % 256)
        byte4 = int((word1 - byte3) / 256)
    else:
        byte2 = int(word0 % 256)
        byte1 = int((word0 - byte2) / 256)
        byte4 = int(word1 % 256)
        byte3 = int((word1 - byte4) / 256)

    # print(byte1)
    # print(byte2)
    # print(byte3)
    # print(byte4)

    byte1hex = chr(byte1)
    byte2hex = chr(byte2)
    byte3hex = chr(byte3)
    byte4hex = chr(byte4)

    abytearray = bytearray()
    abytearray.append(byte1)
    abytearray.append(byte2)
    abytearray.append(byte3)
    abytearray.append(byte4)

    # print('byteshex')
    # print(byte1hex, byte2hex, byte3hex, byte4hex)

    hexbytes = byte1hex.encode() + byte2hex.encode() + byte3hex.encode() + byte4hex.encode()
    returnvalue = struct.unpack('>f', abytearray)[0]

    return returnvalue


def bytestovalue(bytes, format='word32'):
    # Standard word order
    # MSW, LSW

    # Above seems inaccurate for PLCs we are working with. Going to change float32 to default to reverse word here
    # May break something elsewhere, but doesn't appear to be used ubiquitously since CuPID OS is dead.

    # Standard byte order
    # MSB, LSB

    # Standard is byteorder=standard, wordorder=standard
    if format in ['float32swsb', 'float32sw', 'float32sb']:
        value = float32bytestovalue(bytes)
    elif format in ['float32rw', 'float32rwsb', 'float32']:
        value = float32bytestovalue(bytes, wordorder='reverse')
    elif format in ['float32rb', 'float32swrb']:
        value = float32bytestovalue(bytes, byteorder='reverse')
    elif format in ['float32rwrb']:
        value = float32bytestovalue(bytes, byteorder='reverse', wordorder='reverse')

    elif format == 'word32':
        value = bytes[0] * 65536 + bytes[1]
    elif format == 'word32rw':
        value = bytes[1] * 65536 + bytes[0]
    elif format == 'boolean':
        value = int(bytes[0])

    # no provision for reverse bytes in word yet
    else:
        value = bytes[0]

    return value


def valuetobytes(value, format='beword32'):
    if 'word' in format and '32' in format:
        bigbyte = int(value / 65536)
        smallbyte = value % 65536
        if format == 'beword32':
            bytes = [bigbyte, smallbyte]
        else:
            bytes = [smallbyte, bigbyte]
    elif 'float' in format:
        bytes = valuetofloat32bytes(value)
    else:
        bytes = [int(value)]
    return bytes


def valuetofloat32bytes(value, type='float', endian='big', byteorder='standard'):
    import struct
    if type == 'float':
        mybytearray = struct.pack("!f", value)
    elif type == 'double':
        mybytearray = struct.pack("!d", value)
    else:
        return

    # integers = [ord(c) for c in mybytearray]
    # print(integers)
    # print(mybytearray)

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
    entries = dblib.getlasttimerows(pilib.dirs.dbs.log, logname, numrows=numentries)
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


def calcaverage(input, points=5, countzero=True):

    from iiutilities import dblib
    from cupid import pilib

    # just grab last entries of log, create point averaged around
    # also average time

    logname = 'input_' + input + '_log'
    # print(logname)
    entries = dblib.getlasttimerows(pilib.dirs.dbs.log, logname, timecolname='time', numrows=points)
    # print(entries)

    if len(entries) == points:

        points_used = 0
        sum_value = 0.0
        average_seconds = 0
        for entry in entries:
            value = entry['value']
            time_in_seconds = timestringtoseconds(entry['time'])
            if countzero:
                try:
                    sum_value += float(value)
                except:
                    pass
                else:
                    average_seconds += time_in_seconds
                    points_used += 1
            else:
                if value:
                    try:
                        sum_value += float(value)
                    except:
                        pass
                    else:
                        average_seconds += time_in_seconds
                        points_used += 1

        average = sum_value / points_used
        average_time = gettimestring(average_seconds / points_used)

        result = {'average':average, 'points':points_used, 'time':average_time}
    else:
        result = None
    return result


def evaldbvnformula(formula, type='value', debug=False):

    from iiutilities.dblib import dbvntovalue

    if debug:
        print(formula)
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
            if debug:
                print('dbvn: ' + dbvn)
            try:
                value = dbvntovalue(dbvn)
            except:
                return None
            # print('value: ' + str(value))
            textform += str(value) + splitletsplit[1]

    if debug:
        print('EQN Text:')
        print('"' + textform + '"')
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

    # Have to beware of conditions with colons in them.
    if len(split) == 4:
        condition = split[3]
    elif len(split) > 4:
        condition = ':'.join(split[3:])
    else:
        condition = None

    return {'dbname':dbname,'dbpath':dbpath,'tablename':tablename,'valuename':valuename,'condition':condition}


# Auth functions

def gethashedentry(user, password, salt='randomsalt'):

    if type(user) == type('string'):
        user_bytes = user.encode('utf-8')
    elif type(user) == type('string'.encode('utf-8')):
        user_bytes = user
    else:
        return

    if type(password) == type('string'):
        password_bytes = password.encode('utf-8')
    elif type(password) == type('string'.encode('utf-8')):
        password_bytes = password
    else:
        return

    import hashlib
     # Create hashed, salted password entry
    hpass = hashlib.new('sha1')
    hpass.update(password_bytes)
    hashedpassword = hpass.hexdigest()
    hname = hashlib.new('sha1')
    hname.update(user_bytes)
    hashedname = hname.hexdigest()
    hentry = hashlib.new('md5')

    # for item in [hashedname, salt, hashedpassword, hentry]:
    #     print(item, type(item))
        # print(type(item))
    # hentry.update('{}{}{}'.format(hashedname,salt,hashedpassword))
    hentry.update('{}{}{}'.format(hashedname, salt, hashedpassword).encode('utf-8'))

    hashedentry = hentry.hexdigest()
    return hashedentry


"""

Historian and data massaging stuff

"""

def sparsify_time_value_data(data, **kwargs):

    from decimal import Decimal
    from datetime import datetime

    settings = {
        'method':'tolerance',
        'threshold':Decimal(0.01),
        'threshold_type':'absolute',
        'debug':False,
        'presort':True,
        'max_time_gap':180, #s
        'time_label': 'time'
    }
    settings.update(kwargs)

    if settings['presort']:
        # Sort the data:
        pass

    # convenience
    time_label = settings['time_label']

    if settings['debug']:
        print('processing {} data points'.format(len(data)))
        time_span = timestringtoseconds(data[0][time_label]) - timestringtoseconds(data[-1][time_label])
        print('Time span: {}'.format(time_span))

    start_time = datetime.now()

    # Do this so we only have to calculate times once and index
    if settings['max_time_gap']:
        # use elapsed times here because it's faster
        import ciso8601
        converted_timestamps = [ciso8601.parse_datetime(datum[time_label]) for datum in data]
        times_in_seconds = [(converted_timestamps[i] - converted_timestamps[0]).total_seconds() for i in range(len(data))]
        # times_in_seconds = [timestringtoseconds(datum['time'], **settings) for datum in data]
    else:
        times_in_seconds = ['' for datum in data]

    new_data = []
    removed_data = []
    if settings['method'] == 'tolerance':

        # always keep beginning and ending points
        new_data.append(data[0])
        last_datum_time_s = times_in_seconds[0]

        for i in range(len(data)-2):

            skip_this_point = False

            last_datum = new_data[-1]
            this_datum = data[i+1]
            next_datum = data[i+2]

            if abs(Decimal(this_datum['data']) - Decimal(last_datum['data'])) < settings['threshold']:
                # if settings['debug']:
                #     print('{} : within tolerance for previous point'.format(i))
                if abs(Decimal(this_datum['data']) - Decimal(next_datum['data'])) < settings['threshold']:
                    # if settings['debug']:
                    #     print('{} : within tolerance for next point'.format(i))

                    if settings['max_time_gap']:
                        time_span = times_in_seconds[i+1] - last_datum_time_s

                        if time_span <= settings['max_time_gap']:
                            if settings['debug']:
                                print('{} : omitting point'.format(i))
                            skip_this_point=True
                        else:
                            if settings['debug']:
                                print('max time gap of {} exceeded. Inserting.'.format(settings['max_time_gap']))
                    else:
                        # No time requirement
                        skip_this_point = True

            if not skip_this_point:
                new_data.append(this_datum)
                last_datum_time_s = times_in_seconds[i+1]
            else:
                removed_data.append(this_datum)

        # Now tack on the last point
        new_data.append(data[-1])

    elif settings['method'] == 'timespan':
        """
        {
            'method':'timespan',
            'length':2,
            'unit':'day'
        },
        """

        last_datum_time_s = times_in_seconds[-1]

        if settings['unit'] == 'week':
            timespan_in_seconds = settings['length'] * 7 * 24 * 60 * 60
        elif settings['unit'] == 'day':
            timespan_in_seconds = settings['length'] * 24 * 60 * 60
        elif settings['unit'] == 'hour':
            timespan_in_seconds = settings['length'] * 60 * 60
        elif settings['unit'] == 'minute':
            timespan_in_seconds = settings['length'] * 60

        for i in range(len(data)):
            if last_datum_time_s - times_in_seconds[i] <= timespan_in_seconds:
                new_data.append(data[i])
            else:
                removed_data.append(data[i])

    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()

    if settings['debug']:
        print('Elapsed_time: {}s'.format(elapsed_time))

        print('Resulting data set has {} points'.format(len(new_data)))
        omitted_points = len(data) - len(new_data)
        print('{} points omitted ({:.2f}%)'.format(omitted_points, float(omitted_points) / len(data) * 100))


    return {'new_data':new_data, 'removed_data':removed_data, 'status':0, 'elapsed_time':elapsed_time}


def test_sparsify_data(**kwargs):

    from iiutilities import dblib
    settings = {
        'database':'/var/www/html/cupidcontrol/data/clients/testclient/testclient_data.db',
        'tablename':'pH',
        'debug':True
    }
    settings.update(**kwargs)
    the_db = dblib.sqliteDatabase(settings['database'])
    the_data = the_db.read_table(settings['tablename'])

    return_stuff = sparsify_time_value_data(the_data, **settings)

    return return_stuff


def test_time_conversion(**kwargs):
    settings = {
        'numpoints':100000,
        'method':'old',
        'debug':False
    }
    settings.update(kwargs)

    import datetime

    now = datetime.datetime.now()
    data = [{'time':(now + datetime.timedelta(seconds=15*i)).strftime(time_format_string), 'value':i} for i in range(settings['numpoints'])]

    start_time = datetime.datetime.now()

    if settings['method'] == 'old':
        converted_times = [timestringtoseconds(datum['time'], debug=settings['debug']) for datum in data]
    elif settings['method'] == 'new':
        converted_times = [timestringtoseconds(datum['time'], useciso=True, debug=settings['debug']) for datum in data]
    elif settings['method'] == 'new_elapsed':
        import ciso8601
        converted_timestamps = [ciso8601.parse_datetime(datum['time']) for datum in data]
        converted_times = [(converted_timestamps[i]-converted_timestamps[0]).total_seconds() for i in range(len(data))]


    print(converted_times)
    end_time = datetime.datetime.now()
    elapsed_time = (end_time-start_time).total_seconds()
    print('Elapsed time: {}'.format(elapsed_time))


