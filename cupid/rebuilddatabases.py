#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


# This script resets the control databases

from pilib import sqlitemultquery, controldatabase, systemdatadatabase, recipedatabase, sessiondatabase, safedatabase, \
    usersdatabase, motesdatabase

################################################
# Main control database


def rebuildcontroldb(tabledict):
    # Create databases entries or leave them empty?
    addentries = True

    querylist = []
    runquery = False

    ### Remotes table
    if 'remotes' in tabledict:
        runquery = True
        table = 'remotes'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (nodeid integer, msgtype text, keyvalue text, keyvaluename text, data text, time text)")

    ### Actions table
    if 'actions' in tabledict:
        runquery = True
        table = 'actions'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (actionindex integer primary key, valuerowid integer default 1, name text unique default 'myaction', enabled boolean default 0, actiontype text default 'email', actiondetail text default 'info@interfaceinnovations.org', conditiontype text default 'dbvalue',database text default 'controldata',tablename text default 'channels', variablename text default 'controlvalue', variablevalue text default '', operator text default 'equal',criterion text default '25',offdelay real default 0,ondelay real default 0,active boolean default 0, activereset boolean default 1, status boolean default 0,ontime text,offtime text,actionfrequency real default 60, lastactiontime text default '', statusmsg text default 'default msg')")
        if addentries:
            querylist.append("insert into " + table + " default values")

    ### SystemStatus table
    if 'systemstatus' in tabledict:
        runquery = True
        table = 'systemstatus'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (picontrolenabled boolean default 0, picontrolstatus boolean default 0, picontrolfreq real default 15 , lastpicontrolpoll text default '', updateioenabled boolean default 1, updateiostatus boolean default 0, updateiofreq real default 15, lastiopoll text default '', enableoutputs boolean default 0, sessioncontrolenabled boolean default 0, sessioncontrolstatus boolean default 0, systemstatusenabled boolean default 1, netstatusenabled boolean default 1, netconfigenabled default 0, checkhamachistatus boolean default 0, hamachistatus boolean default 0, systemstatusstatus boolean default 0, systemstatusfreq real default 15, lastsystemstatuspoll text default '', systemmessage text default '', serialhandlerenabled boolean default 0, serialhandlerstatus boolean default 0, webserver text default 'nginx')")
        if addentries:
            querylist.append("insert into " + table + " default values")

    ### logconfig Table
    if 'logconfig' in tabledict:
        runquery = True
        table = 'logconfig'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (networkloglevel integer, iologlevel integer, systemstatusloglevel integer, controlloglevel integer, daemonloglevel integer)")
        if addentries:
            querylist.append(
                "insert into " + table + " values (4,4,4,4,4)")


    ### Indicators table
    if 'indicators' in tabledict:
        runquery = True
        table = 'indicators'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( name text primary key, interface text, type text, status boolean default 0, detail text)")
        addentries = True
        if addentries:
            querylist.append("insert into " + table + " values ('SPI_RGB1_R', 'SPI1', 'CuPIDlights',0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB1_G', 'SPI1', 'CuPIDlights',0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB1_B', 'SPI1', 'CuPIDlights',0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_R', 'SPI1', 'CuPIDlights',0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_G', 'SPI1', 'CuPIDlights',0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_B', 'SPI1', 'CuPIDlights',0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_R', 'SPI1', 'CuPIDlights',0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_G', 'SPI1', 'CuPIDlights',0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_B', 'SPI1', 'CuPIDlights',0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_R', 'SPI1', 'CuPIDlights',0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_G', 'SPI1', 'CuPIDlights',0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_B', 'SPI1', 'CuPIDlights',0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_SC_R', 'SPI1', 'CuPIDlights',0,'red')")
            querylist.append("insert into " + table + " values ('SPI_SC_G', 'SPI1', 'CuPIDlights',0,'green')")
            querylist.append("insert into " + table + " values ('SPI_SC_B', 'SPI1', 'CuPIDlights',0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_SC_Y', 'SPI1', 'CuPIDlights',0,'yellow')")

    ### Defaults table
    if 'defaults' in tabledict:
        runquery = True
        table = 'defaults'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( inputpollfreq real, outputpollfreq real)")
        addentries = True
        if addentries:
            querylist.append("insert into " + table + " values (60, 60)")

    ### Outputs table
    if 'outputs' in tabledict:
        runquery = True
        table = 'outputs'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            'create table ' + table + ' (id text primary key, interface text, type text, address text, name text, ' +
            'value real, unit text, polltime text, pollfreq real, ontime text, offtime text)')
    ### Inputs table
    if 'inputs' in tabledict:
        runquery = True
        table = 'inputs'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            'create table ' + table + ' (id text primary key, interface text, type text, address text, name text, ' +
            'value real, unit text, polltime text, pollfreq real, ontime text, offtime text)')


    ### OWFS Table
    if 'owfs' in tabledict:
        runquery = True
        table = 'owfs'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (address text primary key, family text, id text, type text, crc8 text)")

    ### Inputs Info Table
    if 'ioinfo' in tabledict:
        runquery = True
        table = 'ioinfo'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (id text primary key, name text, options text)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('GPIO18', 'GPIO18', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO23', 'GPIO23', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO24', 'GPIO24', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO25', 'GPIO25(BootOk)', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO4', 'GPIO4(MotePower)', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO17', 'GPIO17', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO27', 'GPIO27', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO22', 'GPIO22', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO5', 'GPIO5', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO6', 'GPIO6', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO13', 'GPIO13', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO19', 'GPIO19', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO26', 'GPIO26', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO16', 'GPIO16', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO20', 'GPIO20', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO21', 'GPIO21(WiFi)', '')")

    ### Interfaces Table
    if 'interfaces' in tabledict:
        runquery = True
        table = 'interfaces'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (interface text, type text, address text, id text primary key, name text unique, options text, enabled integer default 0, status integer default 0)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('SPI1','CuPIDlights','','SPIout1','myCuPIDlightboard','',0,0)")
            querylist.append(
                "insert into " + table + " values ('SPI0','SPITC','','SPITC0','mySPITC','',0,0)")
            querylist.append(
                "insert into " + table + " values ('I2C','DS2483','','I2CDS2483','I2C 1Wire','tempunit:F',1,0)")
            querylist.append(
                "insert into " + table + " values ('LAN','MBTCP','192.168.1.18','MBTCP1','Modbus TCPIP','wordblocksize:24,bitblocksize:96',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','18','GPIO18','GPIO 18','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','23','GPIO23','GPIO 23','mode:input,pullupdown:pullu',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','24','GPIO24','GPIO 24','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','25','GPIO25','GPIO 25','mode:output',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','4','GPIO4','GPIO 4','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','17','GPIO17','GPIO 17','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','27','GPIO27','GPIO 27','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','22','GPIO22','GPIO 22','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','5','GPIO5','GPIO 5','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','6','GPIO6','GPIO 6','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','13','GPIO13','GPIO 13','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','19','GPIO19','GPIO 19','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','26','GPIO26','GPIO 26','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','16','GPIO16','GPIO 16','mode:input,pullupdown:pullup',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','20','GPIO20','GPIO 20','mode:input,pullupdown:pulldown,function:shutdown,functionstate:true',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','21','GPIO21','GPIO 21','mode:input,pullupdown:pullup',1,0)")

    ### modbustcp Table
    if 'modbustcp' in tabledict:
        runquery = True
        table = 'modbustcp'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (interfaceid text, register integer, mode text default 'read', length integer default 1,  bigendian boolean default 1, reversebyte boolean default 0, format text, options text)")
        if addentries:
            querylist.append("insert into " + table + " values ('MBTCP1', '400001', 'read', 2, 1, 0, 'float32','')")
            querylist.append("insert into " + table + " values ('MBTCP1', '400003', 'read', 2, 1, 0, 'float32','')")
            querylist.append("insert into " + table + " values ('MBTCP1', '400005', 'read', 2, 1, 0, 'float32','')")
            querylist.append("insert into " + table + " values ('MBTCP1', '400007', 'read', 2, 1, 0, 'float32','')")

    ### Controlalgorithms table
    if 'algorithms' in tabledict:
        runquery = True
        table = 'controlalgorithms'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (name text primary key, type text, maxposrate real default 0, maxnegrate real default 0, derivativemode text default time, derivativeperiod real default 0, integralmode text default time, integralperiod real default 0, proportional real default 1, integral real default 0, derivative real default 0, deadbandhigh real default 0, deadbandlow real default 0, dutypercent real default 0, dutyperiod real default 1, minontime real, minofftime real)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('on/off 1', 'on/off with deadband',1,1,0,0,0,0,0,0,0,0,0,0,1,0,0)")

    ### Algorithmtypes
    if 'algorithmtypes' in tabledict:
        runquery = True
        table = 'algorithmtypes'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " ( name text )")
        if addentries:
            querylist.append("insert into " + table + " values ( 'on/off with deadband')")

    ### Channels table
    if 'channels' in tabledict:
        runquery = True
        table = 'channels'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (channelindex integer primary key, name text unique, controlinput text default 'none', enabled boolean default 0, outputsenabled boolean default 0, controlupdatetime text, controlalgorithm text default 'on/off 1', controlrecipe text default 'none', recipestage integer default 0, recipestarttime real default 0, recipestagestarttime real default 0, setpointvalue real, controlvalue real, controlvaluetime text, positiveoutput text default none, negativeoutput text default none, action real default 0, mode text default manual, statusmessage text, logpoints real default 100, data text)")
        if addentries:
            querylist.append(
                "insert into " + table + " values (1, 'channel 1', 'none', 0, 0, '', 'on/off 1', 'none',0,0,0,65, '', '', 'none', 'none', 0, 'auto', '', 1000,'')")

    if runquery:
        print(querylist)
        sqlitemultquery(controldatabase, querylist)


