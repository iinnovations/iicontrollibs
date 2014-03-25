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

from pilib import sqlitemultquery, controldatabase, systemdatadatabase, recipedatabase, sessiondatabase

################################################
# Main control database


def rebuildcontroldb(tabledict):
    # Create databases entries or leave them empty?
    addentries = True

    querylist = []
    runquery = False

    ### SystemStatus table
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
            "create table " + table + " (picontrolenabled boolean default 0, picontrolstatus boolean default 0, picontrolfreq real default 15 , lastpicontrolpoll text, inputsreadenabled boolean default 1, inputsreadstatus boolean default 0, inputsreadfreq real default 15, lastinputspoll text, enableoutputs boolean default 0, sessioncontrolenabled boolean, sessioncontrolstatus boolean, systemstatusenabled boolean, systemstatusstatus boolean, systemmessage text)")
        if addentries:
            querylist.append("insert into " + table + " values (0,0,15,'',1,0,15,'',0,1,0,1,0,'')")

    ### Indicators table
    if 'indicators' in tabledict:
        runquery = True
        table = 'indicators'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " ( name text primary key, type text, status boolean default 0, detail text)")
        addentries = True
        if addentries:
            querylist.append("insert into " + table + " values ('SPI_RGB1_R', 'SPI', 0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB1_G', 'SPI', 0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB1_B', 'SPI', 0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_R', 'SPI', 0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_G', 'SPI', 0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB2_B', 'SPI', 0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_R', 'SPI', 0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_G', 'SPI', 0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB3_B', 'SPI', 0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_R', 'SPI', 0,'red')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_G', 'SPI', 0,'green')")
            querylist.append("insert into " + table + " values ('SPI_RGB4_B', 'SPI', 0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_SC_R', 'SPI', 0,'red')")
            querylist.append("insert into " + table + " values ('SPI_SC_G', 'SPI', 0,'green')")
            querylist.append("insert into " + table + " values ('SPI_SC_B', 'SPI', 0,'blue')")
            querylist.append("insert into " + table + " values ('SPI_SC_Y', 'SPI', 0,'yellow')")

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
            "create table " + table + " ( id text primary key, interface text, type text, address text, enabled boolean default 0, name text unique, mode text default 'manual', status boolean default 0, ontime string, offtime string, minontime real, minofftime real)")
        addentries = True
        if addentries:
            querylist.append(
                "insert into " + table + " values ('GPIO1', 'GPIO', 'GPIO', '18', 0, 'output1', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO2', 'GPIO', 'GPIO', '23', 0, 'output2', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO3', 'GPIO', 'GPIO', '24', 0, 'output3', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO4', 'GPIO', 'GPIO', '25', 0, 'output4', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO5', 'GPIO', 'GPIO', '4', 0, 'output5', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO6', 'GPIO', 'GPIO', '17', 0, 'output6', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO7', 'GPIO', 'GPIO', '21', 0, 'output7', 'manual', 0,'','',0,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO8', 'GPIO', 'GPIO', '22', 0, 'output8', 'manual', 0,'','',0,0)")

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
        querylist.append("create table " + table + " (id text primary key, name text)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('GPIO1', 'GPIO1')")
            querylist.append(
                "insert into " + table + " values ('GPIO2', 'GPIO2')")
            querylist.append(
                "insert into " + table + " values ('GPIO3', 'GPIO3')")
            querylist.append(
                "insert into " + table + " values ('GPIO4', 'GPIO4')")
            querylist.append(
                "insert into " + table + " values ('GPIO5', 'GPIO5')")
            querylist.append(
                "insert into " + table + " values ('GPIO6', 'GPIO6')")
            querylist.append(
                "insert into " + table + " values ('GPIO7', 'GPIO7')")
            querylist.append(
                "insert into " + table + " values ('GPIO8', 'GPIO8')")

    ### Interfaces Table
    if 'interfaces' in tabledict:
        runquery = True
        table = 'interfaces'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (interface text, type text, id text primary key, name text unique, options text, enabled integer default 0, status integer default 0)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('SPI1','CuPIDlights','SPIout1','myCuPIDlightboard','tempunit:F',1,0)")
            querylist.append(
                "insert into " + table + " values ('I2C','DS2483','I2CDS2483','I2C 1Wire','',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO18','GPIO Output 1','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO23','GPIO Output 2','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO24','GPIO Output 3','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO25','GPIO Output 4','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO4','GPIO Output 5','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO17','GPIO Output 6','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO21','GPIO Output 7','mode:output,pullupdown:pulldown',1,0)")
            querylist.append(
                "insert into " + table + " values ('GPIO','GPIO','GPIO22','GPIO Output 8','mode:output,pullupdown:pulldown',1,0)")



    ### InputData Table
    if 'inputsdata' in tabledict:
        runquery = True
        table = 'inputsdata'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (id text primary key, interface text, type text, address text, value real, unit text, polltime text, enabled boolean default 1, name text)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('GPIO1', 'GPIO', 'GPIO', '18', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO2', 'GPIO', 'GPIO', '23', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO3', 'GPIO', 'GPIO', '24', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO4', 'GPIO', 'GPIO', '25', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO5', 'GPIO', 'GPIO', '4', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO6', 'GPIO', 'GPIO', '17', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO7', 'GPIO', 'GPIO', '21', 0, '', '', 1,'')")
            querylist.append(
                "insert into " + table + " values ('GPIO8', 'GPIO', 'GPIO', '22', 0, '', '', 1,'')")

    ### Controlalgorithms table
    if 'algorithms' in tabledict:
        runquery = True
        table = 'controlalgorithms'
        querylist.append('drop table if exists ' + table)
        querylist.append(
            "create table " + table + " (name text primary key, type text, maxposrate real default 0, maxnegrate real default 0, derivativemode text default time, derivativeperiod real default 0, integralmode text default time, integralperiod real default 0, proportional real default 1, integral real default 0, derivative real default 0, deadbandhigh real default 0, deadbandlow real default 0, dutypercent real default 0, dutyperiod real default 1)")
        if addentries:
            querylist.append(
                "insert into " + table + " values ('on/off 1', 'on/off with deadband',1,1,0,0,0,0,0,0,0,0,0,0,1)")

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
    querylist.append("insert into " + table + " values ('colin', 3)")

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
    sqlitemultquery(sessiondatabase,querylist)


