#!/usr/bin/python3

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


# Need to backward compatible this for Pi2 based on hardware version
def write(message, port=None, baudrate=115200, timeout=1):

    if not port:
        print('NO PORT SPECIFIED')
        return None
    else:
        import serial
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        ser.write(message)


def getsystemserialport():
    from iiutilities.dblib import getsinglevalue
    from iiutilities.utility import log as mylog
    from cupid.pilib import dirs
    from iiutilities import dblib
    system_db = dblib.sqliteDatabase(dirs.dbs.system)

    port = '/dev/ttyAMA0'
    versions = system_db.read_table('versions')

    try:
        versions = system_db.read_table('versions')
        hw_version = ''
        for version in versions:
            print(version['item'])
            if version['item'] == 'versionname':
                print(version)
                hw_version = version['version']
    except:
        mylog(dirs.dbs.system, 'Error retrieving hardware version in serial monitor. Reverting to /dev/tty/AMA0')
        print('Error retrieving hardware version in serial monitor. Reverting to /dev/tty/AMA0')
    else:
        print(hw_version, port)

        if hw_version in ['RPi 3 Model B', 'Pi 3 Model B']:
            port = '/dev/ttyS0'

    return port


def monitor(port=None, baudrate=115200, timeout=1, checkstatus=True, printmessages=False):

    if not port:
        port = getsystemserialport()
    import serial
    import cupid.pilib as pilib
    from iiutilities import datalib, dblib
    from iiutilities import utility
    from time import mktime, localtime
    from time import sleep

    motes_db = dblib.sqliteDatabase(pilib.dirs.dbs.motes)
    control_db = dblib.sqliteDatabase(pilib.dirs.dbs.control)
    system_db = dblib.sqliteDatabase(pilib.dirs.dbs.system)

    data = []

    stringmessage = ''
    seriallog = True
    if seriallog:
        print('serial logging is enabled.')
        logfile = open(pilib.dirs.logs.serial, 'a', 1)
        logfile.write('\n' + datalib.gettimestring() + ": Initializing serial log\n")

    if checkstatus:
        systemstatus =system_db.read_table_row('systemstatus')[0]
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
                if len(data) > 1:   # This will avoid processing endline characters and other trash.
                    s = ''
                    for x in data:
                        s += '%s' % x # ord(x)

                    # clear data

                    data = []
                    # Here for diagnostics
                    # print '%s [len = %d]' % (s, len(data))

                    # now process data
                    # print(s)
                    # print(s.split('\n'))
                    try:
                        if (printmessages):
                            print('*************** processing datadict')
                        # print('processing data of length ' + str(len(data)))
                        datadicts, messages = processserialdata(s)
                        # print('ALL MY DATADICTS (length of ' + str(len(datadicts)) + ')')
                        # print(datadicts)
                        # print('END OF DICTS')
                    except IOError:
                        print('error processing message')
                    except Exception as ex:
                        template = "An exception of type {0} occured (line 99). Arguments:\n{1!r}"
                        message = template.format(type(ex).__name__, ex.args)
                        print('exception: ')
                        print(message)
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
                                    lograwmessages(message)

                                motes_db.size_table('read', **{'size':1000})
                                try:
                                    processremotedata(datadict, message)
                                except Exception as ex:
                                    template = "An exception of type {0} occured  in process remote data. Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print(message)

                            else:
                                if message:
                                    print('message: ')
                                    print(message)

                            # Log message
                            if seriallog:
                                try:
                                    logfile.write(datalib.gettimestring() + ' : ' + message + '\n')
                                except Exception as e:
                                    template = "An exception of type {0} occured (line 142). Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print(message)

                else:
                    # no data, let's see if we should send message
                    # print('no data, try sending')
                    pass

                # print('CLEARING DATA !!!')
                data = []
                # try:
                #     utility.log(pilib.dirs.logs.serial, "Attempting send routine", 4, pilib.loglevels.serial)
                # except Exception as e:
                #     template = "An exception of type {0} occured while doing some serial logging. Arguments:\n{1!r}"
                #     message = template.format(type(ex).__name__, ex.args)
                #     print message


                # See if there are messages to send.
                # print('LET US TRY SEND HANDLER')
                try:
                    runsendhandler(ser)
                except Exception as e:
                    template = "An exception of type {0} occured in runsendhandler (line 142). Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    print(message)
                    utility.log(pilib.dirs.logs.serial, "Error in send routine: " + message, 1, 1)
                # print('SEND HANDLER DONE')

                #
                #     template = "An exception of type {0} occured. Arguments:\n{1!r}"
                #     message = template.format(type(ex).__name__, ex.args)
                #     pilib.log(pilib.dirs.logs.serial, message, 1, 1)


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

    motes_db = dblib.sqliteDatabase(pilib.dirs.dbs.motes)

    try:
        last_queued_message = motes_db.get_first_time_row('queued', 'queuedtime')
    except IndexError:
        # no rows
        # print('we have an error getting a queued message. Could be just no message.')
        pass
    else:
        utility.log(pilib.dirs.logs.serial, 'Sending serial message: ' + last_queued_message['message'], 1, 1)
        try:
            # print('going to send message:')
            # print(lastqueuedmessage['message'])
            ser.write(last_queued_message['message'].encode())
            # sendserialmessage(ser, lastqueuedmessage['message'])
        except:
             utility.log(pilib.dirs.logs.serial, 'Error sending message', 1, 1)
        else:
            utility.log(pilib.dirs.logs.serial, 'Success sending message', 1, 1)

            conditionnames = ['queuedtime', 'message']
            conditionvalues = [last_queued_message['queuedtime'], last_queued_message['message']]
            delquery = dblib.makedeletesinglevaluequery('queued', {'conditionnames':conditionnames, 'conditionvalues':conditionvalues})
            dblib.sqlitequery(pilib.dirs.dbs.motes, delquery)
            dblib.sqliteinsertsingle(pilib.dirs.dbs.motes, 'sent', [last_queued_message['queuedtime'], datalib.gettimestring(), last_queued_message['message']])
            dblib.size_sqlite_table(pilib.dirs.dbs.motes, 'sent', 1000)
    return


