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

from pilib import sqlitemultquery, controldatabase, systemdatadatabase, recipedatabase, sessiondatabase, safedatabase, usersdatabase

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
            "create table " + table + " (channelindex integer primary key, name text unique default 'myaction', enabled boolean default 0, actiontype text default 'email', actiondetail text default 'info@interfaceinnovations.org', conditiontype text default 'dbvalue',database text default 'controldata',tablename text default 'channels', variablename text default 'controlvalue', variablevalue text default '', operator text default '=',criterion text default '25',offdelay real default 0,ondelay real default 0,active boolean default 0, activereset boolean default 1, status boolean default 0,ontime text,offtime text,actionfrequency real default 60, lastactiontime text default '', statusmsg text default 'default msg')")
        if addentries:
            querylist.append("insert into " + table + " default values")

    ### SystemStatus table
    if 'systemstatus' in tabledict:
        runquery = True
        table = 'systemstatus'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (picontrolenabled boolean default 0, picontrolstatus boolean default 0, picontrolfreq real default 15 , lastpicontrolpoll text, updateioenabled boolean default 1, updateiostatus boolean default 0, updateiofreq real default 5, lastiopoll text, enableoutputs boolean default 0, sessioncontrolenabled boolean, sessioncontrolstatus boolean, systemstatusenabled boolean default 0, netconfigenabled boolean default 0, systemstatusstatus boolean, systemstatusfreq real default 15, lastsystemstatuspoll text, systemmessage text, serialhandlerenabled boolean default 0, serialhandlerstatus boolean default 0)")
        if addentries:
            querylist.append("insert into " + table + " values (0,0,15,'',1,0,15,'',0,1,0,1,0,0,15,'','',0,0)")

    ### logconfig Table
    if 'logconfig' in tabledict:
        runquery = True
        table = 'logconfig'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (networkloglevel integer, iologlevel integer, systemstatusloglevel integer, controlloglevel integer, daemonloglevel integer)")
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
                "insert into " + table + " values ('GPIO18', 'GPIO1', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO23', 'GPIO2', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO24', 'GPIO3', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO25', 'GPIO4', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO4', 'GPIO5', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO17', 'GPIO6', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO21', 'GPIO7', '')")
            querylist.append(
                "insert into " + table + " values ('GPIO22', 'GPIO8', '')")

    ### Interfaces Table
    if 'interfaces' in tabledict:
        runquery = True
        table = 'interfaces'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (interface text, type text, address text, id text primary key, name text unique, options text, enabled integer default 0, status integer default 0)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('SPI1','CuPIDlights','','SPIout1','myCuPIDlightboard','',1,0)")
            querylist.append(
                "insert into " + table + " values ('I2C','DS2483','192.168.1.18','I2CDS2483','I2C 1Wire','tempunit:F',1,0)")
            querylist.append(
                "insert into " + table + " values ('LAN','MBTCP','','MBTCP1','Modbus TCPIP','wordblocksize:24,bitblocksize:96',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','18','GPIO18','GPIO 1','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','23','GPIO23','GPIO 2','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','24','GPIO24','GPIO 3','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','25','GPIO25','GPIO 4','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','4','GPIO4','GPIO 5','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','17','GPIO17','GPIO6','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','21','GPIO21','GPIO 7','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','22','GPIO22','GPIO 8','mode:output,pullupdown:pulldown',1,0)")

    ### modbustcp Table
    if 'modbustcp' in tabledict:
        runquery = True
        table = 'modbustcp'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (interfaceid text, register integer, mode text default 'read', length integer default 1,  bigendian boolean default 1, reversebyte boolean default 0, format text, options text)")
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
            "create table " + table + " (channelindex integer primary key, name text unique, controlinput text , enabled boolean default 0, outputsenabled boolean default 0, controlupdatetime text, controlalgorithm text default 'on/off 1', controlrecipe text default 'none', recipestage integer default 0, recipestarttime real default 0, recipestagestarttime real default 0, setpointvalue real, controlvalue real, controlvaluetime text, positiveoutput text, negativeoutput text, action real default 0, mode text default manual, statusmessage text, logpoints real default 100)")
        if addentries:
            querylist.append(
                "insert into " + table + " values (1, 'channel 1', 'none', 0, 0, '', 'on/off 1', 'none',0,0,0,65, '', '', 'output1', 'output2', 0, 'auto', '', 1000)")

    if runquery:
        print(querylist)
        sqlitemultquery(controldatabase, querylist)

