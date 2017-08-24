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


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


def progressbar(time=5, length=20, type='percentage'):

    from time import sleep
    import sys

    for i in range(length):
        lesslength = length - 1
        sys.stdout.write('\r')
        # the exact output you're looking for:
        p = int(100/length*(i+1))
        if type == 'totaltime':
            sys.stdout.write("[%" + '=' * i + '>' + ' ' * (length-i) + "] " + str(float(time)) + 's total ')
        elif type == 'percentoftotaltime':
            sys.stdout.write("[%" + '=' * i + '>' + ' ' * (length-i) + "] " + str(p) + '% of ' + str(float(time)) + 's total ')
        else:
            sys.stdout.write("[%" + '=' * i + '>' + ' ' * (length - i) + "] " + str(p) + '% ')

        sys.stdout.flush()

        sleep(float(time)/float(length))

    # print('')


def split_time_log(log, **kwargs):

    """
    Input here is a log
    """

    settings = {'key': 'time', 'format': 'datetimestring', 'splitmethod': 'time', 'division': 'day'}
    settings.update(kwargs)

    newlist = sorted(log, key=lambda k: k[settings['key']])

    dated_dict_list = {}
    if settings['splitmethod'] == 'time':
        for listitem in newlist:
            if settings['division'] == 'day':
                import time
                if settings['format'] == 'datetimestring':
                    from datalib import timestring_to_struct
                    the_time = timestring_to_struct(listitem['time'])
                criterion = time.struct_time((the_time.tm_year, the_time.tm_mon, the_time.tm_mday, 0, 0, 0, 0, 1, 0))
                # criterion = (time.tm_year, time.tm_mon, time.tm_mday)
            if criterion not in dated_dict_list:
                dated_dict_list[criterion] = [listitem]
            else:
                dated_dict_list[criterion].append(listitem)

    # for key in dated_dict_list:
    #     print(key, len(dated_dict_list[key]))

    return dated_dict_list


def split_time_db(path, **kwargs):

    """
    This beast will go through an entire database and size every log with a well-formed time column
    """
    settings = {
        'division':'day',
        'timekey':'time'
    }
    settings.update(kwargs)

    from iiutilities import dblib
    from datalib import gettimestring
    import time

    database = dblib.sqliteDatabase(path)

    tablenames = database.get_table_names()
    # print(tablenames)
    all_dates = []

    """
    [timestring, timestring, timestring]
    """

    sorted_data = {}
    """
    {
    tableaame:
        {
        struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
            [
            timekey:timestring, 'valuename':'value',
            timekey:timestring, 'valuename':'value'
            ]
        struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
            [
            timekey:timestring, 'valuename':'value',
            timekey:timestring, 'valuename':'value'
            ]
        }
    }
    """

    for tablename in tablenames:
        raw_data = database.read_table(tablename)
        schema = database.get_schema(tablename)

        """
        [
        {timekey:'atimestring','value':'somevalue'},
        {timekey:'anothertimestring','value':'somevalue'}
        ]
        """

        if raw_data:
            if settings['timekey'] in raw_data[0]:
                """
                sorted_data[tablename] [=]
                {
                    'data':
                    {
                        struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
                        [
                            timekey:timestring, 'valuename':'value',
                            timekey:timestring, 'valuename':'value'
                        ]
                        struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
                        [
                            timekey:timestring, 'valuename':'value',
                            timekey:timestring, 'valuename':'value'
                        ]
                    }
                    'schema':sqliteTableSchema object
                }
                """

                # print(schema)
                sorted_data[tablename] = {'data':split_time_log(raw_data), 'schema':schema}
            else:
                print('Table ' + tablename + ' does not have a time column. Skipping. ')
                continue

            # add date tuples to master list
            for key in sorted_data[tablename]['data']:
                if key not in all_dates:
                    all_dates.append(key)

    data_by_date = {}

    """
    data_by_date [=]
    {
        timestruct:
        {
            datatablename:
            {
                'data':
                {
                    struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
                    [
                        timekey:timestring, 'valuename':'value',
                    timekey:timestring, 'valuename':'value'
                    ]
                    struct_time(the_time.tm_year, the_time.tm_mon, the_time.tm_mday, ....):
                    [
                        timekey:timestring, 'valuename':'value',
                        timekey:timestring, 'valuename':'value'
                    ]
                },
                'schema':sqliteTableSchema object
            }
        }
    }
    """

    for date in all_dates:
        data_by_date[date] = {}
        for tablename in sorted_data:
            if date in sorted_data[tablename]['data']:
                data_by_date[date][tablename] = {'data':sorted_data[tablename]['data'][date],
                                                 'schema':sorted_data[tablename]['schema']}


    # print('dates: ' + str(len(all_dates)))
    return data_by_date