def sendserialmessage(serobject, message):
    serobject.write(message.encode())


def processserialdata(data):
    from iiutilities.datalib import parseoptions
    datadicts = []
    messages = []
    # try:
    # Break into chunks

    print('processing data: ')
    print(data)
    print('end data')
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
    from iiutilities.dblib import sqliteinsertsingle, size_sqlite_table
    # try:
    strmessage = str(message).replace('\x00','').strip()
    if strmessage not in ['END RECEIVED', 'BEGIN RECEIVED']:
    # print('publishing message: ' + strmessage)
    # print(repr(strmessage))
        sqliteinsertsingle(dirs.dbs.motes, 'read', [gettimestring(), strmessage])
        size_sqlite_table(dirs.dbs.motes, 'read', size=1000)
    # sqliteinsertsingle(dirs.dbs.motes, 'readmessages', [gettimestring(), 'nodeid:2,chan:02,sv:070.000,pv:071.000,RX_RSSI:_57'])
    # except:
    #     print('it did not go ok')
    #     return {'status':1, 'message':'query error'}
    # else:
    #     print('it went ok')
    #     return{'status':0, 'message':'ok' }


"""
This function processes remote data as it is read. This is reserved for things that should happen synchronously.
Keep in mind, however, that we are trying to read data in real-time within the limits of the UART, so we should
put off all time-consuming activities until later if at all possible to avoid missing messages due to buffer
limitations
"""