############################################
# authlog

def rebuildsessiondb():
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
    sqlitemultquery(sessiondatabase, querylist)


############################################
# device info 

def rebuildsystemdatadb(tabledict):
    runquery = "False"
    querylist = []
    if 'netstatus' in tabledict:
        runquery = True
        table = 'netstatus'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( WANaccess boolean default 0, latency real default 0, mode text default 'eth0wlan0bridge', onlinetime text, offlinetime text default '', updatetime text '', statusmsg text default '')")
        querylist.append("insert into " + table + "  default values")

    if 'netconfig' in tabledict:
        runquery = True
        table = 'netconfig'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (SSID text default none, mode text default eth0wlan0bridge, aprevert text default '', addtype text default 'dhcp', address text default '192.168.1.30', gateway text default '192.168.0.1', dhcpstart text default '192.168.0.70', dhcpend text default '192.168.0.99', apreverttime integer default 60, stationretrytime integer default 300, laststationretry text default '', pingthreshold integer default 2000, netstatslogenabled boolean default 0, netstatslogfreq integer default 60, apoverride boolean default 0, apoverridepin integer default 21)")
        querylist.append("insert into " + table + "  default values")

    if 'systemflags' in tabledict:
        runquery = True
        table = 'systemflags'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (name text, value boolean default 0)")
        querylist.append("insert into " + table + " values ('reboot', 0)")
        querylist.append("insert into " + table + " values ('netconfig', 0)")
        querylist.append("insert into " + table + " values ('updateiicontrollibs', 0)")
        querylist.append("insert into " + table + " values ('updatecupidweblib', 0)")

    if 'metadata' in tabledict:
        runquery = True
        table = 'metadata'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (  devicename text, groupname text)")
        querylist.append("insert into " + table + " values ( 'My CuPID', 'None' )")

    if 'uisettings' in tabledict:
        runquery = True
        table = 'uisettings'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (  'setting' text, 'group' text, 'value' text)")
        querylist.append("insert into " + table + " values ( 'showinputgpiologs', 'dataviewer', '1' )")
        querylist.append("insert into " + table + " values ( 'showinput1wirelogs', 'dataviewer', '1' )")
        querylist.append("insert into " + table + " values ( 'showchannellogs', 'dataviewer', '1' )")

    if 'versions' in tabledict:
        runquery = True
        table = 'versions'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( item text primary key,  version text, versiontime text, updatetime text)")
    if runquery:
        print(querylist)
        sqlitemultquery(systemdatadatabase, querylist)


