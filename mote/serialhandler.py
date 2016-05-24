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

import cupid.pilib as pilib


def write(message, port='/dev/ttyAMA0', baudrate=115200, timeout=1):
    import serial
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    ser.write(message)


def monitor(port='/dev/ttyAMA0', baudrate=115200, timeout=1, checkstatus=True, printmessages=False):
    import serial
    import cupid.pilib as pilib
    from iiutilities import datalib, dblib
    from iiutilities import utility
    from time import mktime, localtime
    from time import sleep

    data = []

    stringmessage = ''
    seriallog = True
    if seriallog:
        print('serial logging is enabled.')
        logfile = open(pilib.dirs.logs.log, 'a', 1)
        logfile.write('\n' + datalib.gettimestring() + ": Initializing serial log\n")

    if checkstatus:
        systemstatus = dblib.readonedbrow(pilib.dirs.dbs.control, 'systemstatus')[0]
        runhandler = systemstatus['serialhandlerenabled']
        checktime = mktime(localtime())
        checkfrequency = 15  # seconds
        if runhandler:
           utility.log(pilib.dirs.logs.io, "Starting monitoring of serial port", 1, pilib.loglevels.io)
        else:
            utility.log(pilib.dirs.logs.io, "Not starting monitoring of serial port. How did I get here?", 1, pilib.loglevels.io)
    else:
        runhandler = True

    if runhandler:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        print("Monitoring serial port " + ser.name)
    else:
        print('not monitoring serial port ')
    while runhandler:
        # This reading has to happen faster than the messages come, or they will all be stuck together
        try:
            ch = ser.read(1)
            # if ch == '\x0D':
            #     print('carriage return')
            # elif ch == '\x00':
            #     print('null character')

            if len(ch) == 0 or ch == '\x0D':
                # print('LEN ZERO OR END CHAR: PROCESS TIME')

                # rec'd nothing print all
                if len(data) > 0:
                    s = ''
                    for x in data:
                        s += '%s' % x # ord(x)

                    # Here for diagnostics
                    # print '%s [len = %d]' % (s, len(data))

                    # now process data
                    # print(s)
                    # print(s.split('\n'))
                    try:
                        if (printmessages):
                            print('*************** processing datadict')

                        datadicts, messages = processserialdata(s)
                        # print('ALL MY DATADICTS')
                        # print(datadicts)
                        # print('END OF DICTS')
                    except IOError:
                        print('error processing message')
                    except Exception as ex:
                        template = "An exception of type {0} occured. Arguments:\n{1!r}"
                        message = template.format(type(ex).__name__, ex.args)
                        print message
                    else:
                        for datadict, message in zip(datadicts, messages):
                            if datadict:
                                if (printmessages):
                                    print("datadict: ")
                                    print(datadict)
                                # print("message: ")
                                # print(message)

                                publish = False
                                for k in datadict:
                                    # print(k + datadict[k])
                                    if k not in ['nodeid','RX_RSSI']:
                                        pass
                                # if 'cmd' in datadict:
                                publish = True
                                if publish:
                                    if (printmessages):
                                        print('publishing message: ')
                                        print(message)
                                    statusresult = lograwmessages(message)

                                dblib.sizesqlitetable(pilib.dirs.dbs.motes, 'readmessages', 1000)

                                statusresult = processremotedata(datadict, message)
                            else:
                                if message:
                                    print('message: ')
                                    print(message)

                            # Log message
                            if seriallog:
                                try:
                                    logfile.write(datalib.gettimestring() + ' : ' + message + '\n')
                                except Exception as e:
                                    template = "An exception of type {0} occured. Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print message

                else:
                    # no data, let's see if we should send message
                    # print('no data, try sending')
                    pass

                utility.log(pilib.dirs.logs.log, "Attempting send routine", 4, pilib.loglevels.serial)

                # See if there are messages to send.
                try:
                    runsendhandler(ser)
                except Exception as e:
                    utility.log(pilib.dirs.logs.log, "Error in send routine", 1, 1)
                #
                #     template = "An exception of type {0} occured. Arguments:\n{1!r}"
                #     message = template.format(type(ex).__name__, ex.args)
                #     pilib.log(pilib.dirs.logs.log, message, 1, 1)
                #     print message
                data = []

            else:
                # print('DATA NOT ZERO')
                # print(ch)
                data.append(ch)
                stringmessage += str(ch)


            if checkstatus:
                print('checking status')
                thetime = mktime(localtime())
                if thetime-checktime > checkfrequency:
                    print('checking control status')
                    systemstatus = dblib.readonedbrow(pilib.dirs.dbs.control, 'systemstatus')[0]
                    runserialhandler = systemstatus['serialhandlerenabled']
                    if runserialhandler:
                        checktime = thetime
                        utility.log(pilib.dirs.logs.io, 'Continuing serialhandler based on status check', 3, pilib.loglevels.io)
                    else:
                        runhandler=False
                        utility.log(pilib.dirs.logs.io, 'Aborting serialhandler based on status check', 3, pilib.loglevels.io)
        except KeyboardInterrupt:
            print('\n Exiting on keyboard interrupt\n')
            logfile.close()
            return
        except:
            # print('no characters available!')
            sleep(0.5)
        #     return
            #runsendhandler(ser)

    logfile.close()
    ser.close()
    return


