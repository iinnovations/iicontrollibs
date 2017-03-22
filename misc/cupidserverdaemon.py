#!/usr/bin/python


__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import inspect
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from iiutilities import dblib, hamachidaemon
from iiutilities import datalib, utility

hamachidbpath = '/var/www/html/hamachi/data/hamachi.db'


def onlineofflinetobinary(status):
    if status in ['online', 'Online']:
        booleanstatus = 1
    elif status in ['offline', 'Offline']:
        booleanstatus = 0
    else:
        booleanstatus = -1
    return booleanstatus


def updatehamachidatabase(path=hamachidbpath):

    from iiutilities.netfun import gethamachidata
    hamachidata = {}
    hamachidata = gethamachidata()

    # Let's database the stuff
    try:
        prevdb = dblib.getentiredatabase(hamachidbpath, method='allmeta')
    except:
        prevdb = {'data': [], 'tablenames': [], 'dictarray': []}

    '''
    table structure:
        name : hamachi network "Name : ID", e.g. "HomeWork : XXX-XXX-XXX"
        row : name, ID (unique key), online, hamachiip, alldata, options

    '''

    # Go network by network and merge tables. The only thing we are going to take from the
    # existing table is the options field, which will contain monitoring options, etc.
    defaultoptions = 'monitor:0'
    networklist = []

    for index,network in enumerate(hamachidata['networks']):

        netclientlist = []

        # Standard tablename format
        tablename = network['name'] + ' : ' + network['id']

        # Does the same network exist?
        if tablename in prevdb['tablenames']:
            # print('TABLE MATCH')

            # index for client list of existing network
            prevtableindex = prevdb['tablenames'].index(tablename)

            # Now get previous clients for this network
            prevclients = prevdb['data'][prevtableindex]

            # Get a list of client IDs
            prevclientids = []
            for prevclient in prevclients:
                # print(prevclient)
                prevclientids.append(prevclient['id'])

            # Now match and grab options
            for client in hamachidata['clients'][index]:
                # print(client['id'])
                cliententry = {'id':client['id'], 'name':client['name'], 'hamachiip':client['hamachiip'], 'onlinestatus':onlineofflinetobinary(client['onlinestatus']), 'alldata': datalib.dicttojson(client)}
                if client['id'] in prevclientids:
                    # print('CLIENT MATCH')

                    prevclient = prevclients[prevclientids.index(client['id'])]
                    cliententry['options'] = prevclient['options']
                else:
                    cliententry['options'] = defaultoptions
                netclientlist.append(cliententry)


        else:
            for client in hamachidata['clients'][index]:
                cliententry = {'id':client['id'], 'name':client['name'], 'hamachiip':client['hamachiip'], 'onlinestatus':onlineofflinetobinary(client['onlinestatus']), 'alldata': datalib.dicttojson(client), 'options':defaultoptions}

                netclientlist.append(cliententry)

        dblib.dropcreatetexttablefromdict(hamachidbpath, tablename, netclientlist, primarykey='id')

        networklist.append({'name':network['name'], 'id':network['id'], 'clientlist':netclientlist})

    return networklist


def rundaemon():

    import iiutilities.netfun as netfun

    hamachidata = updatehamachidatabase()

    hamachidaemon.generatehamachipage(hamachidata, "/var/www/html/hamachi/hamachilist.html")

    import socket
    hostname = socket.gethostname()

    sendmessage = False
    message = ''

    for network in hamachidata:
        for client in network['clientlist']:
            optionsdict = datalib.parseoptions(client['options'])
            if 'monitor' in optionsdict:
                if optionsdict['monitor'] == '1':
                    pingstats = netfun.pingstatus(client['hamachiip'])

                    if ( pingstats['pingave'] > 1000 or pingstats['pingave'] == 0 ):
                        sendmessage = True
                        message += hostname + ' checked ' + client['name'] + '@' + client['hamachiip'] + ' in network "' + network['name'] + '" and found that it is not online. \r\n'

    if sendmessage:
        from iiutilities.utility import gmail
        subject = hostname + ' hosts report'
        email = 'colin.reese@gmail.com'
        actionmail = gmail(message=message, subject=subject, recipient=email)
        actionmail.send()


# Deprecated
def parseiplist(path='/usr/lib/iicontrollibs/misc/hostschecklist'):
    with open(path) as f:
        lines = f.read().splitlines()

    ipdictlist = []
    for line in lines:
        if line[0] == '#':
            print('skipping ' + line)
        else:
            split = line.split(':')
            ipdictlist.append({'name':split[0].strip(), 'address': split[1].strip()})

    return ipdictlist


if __name__=="__main__":

    rundaemon()