def split_and_trim_db_by_date(logpath, **kwargs):

    import dblib
    from datalib import gettimestring
    import time

    settings = {
        'division': 'day',
        'timekey': 'time',
        'remove': 'true'
    }
    settings.update(kwargs)

    data_by_date = split_time_db(logpath, **settings)
    dates = [date for date in data_by_date]
    dates.sort(reverse=True)

    # print('Most recent date', dates[0])
    if dates:
        current_date = dates[0]
    else:
        # print('NO time yet.')
        current_date = time.gmtime()

    # print(current_date)
    dates.reverse()

    log_db = dblib.sqliteDatabase(logpath)

    modified_dbs = []

    for date in data_by_date:

        # Prune off time.
        timestring = gettimestring(time.mktime(date)).split(' ')[0]
        # print(timestring, 'tables: ' +str(len([tablename for tablename in data_by_date[date]])))

        # for table in data_by_date[date]:
        #     print(table)
        new_db_path = logpath.split('.')[0] + '_' + timestring + '.' + logpath.split('.')[1]

        modified_dbs.append(new_db_path)
        new_db = dblib.sqliteDatabase(new_db_path)

        # if table doesn't exist, we create it
        new_db.tablenames = new_db.get_table_names()
        # print('existing tablenames: ')
        # print(new_db.tablenames)
        for tablename in data_by_date[date]:
            if tablename not in new_db.tablenames:
                # print('creating table ' + tablename)
                new_db.create_table(tablename, data_by_date[date][tablename]['schema'], queue=True)

            # print(data_by_date[date][tablename]['data'][0])
            # print(data_by_date[date][tablename]['schema'].items)
            new_db.insert(tablename, data_by_date[date][tablename]['data'], queue=True)

        # print(new_db.queued_queries)

        new_db.execute_queue()

        # Now we need to remove the old entries
        if date != current_date:
            for tablename in data_by_date[date]:
                for datum in data_by_date[date][tablename]['data']:
                    log_db.delete(tablename, '"' + settings['timekey'] + '"=' + "'" + datum[settings['timekey']] + "'", queue=True)


    # print(log_db.queued_queries)
    # print('Deletes',len(log_db.queued_queries))
    log_db.execute_queue()

    return {'modified_dbs':modified_dbs}


def rotate_log_by_size(logname, numlogs=5, logsize=1024):
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