def runsendhandler(ser):
    from iiutilities import dblib, datalib
    from iiutilities import utility

    # print('looking for message to send')
    try:
        lastqueuedmessage = dblib.getfirsttimerow(pilib.dirs.dbs.motes, 'queuedmessages', 'queuedtime')[0]
    except IndexError:
        # no rows
        # print('we have an error getting a queued message. Could be just no message.')
        pass
    else:
        utility.log(pilib.dirs.logs.log, 'Sending serial message: ' + lastqueuedmessage['message'], 1, 1)
        try:
            # print('going to send message:')
            # print(lastqueuedmessage['message'])
            ser.write(lastqueuedmessage['message'].encode())
            # sendserialmessage(ser, lastqueuedmessage['message'])
        except:
             utility.log(pilib.dirs.logs.log, 'Error sending message', 1, 1)
        else:
            utility.log(pilib.dirs.logs.log, 'Success sending message', 1, 1)

            conditionnames = ['queuedtime', 'message']
            conditionvalues = [lastqueuedmessage['queuedtime'], lastqueuedmessage['message']]
            delquery = dblib.makedeletesinglevaluequery('queuedmessages', {'conditionnames':conditionnames, 'conditionvalues':conditionvalues})
            dblib.sqlitequery(pilib.dirs.dbs.motes, delquery)
            dblib.sqliteinsertsingle(pilib.dirs.dbs.motes, 'sentmessages', [lastqueuedmessage['queuedtime'], datalib.gettimestring(), lastqueuedmessage['message']])
    return


def sendserialmessage(serobject, message):
    serobject.write(message.encode())


def processserialdata(data):
    from iiutilities.datalib import parseoptions
    datadicts = []
    messages = []
    # try:
    # Break into chunks

    # RF Message (deprecated, all are of serial form below)
    if data.strip().find('BEGIN RECEIVED') > 0:
        split1 = data.strip().split('BEGIN RECEIVED')
        for split in split1:
            if split.find('END RECEIVED') >= 0:
                message = split.split('END RECEIVED')[0].replace('\x00', '')
                # print(message)
                messages.append(message.strip())
                try:
                    datadict = parseoptions(message)
                except:
                    print('error parsing message: ' + message)
                else:
                    # print(datadict)
                    datadicts.append(datadict)
                    messages.append(message)
    # Serial message
    else:
        messagesplit = data.strip().split('\n')
        # print(messagesplit)
        datadicts=[]
        for entry in messagesplit:
            # print(entry)
            dict = parseoptions(entry)
            # print('dict')
            # print(dict)
            if 'node' or 'cmd' in dict:
                datadicts.append(dict)
                messages.append(entry)
    # except:
    #     print('there was an error processing the message')
    #     return
    # else:
    return datadicts, messages