############################################
# authlog

def rebuildsessiondb():
    querylist=[]

    ### Session limits

    table='sessionlimits'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text primary key, sessionsallowed real default 5 )")

    querylist.append("insert into " + table + " values ('viewer', 5)")
    querylist.append("insert into " + table + " values ('controller', 5)")
    querylist.append("insert into " + table + " values ('administrator', 5)")
    querylist.append("insert into " + table + " values ('owner', 3)")
    querylist.append("insert into " + table + " values ('admin', 3)")
    querylist.append("insert into " + table + " values ('colin', 5)")

    ### Settings table

    table='settings'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (sessionlength real default 600, sessionlimitsenabled real default 1, updatefrequency real)")

    querylist.append("insert into " + table + " values (600,1,30)")

    ### Session table

    table='sessions'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text, sessionid text, sessionlength real, timecreated text, apparentIP text , realIP text)")

    ### Sessions summary

    table='sessionsummary'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text,  sessionsactive real)")

    querylist.append("insert into " + table + " values ('viewer', 0)")
    querylist.append("insert into " + table + " values ('controller', 0)")
    querylist.append("insert into " + table + " values ('administrator', 0)")

    ### Session log

    table='sessionlog'
    querylist.append('drop table if exists ' + table)
    querylist.append("create table " + table + " (username text, sessionid text, time text, action text, apparentIP text, realIP text)")


    #print(querylist)
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
        querylist.append("create table " + table + " ( address text, connected boolean, WANaccess text, latency real, SSID text, dhcpstatus boolean default 0, mode text , onlinetime text, offlinetime text, statusmsg text)")
        querylist.append("insert into " + table + " values ('',0,'','','','','','','','')")

    if 'netconfig' in tabledict:
        runquery = True
        table = 'netconfig'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (enabled boolean, SSID text, mode text, aprevert text default 'temprevert', addtype text, address text, gateway text, dhcpstart text default '192.168.0.70', dhcpend text default '192.168.1.99', apreverttime integer default 60, stationretrytime integer default 300, laststationretry text, pingthreshold integer default 200)")
        querylist.append("insert into " + table + " values ('1','OurHouse','station','temprevert','static','192.168.1.30','192.168.1.1','','',60,300,0,200)")

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
            querylist.append("insert into " + table + " values ( 1, 300, 40, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 2, 600, 60, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 3, 600, 100, 'setpoint','on/off 1')")
            querylist.append("insert into " + table + " values ( 4, 300, 40, 'setpoint','on/off 1')")

    if runquery:
        print(querylist)

        sqlitemultquery(recipedatabase, querylist)

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
    querylist.append('create table users (id integer primary key not null, name text not null, password text not null, email text not null, temp text not null, authlevel integer default 0)')
    if argument == 'defaults':
        runquery = True
        entries = [{'user': 'viewer', 'password': 'viewer', 'email': 'viewer@interfaceinnovations.org', 'authlevel': 1},
                   {'user': 'admin', 'password': 'adminn', 'email': 'admin@interfaceinnovations.org', 'authlevel': 4},
                   {'user': 'controller', 'password': 'controller', 'email': 'viewer@interfaceinnovations.org', 'authlevel': 3}]
        index = 1
        for entry in entries:
            hashedentry = gethashedentry(entry['user'], entry['password'])
            querylist.append("insert into users values(" + str(index) + ",'" + entry['user'] + "','" + hashedentry + "','" + entry['email'] + "',''," + str(entry['authlevel']) + ")")
            index += 1

    else:
        while enteringusers:
            validentry = True
            input = raw_input("Enter username or Q to stop: ")
            passone = raw_input("Enter password: ")
            passtwo = raw_input("Confirm password: ")
            emailentry = raw_input("Enter user email")
            authlevelentry = raw_input("Enter authorization level (0-5)")

            if input == 'Q':
                enteringusers = False
                validentry = False
                print('exiting ...')
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
                hashedentry = gethashedentry(passone)

                querylist.append("insert into users values(" + str(index) + ",'" + input + "','" + hashedentry + "','" + emailentry + "',''," + authlevelentry + ")")
                index += 1
                runquery = True

    if runquery:
        print(querylist)
        sqlitemultquery(usersdatabase, querylist)

############################################
# safedata

def rebuildsafedata():
    runquery = False
    querylist = []
    querylist.append('drop table if exists wireless')
    querylist.append('create table wireless (SSID text, password text)')

    sqlitemultquery(safedatabase, querylist)


