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


# This script resets the control databases

"""
Safe DB
"""


def rebuildsafedb(tabledict={'usermeta':True, 'users':True, 'pathaliases':True}):

    """

    System safe database. Contains users and other info that we do not want in the web path.

    """

    from iiutilities import datalib, dblib
    from inventory import inventorylib

    table = 'usermeta'
    if table in tabledict:

        createentries = True
        querylist = ['drop table if exists ' + table]
        querylist.append(
            "create table " + table + " (user text primary key, data text)")

        if createentries:
            querylist.append("insert into " + table + " values('creese','pathalias:iiinventory')")
            querylist.append("insert into " + table + " values('demo','pathalias:demo')")
            querylist.append("insert into " + table + " values('iwalker','pathalias:isaac')")
            querylist.append("insert into " + table + " values('mbertram','pathalias:demo')")

        try:
            print(querylist)
            print(inventorylib.sysvars.dirs.dbs.safe)
            dblib.sqlitemultquery(inventorylib.sysvars.dirs.dbs.safe, querylist)
        except:
            print('ERROR in usermeta query')

    table = 'pathaliases'
    if table in tabledict:
        runquery = True

        createentries = True
        querylist =['drop table if exists ' + table]
        querylist.append(
            "create table " + table + " (alias text primary key, path text)")

        if createentries:
            querylist.append("insert into " + table + " values('iiinventory','iiinventory')")
            querylist.append("insert into " + table + " values('demo','demo')")

        try:
            print(querylist)
            print(inventorylib.sysvars.dirs.dbs.safe)
            dblib.sqlitemultquery(inventorylib.sysvars.dirs.dbs.safe, querylist)
        except:
            print('Error in ' + table + ' query')



    table = 'users'
    if table in tabledict:

        ### No default tables. Create a table as an example

        querylist=['drop table if exists ' + table,
                    "create table " + table + " ( id integer primary key not null, name text unique, password text, " +
                                              "email text, accesskeywords text, authlevel integer default 1, " +
                                              "temp text, admin integer default 0)"]

        addentries = True
        if addentries:
            entries = [{'name': 'creese', 'password': 'mydata', 'email': 'colin.reese@interfaceinnovations.org', 'accesskeywords': 'iiinventory,demo', 'authlevel':5, 'temp': '', 'admin': 1},
                       {'name': 'iwalker', 'password': 'iwalker', 'email': 'colin.reese@interfaceinnovations.org', 'accesskeywords': 'demo', 'authlevel':4, 'temp':'', 'admin': 0},
                       {'name': 'demo', 'password': 'demo', 'email': 'info@interfaceinnovations.org', 'accesskeywords': 'demo', 'authlevel':2, 'temp':'', 'admin': 0},
                       {'name': 'mbertram', 'password': 'mbertram', 'email': 'info@interfaceinnovations.org', 'accesskeywords': 'demo', 'authlevel': 2, 'temp': '', 'admin': 0}]

            index = 1
            for entry in entries:
                hashedentry = datalib.gethashedentry(entry['name'], entry['password'], salt=inventorylib.sysvars.salt)
                querylist.append(dblib.makesqliteinsert(table, [index, entry['name'], hashedentry, entry['email'], entry['accesskeywords'], entry['authlevel'], '', entry['admin']]))
                index += 1

        try:
            print(querylist)
            print(inventorylib.sysvars.dirs.dbs.safe)
            dblib.sqlitemultquery(inventorylib.sysvars.dirs.dbs.safe, querylist)
        except:
            print('Error in ' + table + ' query')


"""
Main inventory database
"""
"""

For stock, there are some quantity options to discuss. There are a few types of items:

* Standard
inventory field in stock database is 0

* Non-stock, count in BOM pricing
inventory field in stock database is 0

* Stock, do not count in BOM pricing (or have special formula in options or something)
These can be consumables like paper, ferrules, tape.
These do not need to be treated specially. They are not included on BOMs


"""