############################################
# recipesdata

def rebuildrecipesdb(tabledict):
    runquery = False
    querylist = []
    addentries = True
    if 'recipes' in tabledict:
        runquery = True

        table = 'stdreflow'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( stagenumber integer default 1, stagelength real default 0, setpointvalue real default 0, lengthmode text default 'setpoint', controlalgorithm text default 'on/off 1')")
        if addentries:
            querylist.append("insert into " + table + " values ( 1, 180, 300, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 2, 90, 360, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 3, 60, 420, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 4, 60, 60, 'setpoint','on/off 1')")

    if runquery:
        print(querylist)

        sqlitemultquery(recipedatabase, querylist)


############################################
# motes raw data


def rebuildmotesdb(tabledict):
    runquery = False
    querylist = []
    addentries = True
    if 'readmessages' in tabledict:
        runquery = True

        table = 'readmessages'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( time text default '', message text default '' )")

    if 'queuedmessages' in tabledict:
        runquery = True

        table = 'queuedmessages'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( queuedtime text default '', message text default '' )")

    if 'sentmessages' in tabledict:
        runquery = True

        table = 'sentmessages'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( queuedtime text default '', senttime text default '', message text default '' )")

    if runquery:
        print(querylist)

        sqlitemultquery(motesdatabase, querylist)