def unmangleAPIdata(d):

    """
    Objects come through as arrays with string indices
    myobject = {propertyone:'value1', propertytwo:'value2'}

    will come through as:

    {myobject[propertyone]:'value1', myobject[propertytwo]:'value2'}

    Arrays also come in a bit funny. An array such as:

    myarray = ['stuff', 'things', 'otherthings']

    comes through as:

    myarray[] = ['stuff','things','otherthings']

    2D arrays come through as :


    An array of objects comes through as :

    somevariable[0][key]
    somevariable[0][anotherkey]
    somevariable[1][key]
    somevariable[1][anotherkey]

    original
    {'username': 'creese',

    So no array of unnamed objects, or you get this:

    'arrayofobjects[0][things]': 'thingsvalue'
    'arrayofobjects[1][things]': 'thingsvalue',
    'arrayofobjects[2][things]': 'thingsvalue',
    'arrayofobjects[0][stuff]': 'stuffvalue', '
    'arrayofobjects[1][stuff]': 'stuffvalue',
    'arrayofobjects[2][stuff]': 'stuffvalue',

    var objwitharrays = {array1: ['blurg','blurg2'], array2: ['blurg11', 'blurg12']}

    'objwitharray[array1][]': ['blurg', 'blurg2'],
    'objwitharray[array2][]': ['blurg11', 'blurg12']}

    'twodlist[0][]': ['blurg', 'blurg2'],
    'twodlist[1][]': ['blurg11', 'blurg12'],

    'myobject[stuff]': 'stuffvalue',
    'myobject[things]': 'thingsvalue',

    'alist[]': ['blurg', 'blurg2'],

    ld
    {'username': 'creese', 'pathalias': 'iiinventory', 'myobject': {'things': 'thingsvalue', 'stuff': 'stuffvalue'}, 'url': '/wsgiinventory', 'arrayofobjects': {'1': 'stuffvalue', '0': 'stuffvalue', '2': 'stuffvalue'}, 'alist': ['blurg', 'blurg2'], 'objwitharray[array2]': ['blurg11', 'blurg12'], 'start': '0', 'twodlist[0]': ['blurg', 'blurg2'], 'twodlist[1]': ['blurg11', 'blurg12'], 'action': 'addeditorderpart', 'objwitharray[array1]': ['blurg', 'blurg2'], 'hpass': '28229485665f96e033333c22c3bdb508daefca17'}

    Strangely, if an array only has one element, it comes through as myarray, not myarray[]. So if we must use arrays,
    we typically push a sacrificial element to ensure they come through correctly. Now, however, because we are going
    to prune off the '[]', we can test for type. If we don't find an array, we can put it into one.
    """

    unmangled = {}
    for key in d:
        value = d[key] # Python3 compatibility
        # print(key) + ': ' + str(value)
        # if last two characters are '[]' we have an array

        if key[-2:] == '[]':
            # value is list.
            # Could have single item though
            if isinstance(value, list):
                assignvalue = value
            else:
                assignvalue = [value]

            # print(assignvalue)
            # Now check to see if this is part of a 2d list or a dict.
            # The way we are doing this means you should not allow your dict keys to be parsed into integers
            # Also don't use brackets in your keys. Common sense. I think?

            key = key[:-2]
            # print('pruned key: ' + key)

            if key[-1] == ']':
                secondindex = key.split('[')[1].split(']')[0]
                firstindex = key.split('[')[0]
                # print('** Dict' )

                if firstindex not in unmangled:
                    unmangled[firstindex] = {}

                unmangled[firstindex][secondindex]=assignvalue
            else:
                unmangled[key]=assignvalue

        # This should really be extended to arbitrary list size. For now it only goes to dimension two.

        elif key.find('[') > 0 and key.find(']') > 0:
            print('key')
            print(key)
            valuename = key.split('[')[0]
            firstkey = key.split('[')[1].split(']')[0]

            print(valuename)
            print('firstkey')
            print(firstkey)

            print(key.split(']')[1:])
            remainder = ''.join((key.split(']')[1:]))
            print('remainder')
            print(remainder)

            if remainder.find('[') >= 0:

                secondkey = remainder.split('[')[1]
                print('secondkey')
                print(secondkey)
                if valuename not in unmangled:
                    unmangled[valuename] = {}

                if firstkey not in unmangled[valuename]:
                    unmangled[valuename][firstkey] = {}

                unmangled[valuename][firstkey][secondkey] = value
            else:
                if valuename not in unmangled:
                    unmangled[valuename] = {}

                unmangled[valuename][firstkey] = value

            print(unmangled)

        else:
            unmangled[key] = value


    print('******')

    # Now go through the dicts and see if they appear to be arrays:
    for itemkey in unmangled:
        itemvalue = unmangled[key] #python3 compatibility
        if isinstance(itemvalue, dict):
            print('is dict')
            islist = True
            # test to see if they are integers and non-duplicates
            integerkeys = []
            for valuekey, valuevalue in itemvalue.iteritems():
                # must resolve into integer
                try:
                    integerkeys.append(int(valuekey))
                except:
                    islist = False
                    break

            # Check for duplicates
            if len(integerkeys) != len(set(integerkeys)):
                islist = False

            # Convert itemvalue to list
            if islist:
                sortedkeys = sorted(itemvalue, key=lambda key: float(key))
                thelist =[]
                for key in sortedkeys:
                    print(key)
                    thelist.append(itemvalue[key])
                del unmangled[itemkey]
                unmangled[itemkey] = thelist



        # elif key.find('[') > 0 and key.find(']') > 0:
        #     objname = key.split('[')[0]
        #     objkey = key.split('[')[1].split(']')[0]
        #     if objname in unmangled:
        #         unmangled[objname][objkey] = value
        #     else:
        #         unmangled[objname] = {objkey:value}
        # else:
        #     unmangled[key]=value

    return unmangled