def rebuildstockdb(tablelist=None):

    from iiutilities.dblib import sqlitemultquery
    from inventory.inventorylib import sysvars
    from iiutilities import datalib

    dbpath = sysvars.dirs.dbs.stock
    thetime = datalib.gettimestring()

    if not tablelist:
        tablelist = ['stock']

    # Create databases entries or leave them empty?
    addentries = True

    querylist = []
    runquery = False


    ### Stock
    table = 'stock'
    if table in tablelist:
        runquery = True
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (partid text primary key, status text default 'active'," +
            "description text default '', qtyunit text default 'each', qtystock real default 0, qtyonorder real default 0," +
            "qtyreserved real default 0, qtyavailable real default 0, qtystatus text default '', cost real default 0," +
            "stockcost real default 0, onordercost real default 0, totalcost real default 0," +
            "stockprice real default 0, onorderprice real default 0, totalprice real default 0," +
            "costqty real default 1, costqtyunit text default 'each', supplier text default '', " +
            "supplierpart text default '', manufacturer text default '', manufacturerpart text default '', " +
            "notes text default '', partdata text default '', datasheet text default '', inuse integer default 1, datecreated text default '', " +
            "createdby text default '', inventory integer text default 'std', minqty text default 0, type text default parts," +
            "marginmethod text default 'type', margin real default 0, price real default 0 )")

        if addentries:
            querylist.append("insert into " + table + " values ('A001', 'active', 'WIEGMANN 12x12x6', 'each', 1, 1, 1, \
            0, '', 149.97, 0,0,0,0,0,0,1, 'each', \
            'Cascade Controls', 'N412121206C', 'Wiegmann', 'N412121206C', '', '', '', 1, '" + thetime + "', 'CCR', \
            'std', 0, 'parts', 'type', 0, 0)")
            querylist.append("insert into " + table + " values ('A002', 'active', 'WIEGMANN 16x16x6', 'each', 1, 1, 2, \
            0, '', 172, 0,0,0,0,0,0,1, 'each', \
            'Cascade Controls', 'N412121206C', 'Wiegmann', 'N412121206C', '', '', '', 1, '" + thetime + "', 'CCR', \
            'std', 0, 'parts', 'type', 0, 0)")
            querylist.append("insert into " + table + " values ('A003', 'active', 'WIEGMANN 20x20x6', 'each', 1, 1, 2, \
            0, '', 204, 0,0,0,0,0,0,1, 'each', \
            'Cascade Controls', 'N412121206C', 'Wiegmann', 'N412121206C', '', '', '', 1, '" + thetime + "', 'CCR', 'std', 0, 'parts', 'type', 0, 0)")
            querylist.append("insert into " + table + " values ('A004', 'active', 'WIEGMANN 20x24x6', 'each', 1, 1, 2,\
             0,'',  233, 0,0,0,0,0,0,1, 'each', \
            'Cascade Controls', 'N412121206C', 'Wiegmann', 'N412121206C', '', '', '', 1, '" + thetime + "', 'CCR', 'std', 0, 'parts', 'type', 0, 0)")
            querylist.append("insert into " + table + " values ('L001', 'active', 'Shop Labor', 'hour', 1, 1, 2,\
             0, '', 42, 0,0,0,0,0,0,1, 'hour', \
            '', '', '', '', '', '', '', 1, '" + thetime + "', 'CCR', 'std', 0, 'labor', 'type', 0, 0)")

    print(querylist)
    print(dbpath)
    sqlitemultquery(dbpath, querylist)


"""
System

Tables for calculations, uisettings, etc.

Calcs, uisettings -- straight item value text tables


"""