############################################
# userstabledata


def rebuildusersdata(argument=None):
    from pilib import gethashedentry

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
        sqlitemultquery(usersdatabase, querylist)


############################################
# safedata

def rebuildwirelessdata():
    querylist = []
    querylist.append('drop table if exists wireless')
    querylist.append('create table wireless (SSID text, password text)')

    sqlitemultquery(safedatabase, querylist)


def rebuildapdata(SSID='cupidwifi', password='cupidpassword'):
    querylist = []

    querylist.append('drop table if exists apsettings')
    querylist.append("create table apsettings (SSID text default 'cupidwifi', password text default 'cupidpassword')")
    querylist.append(
                "insert into apsettings values('" + SSID + "','" + password + "')")
    sqlitemultquery(safedatabase, querylist)


def maketruetabledict(namelist):
    truetabledict = {}
    for name in namelist:
        truetabledict[name] = True
    return truetabledict

# default routine
if __name__ == "__main__":
    import sys

    # Check for DEFAULTS argument

    controldbtables = ['actions', 'modbustcp', 'logconfig', 'defaults', 'systemstatus', 'indicators', 'inputs', 'outputs', 'owfs', 'ioinfo', 'interfaces',
                       'algorithms', 'algorithmtypes', 'channels', 'remotes', 'mote']
    systemdbtables = ['metadata', 'netconfig', 'netstatus', 'versions', 'systemflags', 'uisettings']
    motestables = ['readmessages', 'queuedmessages', 'sentmessages']

    if len(sys.argv) > 1 and sys.argv[1] == 'DEFAULTS':
        print('making default databases')
        rebuildwirelessdata()

        # This checks the hostname, sets it as the hostname with 'cupid' prefix, and sets default password
        # Then it calls the file rebuild
        from netconfig import setdefaultapsettings
        setdefaultapsettings()
        rebuildusersdata('defaults')

        rebuildcontroldb(maketruetabledict(controldbtables))
        rebuildsystemdatadb(maketruetabledict(systemdbtables))
        rebuildmotesdb(maketruetabledict(motestables))

        rebuildrecipesdb({'recipes': True})
        rebuildsessiondb()

    elif len(sys.argv) > 1:
        if sys.argv[1] in controldbtables:
            print('running rebuild control tables for ' + sys.argv[1])
            rebuildcontroldb(sys.argv[1])
        elif sys.argv[1] in systemdbtables:
            print('running rebuild system tables for ' + sys.argv[1])
            rebuildsystemdatadb(sys.argv[1])
        elif sys.argv[1] in motestables:
            print('running rebuild motes tables for ' + sys.argv[1])
            rebuildmotesdb(sys.argv[1])

    else:

        print("** Motes tables **")
        tablestorebuild = []
        execute = False
        for table in motestables:
            answer = raw_input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuildmotesdb(maketruetabledict(tablestorebuild))

        print("** Control tables **")
        tablestorebuild = []
        execute = False
        for table in controldbtables:
            answer = raw_input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuildcontroldb(maketruetabledict(tablestorebuild))

        print("** System tables **")
        tablestorebuild = []
        execute = False
        for table in systemdbtables:
            answer = raw_input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuildsystemdatadb(maketruetabledict(tablestorebuild))

        answer = raw_input('Rebuild wireless table (y/N)?')
        if answer == 'y':
            rebuildwirelessdata()

        answer = raw_input('Rebuild AP table (y/N)?')
        if answer == 'y':
            rebuildapdata()

        answer = raw_input('Rebuild users table (y/N)?')
        if answer == 'y':
            rebuildusersdata()

        recipetabledict = {}
        answer = raw_input('Rebuild recipes table (y/N)?')
        if answer == 'y':
            recipetabledict['recipes'] = True
        rebuildrecipesdb(recipetabledict)

        answer = raw_input('Rebuild sessions table (y/N)?')
        if answer == 'y':
            rebuildsessiondb()