def insertuser(database, username, password, salt, **kwargs):

    from iiutilities import dblib, datalib
    entry = {'name':username,'password':password, 'email':'','accesskeywords':'','authlevel':1,'temp':'','admin':0}
    entry.update(kwargs)

    # entries = [{'name': 'creese', 'password': 'mydata', 'email': 'colin.reese@interfaceinnovations.org',
    #             'accesskeywords': 'iiinventory,demo', 'authlevel': 5, 'temp': '', 'admin': 1},
    #            {'name': 'iwalker', 'password': 'iwalker', 'email': 'colin.reese@interfaceinnovations.org',
    #             'accesskeywords': 'demo', 'authlevel': 4, 'temp': '', 'admin': 0},
    #            {'name': 'demo', 'password': 'demo', 'email': 'info@interfaceinnovations.org',
    #             'accesskeywords': 'demo', 'authlevel': 2, 'temp': '', 'admin': 0},
    #            {'name': 'mbertram', 'password': 'mbertram', 'email': 'info@interfaceinnovations.org',
    #             'accesskeywords': 'demo', 'authlevel': 2, 'temp': '', 'admin': 0}]

    existingentries = dblib.readalldbrows(database, 'users')
    usercount = len(existingentries)
    existingindices = [existingentry['id'] for existingentry in existingentries]
    existingnames = [existingentry['id'] for existingentry in existingentries]

    print('EXISTING ENTRIES:')
    print(existingentries)

    newindex = usercount+1
    while newindex in existingindices:
        newindex += 1

    table = 'users'

    hashedentry = datalib.gethashedentry(entry['name'], entry['password'], salt=salt)


    query = dblib.makesqliteinsert(table, [newindex, entry['name'], hashedentry, entry['email'],
                                                    entry['accesskeywords'], entry['authlevel'], '',
                                                    entry['admin']])

    print(database)
    print(salt)
    print(query)
    dblib.sqlitequery(database, query)


def parsekeys(key):
    import re

    depth = key.count('[')
    depth2 = key.count(']')

    if depth != depth2:
        # print('we have a depth calculation problem with key ' + key)
        return None

    # print ('depth is ' + str(depth) + ' for key ' + key)
    if depth > 0:
        indices = re.findall('\[(.*?)\]', key)
        # print('indices:')
        # print (indices)

        islist = []
        for index in indices:
            # Empty index means list, i.e. []
            if not index:
                islist.append(True)
            else:
                try:
                    anindex = int(index)
                except:
                    islist.append(False)
                else:
                    islist.append(True)

        # If index is empty, we got a level 1 list, e.g. partids[]
        if indices[0]:
            root=key[0:key.index(indices[0])-1]
        else:
            root=key[0:key.index('[')]
    else:
        indices=[]
        root=key
        islist = []
    # print('root')
    # print(root)

    return({'root':root,'depth':depth,'indices':indices, 'islist':islist})