def rebuildsystemdb(tablelist=None):

    from iiutilities.dblib import sqlitemultquery
    from inventory.inventorylib import sysvars
    dbpath = sysvars.dirs.dbs.system

    if not tablelist:
        tablelist = ['calcs', 'uisettings']


    querylist = []
    runquery = False

    ### Calcs
    table = 'calcs'
    if table in tablelist:
        runquery = True
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (item text primary key, value text, notes text, detail text)")

        addentries = True
        if addentries:
            querylist.append("insert into " + table + " values ('partsmargin', '0.25', '', '')")
            querylist.append("insert into " + table + " values ('labormargin', '0.25', '', '')")
            querylist.append("insert into " + table + " values ('panelsizeoverheadmultiplier', '0.15', 'Dollars per \
                inch for miscellaneous parts.', '')")


    ### UISettings
    table = 'uisettings'
    if table in tablelist:
        runquery = True
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (item text primary key, value text, notes text, detail text)")

    if runquery:
        sqlitemultquery(dbpath, querylist)

"""
BOMS

Each BOM will have a unique, human-friendly tablename

The table format will be simple: partid text, qty text, partdata

A subset of the data is stored in the partdata field. This is so that we can alter data of the part in the BOM
independent of the part data in the stock database

We will also have a metadata \table
"""

"""
Inventories

<< see inventorylib for table structures >>

"""

"""
Orders

<< see inventorylib for table structures >>

"""

"""
Assemblies

<< see inventorylib for table structures >>

"""



"""
Notifications (mail, IFFFT, etc) data
"""


def rebuildnotificationsdb(tabledict=['queuednotifications', 'sentnotifications']):
    from iiutilities.dblib import sqlitemultquery
    from cupid.pilib import dirs

    runquery = False
    querylist = []
    addentries = True

    table = 'queuednotifications'
    if table in tabledict:
        runquery = True

        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( queuedtime text default '', type text default 'email', message text default '', options text default '')")

    table = 'sentnotifications'
    if table in tabledict:
        runquery = True

        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( queuedtime text default '', senttime text default '', type text default 'email', message text default '', options text default '')")

    if runquery:
        print(querylist)

        sqlitemultquery(dirs.dbs.notifications, querylist)




"""
userstabledata
"""


def rebuildusersdata(argument=None):
    from pilib import gethashedentry, dirs
    from iiutilities.dblib import sqlitemultquery

    querylist = []
    runquery = True

    querylist.append('drop table if exists users')
    enteringusers = True
    runquery = False
    index = 1
    querylist.append(
        'create table users (id integer primary key not null, name text not null, password text not null, email text not null, temp text not null, authlevel integer default 0)')
    if argument == 'defaults':
        runquery = True
        entries = [{'user': 'viewer', 'password': 'viewer', 'email': 'viewer@interfaceinnovations.org', 'authlevel': 1},
                   {'user': 'admin', 'password': 'adminn', 'email': 'admin@interfaceinnovations.org', 'authlevel': 4},
                   {'user': 'controller', 'password': 'controller', 'email': 'viewer@interfaceinnovations.org',
                    'authlevel': 3}]
        index = 1
        for entry in entries:
            hashedentry = gethashedentry(entry['user'], entry['password'])
            querylist.append(
                "insert into users values(" + str(index) + ",'" + entry['user'] + "','" + hashedentry + "','" + entry[
                    'email'] + "',''," + str(entry['authlevel']) + ")")
            index += 1

    else:
        while enteringusers:
            validentry = True
            userinput = raw_input("Enter username or Q to stop: ")
            if userinput == 'Q':
                print('exiting ...')
                break
            passone = raw_input("Enter password: ")
            passtwo = raw_input("Confirm password: ")
            emailentry = raw_input("Enter user email")
            authlevelentry = raw_input("Enter authorization level (0-5)")

            if passone != passtwo:
                validentry = False
                print('passwords do not match')
            if not len(passone) >= 6:
                validentry = False
                print('passwords must be at least six characters')
            if not emailentry.find('@') > 0:
                validentry = False
                print('Email does not appear to be valid')

            if validentry:
                hashedentry = gethashedentry(userinput, passone)

                querylist.append("insert into users values(" + str(
                    index) + ",'" + userinput + "','" + hashedentry + "','" + emailentry + "',''," + authlevelentry + ")")
                index += 1
                runquery = True

    if runquery:
        print(querylist)
        sqlitemultquery(dirs.dbs.users, querylist)