def lograwmessages(message):
    from cupid.pilib import dirs
    from iiutilities.datalib import gettimestring
    from iiutilities.dblib import sqliteinsertsingle
    # try:
    strmessage = str(message).replace('\x00','').strip()
    # print(repr(strmessage))
    sqliteinsertsingle(dirs.dbs.motes, 'readmessages', [gettimestring(), strmessage])
    # sqliteinsertsingle(dirs.dbs.motes, 'readmessages', [gettimestring(), 'nodeid:2,chan:02,sv:070.000,pv:071.000,RX_RSSI:_57'])
    # except:
    #     print('it did not go ok')
    #     return {'status':1, 'message':'query error'}
    # else:
    #     print('it went ok')
    #     return{'status':0, 'message':'ok' }


# THis function processes remote data as it is read. This is reserved for things that should happen synchronously.
# Keep in mind, however, that we are trying to read data in real-time within the limits of the UART, so we should
# put off all time-consuming activities until later if at all possible to avoid missing messages due to buffer
# limitations

def processremotedata(datadict, stringmessage):
    import cupid.pilib as pilib
    from iiutilities import dblib, datalib
    if 'nodeid' in datadict:

        # We are going to search for keywords. Message type will not be explicitly declared so
        # as not to waste precious message space in transmission. Or we could tack these on in
        # the gateway, but we won't yet.

        # Then we have to construct a query where we will replace a unique item
        # This will take the form :
        #   update or replace in remotes where nodeid=3 and msgtype='iovalue' and iopin=3
        #   update or repalce in remotes where nodeid=2 and msgtype='owdev' and owrom='28XXXXXXXXXXXXXX'
        #               (and later which IO on this device)
        #   update or replace in remotes where nodeid=2 and msgtype='chanstat' channum=1
        #               (need to see if all channel variables can be fit into one message:
        #               channum, sv,pv,mode,state
        runquery = False
        nodeid = datadict['nodeid']
        querylist = []

        # Command responses, including value requests
        if 'cmd' in datadict:
            if datadict['cmd'] == 'lp':
                # Remove command key and process remaining data
                del datadict['cmd']
                motetablename = 'node_' + nodeid + '_status'

                # Create table if it doesn't exist
                query = 'create table if not exists \'' + motetablename + '\' ( time text, message text primary key, value text)'
                dblib.sqlitequery(pilib.dirs.dbs.motes, query)

                for key in datadict:
                    thetime = datalib.gettimestring()
                    if key in ['iov', 'iov2', 'iov3', 'pv', 'pv2', 'sv', 'sv2', 'iomd', 'ioen', 'iordf', 'iorpf', 'chen', 'chmd', 'chnf', 'chpf', 'chdb', 'chsv', 'chsv2', 'chpv', 'chpv2']:
                        # We need to process these specially, going back to the original message
                        values = datadict[key]
                        valuelist = values.split('|')
                        print(valuelist)
                        index = 0
                        if key in ['iov', 'iov2', 'iov3']:
                            base = 'iov_'
                            if key == 'iov2':
                                index = 5
                            elif key == 'iov3':
                                index = 9
                        elif key in ['pv', 'pv2']:
                            base = 'pv_'
                            if key == 'pv2':
                                index = 5
                        elif key in ['sv', 'sv2']:
                            base = 'sv_'
                            if key == 'sv2':
                                index = 5
                        else:
                            base = key + '_'

                        querylist = []
                        for value in valuelist:
                            querylist.append(dblib.makesqliteinsert(motetablename, [thetime, base + str(index), value]))
                            index += 1
                        dblib.sqlitemultquery(pilib.dirs.dbs.motes, querylist)

                    # Update table entry. Each entry has a unique key
                    # updatetime, keyname, data
                    else:
                        dblib.sqliteinsertsingle(pilib.dirs.dbs.motes, motetablename, [thetime, key, datadict[key]])
                        print('inserted ' + thetime + ' ' + key + ' ' + datadict[key])

        # This is for values that are reported by the node
        elif 'ioval' in datadict:
            # check to see if entry exists with node and ionum. Need to generalize these.
            # Might make sense to put then into an ID to compare. Other database, compatible?
            # iovalue type message
            try:
                msgtype = 'iovalue'
                keyvalue = datadict['iopin']
                keyvaluename = 'iopin'
            except:
                print('oops')
            else:
                runquery = True

        elif 'owdev' in datadict:
            try:
                msgtype = 'owdev'
                keyvalue = datadict['owrom'][2:]
                keyvaluename = 'owrom'
                if len(keyvalue) != 16:
                    raise NameError('invalid ROM length')
                else:
                    for romcbar in keyvalue:
                        hexchars = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','a','b','c','d','e','f']
                        if romcbar not in hexchars:
                            raise NameError('Invalid ROM hex character')
            except:
                print("oops")
            else:
                runquery = True
        elif 'chan' in datadict:
            # insert or update remotes database value
            # first need to get existing entry if one exists
            msgtype = 'channel'
            keyvalue = str(int(datadict['chan'])) # Zeroes bad
            keyvaluename = str(int(datadict['chan']))

            # conditions = '"nodeid"=2 and "msgtype"=\'channel\' and "keyvalue"=\'' + keyvalue + '\'"'

            # Should be able to offer all conditions, but it is not working for some reason, so we will
            # iterate over list to find correct enty

            # Here, get all remote entries for the specific node id
            conditions = '"nodeid"=\''+ datadict['nodeid'] + '\' and "msgtype"=\'channel\''
            chanentries = dblib.readalldbrows(pilib.dirs.dbs.control, 'remotes', conditions)

            # parse through to get data from newdata
            newdata = {}
            for key, value in datadict.iteritems():
                if key not in ['chan','nodeid']:
                    newdata[key] = value

            updateddata = newdata.copy()

            # This does not take time into account. This should not be an issue, as there should only be one entry
            # Now match entry from node. Here, for example, keyvaluename could be channel, and keyvalue representing the
            # channel or controller on the node.

            for chanentry in chanentries:
                if (str(int(chanentry['keyvalue']))) == keyvalue:
                    # print('I FOUND')

                    # newdata  = {'fakedatatype':'fakedata', 'anotherfakedatatype':'morefakedata'}
                    olddata = datalib.parseoptions(chanentry['data'])

                    olddata.update(updateddata)
                    updateddata = olddata.copy()

                    newqueries = []
                    conditions += ' and "keyvalue"=\'' + keyvalue +"\'"

            # Ok, so here we are. We have either added new data to old data, or we have the new data alone.
            # We take our dictionary and convert it back to json and put it in the text entry

            updatedjsonentry = datalib.dicttojson(updateddata)

            conditions += 'and "keyvalue"=\'' + keyvalue +'\''
            deletequery = dblib.makedeletesinglevaluequery('remotes', conditions)

            # hardcode this for now, should supply valuename list.
            addquery = dblib.makesqliteinsert('remotes', [datadict['nodeid'], 'channel', keyvalue, 'channel', updatedjsonentry, datalib.gettimestring()])

            dblib.sqlitemultquery(pilib.dirs.dbs.control, [deletequery, addquery])


        elif 'scalevalue' in datadict:
            querylist.append('create table if not exists scalevalues (value float, time string)')
            querylist.append(dblib.makesqliteinsert('scalevalues', [datadict['scalevalue'], datalib.gettimestring()], ['value', 'time']))
            dblib.sqlitemultquery(pilib.dirs.dbs.log, querylist)

        if runquery:
            deletequery = dblib.makedeletesinglevaluequery('remotes', {'conditionnames': ['nodeid', 'keyvalue', 'keyvaluename'], 'conditionvalues': [nodeid , keyvalue, keyvaluename]})
            insertquery = dblib.makesqliteinsert('remotes', [nodeid, msgtype, keyvaluename, keyvalue, stringmessage.replace('\x00', ''), datalib.gettimestring()], ['nodeid', 'msgtype', 'keyvaluename', 'keyvalue', 'data', 'time'])
            querylist.append(deletequery)
            querylist.append(insertquery)
            dblib.sqlitemultquery(pilib.dirs.dbs.control, querylist)

            return
        else:
            # print('not running query')
            pass
    return

if __name__ == '__main__':
    monitor(checkstatus=False, printmessages=True)
    # monitor()