def testunmangle():
    sampledict = {
        'paneldesc[paneltype]':'brewpanel',
        'paneldesc[pumps][0][controltype]': 'none',
        'paneldesc[pumps][0][name]':'HLT Pump',
        'paneldesc[pumps][0][size]':'1HP',
        'paneldesc[pumps][1][controltype]':'none',
        'paneldesc[pumps][1][name]':'MLT Pump',
        'paneldesc[pumps][1][size]':'none',
        'paneldesc[pumps][2][controltype]':'none',
        'paneldesc[pumps][2][name]':'Kettle Pump',
        'paneldesc[pumps][2][size]':'none',
        'paneldesc[pumps][3][contr]':'none',
        'paneldesc[pumps][3][name]':'Other Pu',
        'paneldesc[vessels][0][lowlevel]':'none',
        'paneldesc[vessels][0][name]':'HLT',
        'paneldesc[vessels][1][con]':'monitor',
        'paneldesc[vessels][1][highlevel]':'none',
        'paneldesc[vessels][1][lowlevel]':'none',
        'paneldesc[vessels][1][name]':'MLT',
        'paneldesc[vessels][2][controltype]':'monitor',
        'paneldesc[vessels][2][highlevel]':'tuningforkwithtimer',
        'paneldesc[vessels][2][lowlevel]':'none',
        'paneldesc[vessels][2][name]':'Kettle',
        'partids[]':['value, anothervalue, yetanothervalue'],
        # 'partids[someshit][]':'value, anothervalue, yetanothervalue',
        'recalc':'true'
    }
    print(sampledict)
    print(newunmangle(sampledict))


def newunmangle(d):

    # NB this will barf if you send in a dict key with the same value as a list, e.g.
    # mydict['key'] = 'some value'
    # mydict['key'][0] = 'some value'

    # Also need to account for empty index list, e.g. partids[]. This will be list=True, index=''
    # This is only currently done for first level ...*[]:

    unmangled = {}
    for key in d:
        value = d[key]

        keyassess = parsekeys(key)
        # print(keyassess)
        if keyassess['depth'] == 0:
            unmangled[keyassess['root']] = value


        # """ Test FUNCTION for arbitrary depth """
        #
        # depth = keyassess['depth']
        # if keyassess['root'] not in unmangled:
        #
        #     unmangled[keyassess['root']] = {}
        #     root_dict = unmangled[keyassess['root']]
        #
        #     for index in range(depth-1):
        #         root_dict[keyassess['indices'][index]] = {}
        #         root_dict = root_dict[keyassess['indices'][index]]
        #
        #
        # """ End test function  """

        elif keyassess['depth'] == 1:
            if keyassess['root'] not in unmangled:
                unmangled[keyassess['root']] = {}

            if keyassess['indices'][0] in unmangled[keyassess['root']]:
                print('we appear to be overwriting something at depth 1: ')
                print(keyassess['indices'][0] + ' already exists in unmangled key ' + keyassess['root'])
                print('already existing value is ' + unmangled[keyassess['root']][keyassess['indices'][0]] + ', new value is ' + value)

            if keyassess['indices'][0]:
                unmangled[keyassess['root']][keyassess['indices'][0]] = value
            else:   # Empty index = list
                if isinstance(value, list):
                    unmangled[keyassess['root']] = value
                else:
                    unmangled[keyassess['root']] = [value]

        elif keyassess['depth'] == 2:
            if keyassess['root'] not in unmangled:
                unmangled[keyassess['root']] = {}
                unmangled[keyassess['root']][keyassess['indices'][0]] = {}

            elif keyassess['indices'][0] not in unmangled[keyassess['root']]:
                unmangled[keyassess['root']][keyassess['indices'][0]] = {}

            if keyassess['indices'][1] in unmangled[keyassess['root']][keyassess['indices'][0]]:
                print('we appear to be overwriting something at depth 2: ' + keyassess['indices'][1] + ', value: ' + value)

            if keyassess['indices'][1]:
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]] = value
            else:   # Empty index is list
                if isinstance(value, list):
                    unmangled[keyassess['root']][keyassess['indices'][0]] = value
                else:
                    unmangled[keyassess['root']][keyassess['indices'][0]] = [value]

        elif keyassess['depth'] == 3:
            if keyassess['root'] not in unmangled:
                # print('root not in unmangled')
                unmangled[keyassess['root']] = {}
                unmangled[keyassess['root']][keyassess['indices'][0]] = {}
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]] = {}

            elif keyassess['indices'][0] not in unmangled[keyassess['root']]:
                # print('index 0 not in root')
                unmangled[keyassess['root']][keyassess['indices'][0]] = {}
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]] = {}

            elif keyassess['indices'][1] not in unmangled[keyassess['root']][keyassess['indices'][0]]:
                # print('index 1 not in root 0')
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]] = {}

            elif keyassess['indices'][2] not in unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]]:
                # print('index 2 not in index 0 1 ')
                pass

            if keyassess['indices'][2] in unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]]:
                print('we appear to be overwriting something for depth 3: ' + keyassess['indices'][1] + ', value: ' + value)

            if keyassess['indices'][2]:
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]][keyassess['indices'][2]] = value
            else:       # Empty index is list
                unmangled[keyassess['root']][keyassess['indices'][0]][keyassess['indices'][1]] = value



    reducedicttolist(unmangled)
    # print(' ** DONE **')
    return unmangled