def rebuildsessiondb():
    from iiutilities.dblib import sqlitemultquery
    from inventorylib import sysvars

    querylist = []

    ### Session limits

    table = 'sessionlimits'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text primary key, sessionsallowed real default 5 )")

    querylist.append("insert into " + table + " values ('viewer', 5)")
    querylist.append("insert into " + table + " values ('controller', 5)")
    querylist.append("insert into " + table + " values ('administrator', 5)")
    querylist.append("insert into " + table + " values ('owner', 3)")
    querylist.append("insert into " + table + " values ('admin', 3)")
    querylist.append("insert into " + table + " values ('colin', 5)")

    ### Settings table

    table = 'settings'
    querylist.append('drop table if exists ' + table)
    querylist.append(
        "create table " + table + " (sessionlength real default 600, sessionlimitsenabled real default 1, updatefrequency real)")

    querylist.append("insert into " + table + " values (600,1,30)")

    ### Session table

    table = 'sessions'
    querylist.append('drop table if exists ' + table)
    querylist.append(
        "create table " + table + " (username text, sessionid text, sessionlength real, timecreated text, apparentIP text , realIP text)")

    ### Sessions summary

    table = 'sessionsummary'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text,  sessionsactive real)")

    querylist.append("insert into " + table + " values ('viewer', 0)")
    querylist.append("insert into " + table + " values ('controller', 0)")
    querylist.append("insert into " + table + " values ('administrator', 0)")

    ### Session log

    table = 'sessionlog'
    querylist.append('drop table if exists ' + table)
    querylist.append(
        "create table " + table + " (username text, sessionid text, time text, action text, apparentIP text, realIP text)")


    # print(querylist)
    sqlitemultquery(sysvars.dirs.dbs.authlog, querylist)


def maketruetabledict(namelist):
    truetabledict = {}
    for name in namelist:
        truetabledict[name] = True
    return truetabledict

# default routine
if __name__ == "__main__":
    import sys

    # Check for DEFAULTS argument

    stockdbtables = ['stock']
    systemdbtables = ['system']
    notificationstables = ['queuedmessages', 'setmessages']
    safetables = ['users', 'usermeta', 'pathaliases']

    if len(sys.argv) > 1 and sys.argv[1] == 'DEFAULTS':
        print('making default databases')
        rebuildstockdb()
        rebuildsystemdb()
        rebuildsafedb()

    elif len(sys.argv) > 1:
        if sys.argv[1] in stockdbtables:
            print('running rebuild control tables for ' + sys.argv[1])
            rebuildstockdb(sys.argv[1])
        elif sys.argv[1] in systemdbtables:
            print('running rebuild system tables for ' + sys.argv[1])
            rebuildsystemdb(sys.argv[1])
        elif sys.argv[1] in safetables:
            print('running rebuild safe tables ' + sys.argv[1])
            rebuildsafedb(sys.argv[1])
        elif sys.argv[1] == 'safetables':
            print('rebuilding all safe tables ')
            rebuildsafedb()
        else:
            print('argument ' + sys.argv[1] + ' not found in argument list. ')

    else:
        pass
        # answer = raw_input('Rebuild wireless table (y/N)?')
        # if answer == 'y':
        #     rebuildwirelessdata()
        #
        # answer = raw_input('Rebuild AP table (y/N)?')
        # if answer == 'y':
        #     rebuildapdata()

        # answer = raw_input('Rebuild users (y/N)?')
        # if answer == 'y':
        #     rebuildsafedata()


