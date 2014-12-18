#!/usr/bin/env python

# do this stuff to access the pilib for sqlite
import os, sys, inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def write(message, port='/dev/ttyAMA0', baudrate=115200, timeout=1):
    import serial
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    ser.write(message)


def monitor(port='/dev/ttyAMA0', baudrate=115200, timeout=1, checkstatus=True):
    import serial
    import cupid.pilib as pilib
    from time import mktime, localtime

    data = []

    if checkstatus:
        systemstatus = pilib.readonedbrow(pilib.controldatabase, 'systemstatus')[0]
        runhandler = systemstatus['serialhandlerenabled']
        checktime = mktime(localtime())
        checkfrequency = 15  # seconds
        if runhandler:
           pilib.writedatedlogmsg(pilib.iolog, "Starting monitoring of serial port", 1, pilib.iologlevel)
        else:
            pilib.writedatedlogmsg(pilib.iolog, "Not starting monitoring of serial port. How did I get here?", 1, pilib.iologlevel)
    else:
        runhandler = True

    if runhandler:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        print("Monitoring serial port " + ser.name)
    else:
        print('not monitoring serial port ')
    while runhandler:
        ch = ser.read(1)
        if len(ch) == 0:
            # rec'd nothing print all
            if len(data) > 0:
                s = ''
                for x in data:
                    s += '%s' % x # ord(x)

                # Here for diagnostics
                # print '%s [len = %d]' % (s, len(data))

                # now process data
                # print(s)
                try:
                    datadicts, messages = processserialdata(s)
                except IOError:
                    print('error processing message')
                else:
                    for datadict, message in zip(datadicts, messages):
                        print("datadict: ")
                        print(datadict)
                        print("message: ")
                        print(message.strip())
                        # try:
                        statusresult = processremotedata(datadict, message)
                        # except:
                        #     print('error processing returned datadict, message:')
                            # print(message)
                        # else:
                        #     print("message parse was successful")
                        #     print(message)

            data = []
        else:
            data.append(ch)
        if checkstatus:
            thetime = mktime(localtime())
            if thetime-checktime > checkfrequency:
                print('checking control status')
                systemstatus = pilib.readonedbrow(pilib.controldatabase, 'systemstatus')[0]
                runserialhandler = systemstatus['serialhandlerenabled']
                if runserialhandler:
                    checktime = thetime
                    pilib.writedatedlogmsg(pilib.iolog, 'Continuing serialhandler based on status check',3,pilib.iologlevel)
                else:
                    runhandler=False
                    pilib.writedatedlogmsg(pilib.iolog, 'Aborting serialhandler based on status check',3,pilib.iologlevel)


def processserialdata(data):
    from cupid.pilib import parseoptions
    datadicts = []
    messages = []
    # try:
    # Break into chunks
    split1 = data.strip().split('BEGIN RECEIVED')
    for split in split1:
        if split.find('END RECEIVED') >= 0:
            message = split.split('END RECEIVED')[0]
            print(message)
            messages.append(message.strip())
            try:
                datadict = parseoptions(message)
            except:
                print('error parsing message: ' + message)
            else:
                print(datadict)
                datadicts.append(datadict)
    # except:
    #     print('there was an error processing the message')
    #     return
    # else:
    return datadicts, messages


def processremotedata(datadict, stringmessage):
    import cupid.pilib as pilib
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
        if 'ioval' in datadict:
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
            # {chan:name,sp:XXX.XXX,pv:XXX.XXX,act:XXX.XXX}
            pass
        elif 'scalevalue' in datadict:
            pass
        if runquery:
            print('running query')
            print(stringmessage.strip())
            deletequery = pilib.makedeletesinglevaluequery('remotes', {'conditionnames': ['nodeid', 'keyvalue', 'keyvaluename'], 'conditionvalues': [nodeid ,keyvalue, keyvaluename]})
            insertquery = pilib.makesqliteinsert('remotes',  [nodeid, msgtype, keyvaluename, keyvalue, stringmessage.replace('\x00', ''), pilib.gettimestring()], ['nodeid', 'msgtype', 'keyvaluename', 'keyvalue', 'data', 'time'])
            querylist.append(deletequery)
            querylist.append(insertquery)
            print(querylist)
            pilib.sqlitemultquery(pilib.controldatabase, querylist)

            return
        else:
            print('not running query')

if __name__ == '__main__':
    monitor(checkstatus=False)
    # monitor()