def reducedicttolist(mydict):
    """
    This function recursively reduces dictionaries with integer keys to lists.
    This is especially useful for unmangling data that comes through with the integer indices as strings,
    in wsgi calls.
    """

    allintegers = True
    for key in mydict:
        value = mydict[key]
        if isinstance(value, dict):
            # recursive call
            returnvalue = reducedicttolist(value)
            mydict[key] = returnvalue

    for key in mydict:
        value = mydict[key]
        try:
            int(value)
        except:
            allintegers=False

    if allintegers:
        returnlist = []
        sortedkeys = sorted(mydict, key=lambda key: float(key))
        for key in sortedkeys:
            returnlist.append(mydict[key])
        return returnlist
    else:
        return mydict


def killprocbyname(name):
    import subprocess
    try:
        result = subprocess.check_output(['pgrep','hamachi'])
    except:
        # Error thrown means hamachi is not running
        print('catching error')
    else:
        split = result.split('\n')
        # print(split)
        for pid in split:
            if pid:
                # print(pid)
                subprocess.call(['kill', '-9', str(pid.strip())])
    return


def log(logfile, message, reqloglevel=1, currloglevel=1):
    # Allow passing None for logfile
    if logfile:
        from iiutilities.datalib import gettimestring
        if currloglevel >= reqloglevel:
            logfile = open(logfile, 'a')
            logfile.writelines([gettimestring() + ' : ' + message + '\n'])
            logfile.close()
        if currloglevel >= 9:
            print(message)


def writetabletopdf(tabledata, **kwargs):

    output = {}
    if 'fields' in kwargs:
        output['message'] += 'Fields argument found. '
        fields = kwargs['fields']
    else:
        fields = None

    output = {}
    try:
        import reportlab
    except ImportError:
        output['message'] += "You do not have reportlab installed. You need to do that. "
        output['status'] = 1
        return output

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, landscape

    c = canvas.Canvas(kwargs['outputfile'], pagesize=letter)

    ystart = 750
    xstart = 50
    charwidth = 4
    colwidths = []
    yrowoffset = 15

    # Do header row
    if not fields:
        drawstring = ''
        for key in tabledata[0]:
            value = tabledata[0][key]
            drawstring += '| ' + key + ' |'
            length = float(len(key) + 4) * charwidth
            colwidths.append(length)


    else:
        # Get these in the right order.
        drawstring = ''
        for key in fields:
            if key in tabledata[0]:
                drawstring += '| ' + key + ' |'
                length = float(len(key) + 4) * charwidth
                colwidths.append(length)

        c.drawString(xstart, ystart, drawstring)
    yoffset = -yrowoffset
    for row in tabledata:
        if not fields:
            pass
        else:
            # Get these in the right order.
            drawstring = ''
            for key in fields:
                if key in row:
                    drawstring += '  ' + row[key] + '  '

        c.drawString(xstart, ystart+yoffset, drawstring)
        yoffset -= yrowoffset
    # rowspacing = 15
    # for rowindex, row in enumerate(tabledata):
    #
    #     for colindex, key, value in enumerate(row.iteritems()):
    #         c.drawString(100,750,value)

    c.save()
    return output