# default routine
if __name__ == "__main__":
    import sys

    # Check for DEFAULTS argument

    if len(sys.argv) > 1 and sys.argv[1] == 'DEFAULTS':
        print('making default databases')
        rebuildsafedata()
        rebuildusersdata('defaults')
        rebuildcontroldb({'actions': True, 'modbustcp': True, 'logconfig': True, 'defaults': True, 'systemstatus': True, 'indicators': True, 'inputs': True, 'outputs': True, 'owfs': True, 'ioinfo': True, 'interfaces': True, 'inputsdata':True, 'algorithms': True, 'algorithmtypes': True, 'channels': True, 'remotes': True})
        rebuildsystemdatadb({'metadata': True, 'netconfig': True, 'netstatus': True, 'versions': True, 'systemflags': True})
        rebuildrecipesdb({'recipes': True})
        rebuildsessiondb()

    else:
        answer = raw_input('Rebuild wireless table (y/N)?')
        if answer == 'y':
            rebuildsafedata()

        answer = raw_input('Rebuild users table (y/N)?')
        if answer == 'y':
            rebuildusersdata()

        controltabledict = {}
        answer = raw_input('Rebuild remotes table (y/N)?')
        if answer == 'y':
            controltabledict['remotes'] = True

        answer = raw_input('Rebuild actions table (y/N)?')
        if answer == 'y':
            controltabledict['actions'] = True

        answer = raw_input('Rebuild logconfig table (y/N)?')
        if answer == 'y':
            controltabledict['logconfig'] = True

        answer = raw_input('Rebuild defaults table (y/N)?')
        if answer == 'y':
            controltabledict['defaults'] = True

        answer = raw_input('Rebuild systemstatus table (y/N)?')
        if answer == 'y':
            controltabledict['systemstatus'] = True

        answer = raw_input('Rebuild indicators table (y/N)?')
        if answer == 'y':
            controltabledict['indicators'] = True

        answer = raw_input('Rebuild inputs table (y/N)?')
        if answer == 'y':
            controltabledict['inputs'] = True

        answer = raw_input('Rebuild modbus table (y/N)?')
        if answer == 'y':
            controltabledict['modbustcp'] = True

        answer = raw_input('Rebuild outputs table (y/N)?')
        if answer == 'y':
            controltabledict['outputs'] = True

        answer = raw_input('Rebuild owfs table (y/N)?')
        if answer == 'y':
            controltabledict['owfs'] = True

        answer = raw_input('Rebuild ioinfo table (y/N)?')
        if answer == 'y':
            controltabledict['ioinfo'] = True

        answer = raw_input('Rebuild interfaces table (y/N)?')
        if answer == 'y':
            controltabledict['interfaces'] = True

        answer = raw_input('Rebuild inputsdata table (y/N)?')
        if answer == 'y':
            controltabledict['inputsdata'] = True

        answer = raw_input('Rebuild algorithms table (y/N)?')
        if answer == 'y':
            controltabledict['algorithms'] = True

        answer = raw_input('Rebuild algorithmtypes table (y/N)?')
        if answer == 'y':
            controltabledict['algorithmtypes'] = True

        answer = raw_input('Rebuild channels table (y/N)?')
        if answer == 'y':
            controltabledict['channels'] = True

        rebuildcontroldb(controltabledict)

        systemtabledict = {}
        answer = raw_input('Rebuild metadata table (y/N)?')
        if answer == 'y':
            systemtabledict['metadata'] = True

        answer = raw_input('Rebuild versions table (y/N)?')
        if answer == 'y':
            systemtabledict['versions'] = True

        answer = raw_input('Rebuild netconfig table (y/N)?')
        if answer == 'y':
            systemtabledict['netconfig'] = True

        answer = raw_input('Rebuild netstatus table (y/N)?')
        if answer == 'y':
            systemtabledict['netstatus'] = True

        answer = raw_input('Rebuild systemflags table (y/N)?')
        if answer == 'y':
            systemtabledict['systemflags'] = True

        rebuildsystemdatadb(systemtabledict)

        recipetabledict = {}
        answer = raw_input('Rebuild recipes table (y/N)?')
        if answer == 'y':
            recipetabledict['recipes'] = True
        rebuildrecipesdb(recipetabledict)

        answer = raw_input('Rebuild sessions table (y/N)?')
        if answer == 'y':
            rebuildsessiondb()
