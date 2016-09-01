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

    unmanged
    {'username': 'creese', 'pathalias': 'iiinventory', 'myobject': {'things': 'thingsvalue', 'stuff': 'stuffvalue'}, 'url': '/wsgiinventory', 'arrayofobjects': {'1': 'stuffvalue', '0': 'stuffvalue', '2': 'stuffvalue'}, 'alist': ['blurg', 'blurg2'], 'objwitharray[array2]': ['blurg11', 'blurg12'], 'start': '0', 'twodlist[0]': ['blurg', 'blurg2'], 'twodlist[1]': ['blurg11', 'blurg12'], 'action': 'addeditorderpart', 'objwitharray[array1]': ['blurg', 'blurg2'], 'hpass': '28229485665f96e033333c22c3bdb508daefca17'}

    Strangely, if an array only has one element, it comes through as myarray, not myarray[]. So if we must use arrays,
    we typically push a sacrificial element to ensure they come through correctly. Now, however, because we are going
    to prune off the '[]', we can test for type. If we don't find an array, we can put it into one.
    """

    unmangled = {}
    for key, value in d.iteritems():
        # print(key) + ': ' + str(value)
        # if last two characters are '[]' we have an array

        if key[-2:] == '[]':
            # value is list.
            # Could have single item though
            if isinstance(value, list):
                assignvalue = value
            else:
                assignvalue = [value]

            print(assignvalue)
            # Now check to see if this is part of a 2d list or a dict.
            # The way we are doing this means you should not allow your dict keys to be parsed into integers
            # Also don't use brackets in your keys. Common sense. I think?

            key = key[:-2]
            print('pruned key: ' + key)

            if key[-1] == ']':
                secondindex = key.split('[')[1].split(']')[0]
                firstindex = key.split('[')[0]
                print('** Dict' )

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
    for itemkey, itemvalue in unmangled.iteritems():
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
    from iiutilities.datalib import gettimestring
    if currloglevel >= reqloglevel:
        logfile = open(logfile, 'a')
        logfile.writelines([gettimestring() + ' : ' + message + '\n'])
        logfile.close()


def writetabletopdf(**kwargs):

    output = {'status':0,'message':''}
    requiredarguments = ['database', 'tablename', 'outputfile']
    for argument in requiredarguments:
        if argument not in kwargs:
            output['message'] += argument + ' argument required. Exiting. '
            output['status'] = 1
            return output

    try:
        import reportlab
    except ImportError:
        output['message'] += "You do not have reportlab installed. You need to do that. "
        output['status'] = 1
        return output

    from iiutilities import dblib

    tabledata = dblib.readalldbrows(kwargs['database'], kwargs['tablename'])

    if tabledata:

        columnames=[]
        for key, value in tabledata[0].iteritems():
            columnames.append(key)

    else:
        output['message'] += 'No tabledata retrieved (Error or empty table). '
        output['status'] = 1
        return output

    if 'fields' in kwargs:
        output['message'] += 'Fields argument found. '
        fields = kwargs['fields']
    else:
        fields = None

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
        for key, value in tabledata[0].iteritems():
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

    output['message'] += 'Routine finished. '
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

        session.sendmail(self.sender, self.recipient, headers + '\r\n\r\n' + self.message)
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


def dicttojson(dict):
    jsonentry = ''
    for key, value in dict.iteritems():
        jsonentry += key + ':' + str(value).replace('\x00','') + ','
    jsonentry = jsonentry[:-1]
    return jsonentry