def writetextdoctopdf(text, **kwargs):

    output = {}
    try:
        import reportlab
    except ImportError:
        output['message'] += "You do not have reportlab installed. You need to do that. "
        output['status'] = 1
        return output

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.testutils import setOutDir,makeSuiteForClasses, outputfile, printLocation
    from reportlab.platypus import Paragraph, SimpleDocTemplate, XBox, Indenter, XPreformatted
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import red, black, navy, white, green
    from reportlab.lib.randomtext import randomText
    from reportlab.rl_config import defaultPageSize

    styNormal = ParagraphStyle('normal')

    styIndent1 = ParagraphStyle('normal', leftIndent=10)

    body = []

    for index,item in enumerate(text.split('\n')):
        tabs = item.count('\t')
        thisStyle = ParagraphStyle('normal', leftIndent=10*tabs)
        body.append(Paragraph(item, thisStyle))

    body.append(Paragraph("""<para>\n\tThis has newlines and tabs on the front but inside the para tag</para>""", styNormal))
    doc = SimpleDocTemplate(kwargs['outputfile'])
    # doc.build(body, onFirstPage=formatted_page, onLaterPages=formatted_page)
    doc.build(body)

    return output


def writedbtabletopdf(**kwargs):

    output = {'status':0,'message':''}
    requiredarguments = ['database', 'tablename', 'outputfile']
    for argument in requiredarguments:
        if argument not in kwargs:
            output['message'] += argument + ' argument required. Exiting. '
            output['status'] = 1
            return output

    from iiutilities import dblib

    tabledata = dblib.readalldbrows(kwargs['database'], kwargs['tablename'])

    if tabledata:

        columnames=[]
        for key in tabledata[0]:
            columnames.append(key)

    else:
        output['message'] += 'No tabledata retrieved (Error or empty table). '
        output['status'] = 1
        return output

    returnstatus = writetabletopdf(tabledata)

    output['message'] += 'Routine finished. '
    output['status'] = returnstatus
    return output


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

        if self.recipient.find(',') >=0:
            self.recipients = self.recipient.split(',')
        else:
            self.recipients = [self.recipient]

    def send(self):
        import smtplib

        headers = ['From:' + self.sender,
                  'Subject:' + self.subject,
                  'To:' + self.recipient,
                  'MIME-Version: 1.0',
                  'Content-Type: text/plain']
        headers = '\r\n'.join(headers)

        session = smtplib.SMTP(self.server, self.port)

        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.login, self.password)
        for recipient in self.recipients:
            if recipient:
                session.sendmail(self.sender, recipient.strip(), headers + '\r\n\r\n' + self.message)
        session.quit()


def findprocstatuses(procstofind):
    import subprocess
    statuses = []
    for proc in procstofind:
        # print(proc)
        status = False
        try:
            result = subprocess.check_output(['pgrep','-fc',proc])
            # print(result)
        except:
            # print('ERROR')
            pass
        else:
            if int(result) > 0:
                # print("FOUND")
                status = True
            else:
                pass
                # print("NOT FOUND")
        statuses.append(status)
    # print(statuses)
    return statuses


def jsontodict(jsonstring):
    splits = jsonstring.split(',')
    outputdict = {}
    for split in splits:
        try:
            itemsplit = split.split(':')
        except:
            continue
        else:
            if len(itemsplit) == 2:
                outputdict[itemsplit[0].strip()] = itemsplit[1].strip()
            else:
                pass

    return outputdict


def get_directory_listing(directory):

    from os import walk

    # returns on first, so not recursive
    for (dirpath, dirnames, filenames) in walk(directory):
        return {'dirnames':dirnames, 'filenames':filenames}