############################################
# device info 

def rebuildsystemdatadb(tabledict):
    runquery = "False"
    querylist = []
    if 'netstatus' in tabledict:
        runquery = "True"
        table = 'netstatus'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " ( IPAddress text, gateway text, WANaccess text, networkSSID text networkpassword text, dhcpstatus boolean default 0, hostapdstatus boolean default 0)")
        querylist.append("insert into " + table + " values ('','','','','','')")
    if 'netconfig' in tabledict:
        runquery = "True"
        table = 'netconfig'
        querylist.append('drop table if exists ' + table)
        querylist.append("create table " + table + " (nettype text, addtype text, address text, gateway text, dhcpstart text default '192.168.0.70', dhcpend text default '192.168.1.99')")
        querylist.append("insert into " + table + " values ('station','static','192.168.1.40','192.168.1.1','','')")

    if 'metadata' in tabledict:
        runquery = "True"
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
        runquery = "True"

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

# default routine
if __name__ == "__main__":

    controltabledict = {}
    answer = raw_input('Rebuild actions table (y/N)?')
    if answer == 'y':
        controltabledict['actions'] = True

    answer = raw_input('Rebuild defaults table (y/N)?')
    if answer == 'y':
        controltabledict['defaults'] = True

    answer = raw_input('Rebuild systemstatus table (y/N)?')
    if answer == 'y':
        controltabledict['systemstatus'] = True

    answer = raw_input('Rebuild indicators table (y/N)?')
    if answer == 'y':
        controltabledict['indicators'] = True

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
    rebuildsystemdatadb(systemtabledict)

    recipetabledict = {}
    answer = raw_input('Rebuild recipes table (y/N)?')
    if answer == 'y':
        recipetabledict['recipes'] = True
    rebuildrecipesdb(recipetabledict)

    answer = raw_input('Rebuild sessions table (y/N)?')
    if answer == 'y':
        rebuildsessiondb()