def processremotedata(datadict, stringmessage):
    import cupid.pilib as pilib
    from iiutilities import dblib, datalib, utility

    control_db = dblib.sqliteDatabase(pilib.dirs.dbs.control)
    motes_db = dblib.sqliteDatabase(pilib.dirs.dbs.motes)
    log_db = dblib.sqliteDatabase(pilib.dirs.dbs.log)

    print('PROCESSING REMOTE DATA')
    print(datadict)
    if 'nodeid' in datadict:

        """
        We are going to search for keywords. Message type will not be explicitly declared so
        as not to waste precious message space in transmission. Or we could tack these on in
        the gateway, but we won't yet.
        """

        """
        Then we have to construct a query where we will replace a unique item
        This will take the form :
          update or replace in remotes where nodeid=3 and msgtype='iovalue' and iopin=3
          update or repalce in remotes where nodeid=2 and msgtype='owdev' and owrom='28XXXXXXXXXXXXXX'
                      (and later which IO on this device)


          update or replace in remotes where nodeid=2 and msgtype='chanstat' channum=1
        """
        """
                      (need to see if all channel variables can be fit into one message:
                      channum, sv,pv,mode,state
        """
        runquery = False
        nodeid = datadict['nodeid']

        # We are going to use this to filter datadict entries into remote channels. More later.
        allowedfieldnames = ['nodeid','sv','pv','htcool','run','treg','prop','p','i','d']

        control_db = dblib.sqliteDatabase(pilib.dirs.dbs.control)

        # Command responses, including value requests


        # Node status values

        value_types = ['vbat', 'vout', 'autoboot', 'output', 'batterylow', 'sigbootok', 'sigshutoff']
        # sprintf(buff, "nodeid:1,vbat:%01d.%02d,vout:%01d.%02d,autoboot:%01d,output:%01d", wholevoltage, fractvoltage,
        #        wholevoltage2, fractvoltage2, autobootenabled, outputstate);
        # Serial.println(buff);
        # sprintf(buff, "batterylow:%01d,sigbootok:%01d,sigshutoff:%01d", batteryLow, bootok, sigshutoff);

        for value_type in value_types:
            if value_type in datadict:

                insert = {
                    'nodeid': nodeid,
                    'msgtype': 'nodestatus',
                    'keyvaluename': value_type,
                    'keyvalue': datadict[value_type],
                    'data': stringmessage.replace('\x00', ''),
                    'time': datalib.gettimestring()
                }
                control_db.query(dblib.makedeletesinglevaluequery('remotes',
                                                                        {'conditionnames': ['nodeid', 'keyvaluename'],
                                                                         'conditionvalues': [nodeid, insert['keyvaluename']]}), queue=True)
                control_db.insert('remotes', insert, queue=True)

        # Node system events

        if 'event' in datadict:
            insert = {
                'nodeid': nodeid,
                'msgtype': 'event',
                'keyvaluename': datadict['event'],
                'keyvalue': datalib.gettimestring(),
                'data': stringmessage.replace('\x00', ''),
                'time': datalib.gettimestring()
            }
            control_db.query(dblib.makedeletesinglevaluequery('remotes',
                                                                    {'conditionnames': ['nodeid', 'keyvaluename'],
                                                                     'conditionvalues': [nodeid, insert['keyvaluename']]}),
                                                                        queue=True)
            control_db.insert('remotes', insert, queue=True)

            # Also queue an email message to cupid_status
            import socket
            hostname = socket.gethostname()

            message = 'CuPID system event : {} \r\n\r\n'.format(insert['keyvaluename'])
            notifications_email = 'cupid_status@interfaceinnovations.org'
            subject = 'CuPID : {} : {} '.format(hostname, insert['keyvaluename'])
            notification_database = pilib.cupidDatabase(pilib.dirs.dbs.notifications)
            system_database = pilib.cupidDatabase(pilib.dirs.dbs.system)

            currenttime = datalib.gettimestring()
            notification_database.insert('queued',
                                         {'type': 'email', 'message': message,
                                          'options': 'email:' + notifications_email + ',subject:' + subject,
                                          'queuedtime': currenttime})
            system_database.set_single_value('notifications', 'lastnotification', currenttime, condition="item='boot'")

        if 'cmd' in datadict:
            if datadict['cmd'] == 'lp':
                # Remove command key and process remaining data
                del datadict['cmd']
                motetablename = 'node_' + nodeid + '_status'

                # Create table if it doesn't exist
                motes_db.create_table(motetablename, pilib.schema.mote, queue=True)

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
                            query = dblib.makesqliteinsert(motetablename, [thetime, base + str(index), value])
                            motes_db.query(query, queue=True)
                            # querylist.append(dblib.makesqliteinsert(motetablename, [thetime, base + str(index), value]))
                            index += 1


                    # Update table entry. Each entry has a unique key
                    # updatetime, keyname, data
                    else:
                        motes_db.insert(motetablename, {'time':thetime, 'message':key, 'value':datadict[key]}, queue=True)
                        # print('inserted ' + thetime + ' ' + key + ' ' + datadict[key])

                    if motes_db.queued_queries:
                        motes_db.execute_queue()

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
                control_db.insert()

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
            keyvalue = str(int(datadict['chan']))  # Zeroes bad
            keyvaluename = str(int(datadict['chan']))

            # conditions = '"nodeid"=2 and "msgtype"=\'channel\' and "keyvalue"=\'' + keyvalue + '\'"'

            # Should be able to offer all conditions, but it is not working for some reason, so we will
            # iterate over list to find correct enty

            # Here, get all remote entries for the specific node id
            conditions = '"nodeid"=\'' + datadict['nodeid'] + '\' and "msgtype"=\'channel\''
            chanentries = control_db.read_table('remotes', conditions)

            # parse through to get data from newdata
            newdata = {}
            import string
            printable = set(string.printable)
            for key, value in datadict.iteritems():
                if key not in ['chan','nodeid']:
                    if key in allowedfieldnames:
                        filteredvalue = filter(lambda x: x in printable, value)
                        newdata[key] = filteredvalue

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
            print(deletequery)
            print(addquery)

            control_db.queries([deletequery, addquery])

        elif 'scalevalue' in datadict:
            # TODO : What is this?
            # querylist.append('create table if not exists scalevalues (value float, time string)')
            # querylist.append(dblib.makesqliteinsert('scalevalues', [datadict['scalevalue'], datalib.gettimestring()], ['value', 'time']))
            # log_db.queries(querylist)
            pass

        if control_db.queued_queries:
            control_db.execute_queue()

            return
        else:
            # print('not running query')
            pass
    return

if __name__ == '__main__':
    # Need to include an option for only debug. See other scripts for examples.
    monitor(checkstatus=False, printmessages=True)
    # monitor()