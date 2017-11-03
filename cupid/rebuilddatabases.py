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

from iiutilities.utility import Bunch
from cupid import pilib

tablenames = Bunch()

tablenames.control = ['actions', 'modbustcp', 'labjack', 'defaults', 'indicators', 'inputs', 'outputs', 'owfs', 'ioinfo',
                   'interfaces',
                   'controlalgorithms', 'algorithmtypes', 'channels', 'remotes']
tablenames.system = ['systemstatus', 'logconfig', 'metadata', 'netconfig', 'netstatus', 'wirelessnetworks', 'versions',
                  'systemflags', 'uisettings', 'notifications']
tablenames.motes = ['read', 'queued', 'sent']
tablenames.safe = ['wirelessdata', 'apdata']
tablenames.notifications = ['queued', 'sent']
tablenames.recipes = ['recipes']
tablenames.sessions = ['sessionlimits','settings','sessions','sessionsummary','sessionlog']
tablenames.logsettings = ['logsettings']
tablenames.users = ['users']


"""
Main control database
"""


def rebuild_control_db(**kwargs):

    from iiutilities.dblib import sqlitemultquery
    from iiutilities import dblib
    from cupid.pilib import dirs

    settings = {
        'tablelist':None,
        'migrate':True,
        'data_loss_ok':False
    }
    settings.update(kwargs)

    if not settings['tablelist']:
        settings['tablelist'] = tablenames.control

    # Create databases entries or leave them empty?
    addentries = True

    querylist = []
    runquery = False

    control_database = pilib.cupidDatabase(dirs.dbs.control)

    ### Remotes table
    tablename = 'remotes'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'nodeid'},
            {'name':'msgtype'},
            {'name':'keyvalue'},
            {'name':'keyvaluename'},
            {'name':'data'},
            {'name':'time'}
        ])
        if settings['migrate']:
            control_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            control_database.create_table(tablename, schema, queue=True)

    ### Actions table
    tablename = 'actions'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'actionindex', 'type':'integer','primary':True},
            {'name': 'name', 'unique':True, 'default':'myaction'},
            {'name': 'enabled', 'type':'boolean', 'default':0},
            {'name': 'actiontype', 'default':'email'},
            {'name': 'actiondetail', 'default':'info@interfaceinnovationsorg'},
            {'name': 'conditiontype', 'default':'logical'},
            {'name': 'actiondata'},
            {'name': 'value'},
            {'name': 'offdelay', 'type':'real', 'default':0},
            {'name': 'ondelay', 'type':'real', 'default':0},
            {'name': 'active', 'type':'boolean', 'default':0},
            {'name': 'activereset','type':'boolean', 'default':1},
            {'name': 'status','type':'boolean', 'default':0},
            {'name': 'ontime'},
            {'name': 'offtime'},
            {'name': 'actionfrequency','type':'real','default':0},
            {'name': 'lastactiontime'},
            {'name': 'statusmsg','default':'default msg'}
        ])
        if settings['migrate']:
            control_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            control_database.create_table(tablename, schema, queue=True)

        if addentries:
            entries = [
                {'actionindex':1,'name':'System status red','actiontype':'output',
                'actiondetail':'GPIO5','conditiontype':'logical',
                 'actiondata':'condition:[systemdb:systemstatus:systemstatusstatus]==1',
                'enabled':1},
                {'actionindex':2, 'name': 'WAN Access yellow', 'actiontype': 'output',
                 'actiondetail': 'GPIO19', 'conditiontype': 'logical',
                 'actiondata': 'condition:[systemdb:netstatus:WANaccess]==1',
                 'enabled': 1},
                {'actionindex':3, 'name': 'Update IO Status green', 'actiontype': 'output',
                 'actiondetail': 'GPIO6', 'conditiontype': 'logical',
                 'actiondata': 'condition:[systemdb:systemstatus:updateiostatus]==1',
                 'enabled': 1},
                {'actionindex':4, 'name': 'Hamachi Status blue', 'actiontype': 'output',
                 'actiondetail': 'GPIO13', 'conditiontype': 'logical',
                 'actiondata': 'condition:[systemdb:systemstatus:hamachistatus]==1',
                 'enabled': 1},
                # {'actionindex': 5, 'name': 'Voltage monitor', 'actiontype': 'email',
                #  'actiondetail': 'info@interfaceinnovations.org','actionfrequency':300,
                #  'actiondata': "condition:[controldb:inputs:value:id='MOTE1_voltage']<5",
                #  'enabled': 1},
                {'actionindex': 5, 'name': 'Voltage monitor', 'actiontype': 'email',
                 'actiondetail': 'info@interfaceinnovations.org', 'conditiontype':'value', 'actionfrequency': 300,
                 'actiondata': "dbvn:controldb:inputs:value:id='MOTE1_vbat',criterion:4.0,operator:<",'activereset':0,
                 'enabled': 1},
            ]
            control_database.insert(tablename, entries, queue=True)

    ### Indicators table
    tablename = 'indicators'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'name','primary':True},
            {'name':'interface'},
            {'name':'type'},
            {'name':'status', 'type':'boolean'},
            {'name':'detail'}
        ])
        if settings['migrate']:
            control_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            control_database.create_table(tablename, schema, queue=True)

            addentries = True

        if addentries:
            control_database.insert(tablename, {'name':'SPI_RGB1_R', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'red'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB1_G', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'green'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB1_B', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'blue'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB2_R', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'red'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB2_G', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'green'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB2_B', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'blue'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB3_R', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'red'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB3_G', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'green'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB3_B', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'blue'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB4_R', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'red'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB4_G', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'green'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_RGB4_B', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'blue'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_SC_R', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'red'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_SC_G', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'green'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_SC_B', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'blue'}, queue=True)
            control_database.insert(tablename, {'name':'SPI_SC_Y', 'interface':'SPI1', 'type':'CuPIDlights', 'status':0, 'detail':'yellow'}, queue=True)


    ### Defaults table
    tablename = 'defaults'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'valuename', 'primary': True},
            {'name': 'value'}
        ])
        if settings['migrate']:
            prev_table = control_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            prev_table = []
            control_database.create_table(tablename, schema, queue=True)

        # Insert only if it does not override existing entries, as reported by migrate (or empty for initialize)
        inserts = [
            {'valuename':'inputpollfreq', 'value':60},
            {'valuename':'outputpollfreq', 'value':60},
            {'valuename':'inputs_log_options', 'value':'mode:timespan,size:8,unit:hours'},
            {'valuename':'channels_log_options', 'value':'mode:timespan,size:8,unit:hours'}
        ]
        for insert in inserts:
            if not any(insert['valuename'] in row['valuename'] for row in prev_table):
                control_database.insert(tablename, insert, queue=True)

    ### Outputs table
    tablename = 'outputs'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'id','options':'primary'},
            {'name':'interface'},
            {'name':'type'},
            {'name':'address'},
            {'name':'name'},
            {'name':'value','type':'real'},
            {'name':'unit'},
            {'name':'polltime'},
            {'name':'pollfreq'},
            {'name':'ontime'},
            {'name':'offtime'}
        ])
        if settings['migrate']:
            prev_table = control_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            control_database.create_table(tablename, schema, queue=True)

    ### Inputs table
    tablename = 'inputs'
    if tablename in settings['tablelist']:
        control_database.create_table(tablename, pilib.schema.input, queue=True)

    ### OWFS Table
    tablename = 'owfs'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'address', 'options': 'primary'},
            {'name': 'family'},
            {'name': 'id'},
            {'name': 'type'},
            {'name': 'crc8'}
        ])
        control_database.create_table(tablename, schema, queue=True)

    ### Inputs Info Table
    tablename = 'ioinfo'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'id', 'primary':True},
            {'name': 'name'},
            {'name': 'options'}
        ])
        control_database.create_table(tablename, schema, queue=True)

        if addentries:
            control_database.insert(tablename, {'id':'GPIO18','name':'GPIO18'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO23','name':'GPIO23'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO24','name':'GPIO24'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO25','name':'GPIO25 (Boot ok)'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO35','name':'GPIO35 (Undervoltage)'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO4','name':'GPIO4(MB Power)'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO17','name':'GPIO17'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO27','name':'GPIO27'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO22','name':'GPIO22'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO5','name':'GPIO5 - Red Status'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO6','name':'GPIO6 - Green Status'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO13','name':'GPIO13 - Blue Status'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO19','name':'GPIO19 - Yellow Status'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO26','name':'GPIO26 - Other Status'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO16','name':'GPIO16'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO20','name':'GPIO20'}, queue=True)
            control_database.insert(tablename, {'id':'GPIO21','name':'GPIO21'}, queue=True)

    ### Interfaces Table
    tablename = 'interfaces'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'id', 'primary':True},
            {'name': 'interface'},
            {'name': 'type'},
            {'name': 'address'},
            {'name': 'name'},
            {'name': 'options'},
            {'name': 'enabled', 'type':'boolean','default':0},
            {'name': 'status', 'type':'boolean','default':0}
        ])
        control_database.create_table(tablename, schema, queue=True)

        if addentries:
            control_database.insert(tablename, {'interface': 'SPI1', 'type': 'CuPIDlights', 'id': 'SPIout1', 'name': 'myCuPIDlightboard'}, queue=True)
            control_database.insert(tablename, {'interface': 'SPI0', 'type': 'SPITC', 'id': 'SPITC0', 'name': 'mySPITC'}, queue=True)
            control_database.insert(tablename, {'interface': 'I2C', 'type': 'DS2483', 'address':'', 'id': 'I2C_DS2483', 'name': 'I2C 1Wire', 'options':'tempunit:F', 'enabled':0}, queue=True)
            control_database.insert(tablename, {'interface': 'I2C', 'type': 'ADS1115', 'address':'1:48','id': 'I2C_1:48_ADS1115', 'name': 'I2C ADS1115', 'options':'type:diff,gain:16,channel:0', 'enabled':0}, queue=True)
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'18', 'id': 'GPIO18', 'name': 'GPIO 18', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'23', 'id': 'GPIO23', 'name': 'GPIO 23', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'24', 'id': 'GPIO24', 'name': 'GPIO 24', 'options':'mode:input,pullupdown:pullup','enabled':0},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'25', 'id': 'GPIO25', 'name': 'GPIO 25', 'options':'mode:output','enabled':0},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'4', 'id': 'GPIO4', 'name': 'GPIO 4', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'17', 'id': 'GPIO17', 'name': 'GPIO 17', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'27', 'id': 'GPIO27', 'name': 'GPIO 27', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'22', 'id': 'GPIO22', 'name': 'GPIO 22', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'5', 'id': 'GPIO5', 'name': 'GPIO 5', 'options':'mode:output','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'6', 'id': 'GPIO6', 'name': 'GPIO 6', 'options':'mode:output','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'13', 'id': 'GPIO13', 'name': 'GPIO 13', 'options':'mode:output','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'19', 'id': 'GPIO19', 'name': 'GPIO 19', 'options':'mode:output','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'26', 'id': 'GPIO26', 'name': 'GPIO 26', 'options':'mode:output','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'16', 'id': 'GPIO16', 'name': 'GPIO 16', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'20', 'id': 'GPIO20', 'name': 'GPIO 20', 'options':'mode:input,pullupdown:pulldown,function:shutdown,functionstate:true','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'GPIO', 'type': 'GPIO','address':'21', 'id': 'GPIO21', 'name': 'GPIO 21', 'options':'mode:input,pullupdown:pullup','enabled':1},queue=True),
            control_database.insert(tablename, {'interface': 'MOTE', 'type': 'MOTE','address':'1', 'id': '', 'name': 'Gateway Mote', 'enabled':1},queue=True),

    """
    modbustcp Table
    TODO: Double-check to make sure this works the same as qmclibs, which is working nicely
    """

    tablename = 'modbustcp'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'interfaceid'},
            {'name': 'register', 'type':'integer'},
            {'name': 'mode', 'default':'read'},
            {'name': 'length', 'type':'integer', 'default':1},
            {'name': 'bigendian', 'type':'boolean', 'default':1},
            {'name': 'reversebyte', 'type':'boolean', 'default':0},
            {'name': 'reverseword', 'type':'boolean', 'default':0},
            {'name': 'format'},
            {'name': 'options'},
            {'name':'message'}
        ])
        control_database.create_table(tablename, schema, queue=True)

        # querylist.append(
        #     "create table " + tablename + " (interfaceid text, register integer, mode text default 'read', length integer default 1,  "
        #                               "bigendian boolean default 1, reversebyte boolean default 0, format text, options text)")
        if addentries:
            control_database.insert(tablename, {'interfaceid':'MBTCP1', 'register':400001, 'length':2, 'format':'float32'})
            control_database.insert(tablename, {'interfaceid':'MBTCP1', 'register':400003, 'length':2, 'format':'float32'})
            control_database.insert(tablename, {'interfaceid':'MBTCP1', 'register':400005, 'length':2, 'format':'float32'})
            control_database.insert(tablename, {'interfaceid':'MBTCP1', 'register':400007, 'length':2, 'format':'float32'})

    ### LabJack table
    tablename = 'labjack'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'interfaceid'},
            {'name': 'address', 'type': 'integer'},
            {'name': 'mode', 'default': 'read'},
            {'name': 'options'}
        ])
        control_database.create_table(tablename, schema, queue=True)

        if addentries:
            control_database.insert(tablename, {'interfaceid':'USB1','address':0, 'mode':'AIN'})

    ### Controlalgorithms table
    tablename = 'controlalgorithms'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'name', 'primary':True},
            {'name': 'description'},
            {'name': 'maxposrate', 'type':'real', 'default':0},
            {'name': 'maxnegrate', 'type':'real', 'default':0},
            {'name': 'derivativemode', 'default': 'time'},
            {'name': 'derivativeperiod', 'default': 0, 'type':'real'},
            {'name': 'integralmode', 'default': 'time'},
            {'name': 'integralperiod', 'type':'real','default': 0},
            {'name': 'proportional', 'type':'real','default': 1},
            {'name': 'integral', 'type':'real','default': 0},
            {'name': 'derivative', 'type':'real','default': 0},
            {'name': 'deadbandhigh', 'type':'real','default': 0},
            {'name': 'deadbandlow', 'type':'real','default': 0},
            {'name': 'dutypercent', 'type':'real','default': 0},
            {'name': 'dutyperiod', 'type':'real','default': 0},
            {'name': 'minontime', 'type':'real','default': 0},
            {'name': 'minofftime', 'type':'real','default': 0}
        ])
        control_database.create_table(tablename, schema, queue=True)

        if addentries:
            control_database.insert(tablename,{'name':'on/off 1', 'description':'on/off with deadband'}, queue=True)

    ### Algorithmtypes
    tablename = 'algorithmtypes'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'name'}
        ])
        control_database.create_table(tablename, schema, queue=True)

        if addentries:
            control_database.insert(tablename, {'name':'on/off with deadband'})

    ### Channels table
    tablename = 'channels'
    if tablename in settings['tablelist']:
        schema = pilib.schema.channel

        if settings['migrate']:
            print('MIGRATING')
            control_database.settings['quiet'] = False
            control_database.migrate_table(tablename, schema=schema, data_loss_ok=settings['data_loss_ok'])
            addentries = False
        else:
            control_database.create_table(tablename, schema, queue=True)

        if addentries:
            pass
            # TODO: fix channel default entries
            # control_database.insert(tablename, {'channelindex':1,'type':'remote','Kettle'})
            # querylist.append("insert into " + table + " values (1, 'local', 'channel 1', '', 'none', 0, 0, '', 'on/off 1', 'none',0,0,0,65, '', '', 'none', 'none', 0, 'auto', '', 1000,'', '', '')")
            # querylist.append("insert into " + table + " values (1, 'remote', 'Kettle', 'none', 0, 0, '', 'on/off 1', 'none',1,0,0,65, '', '', 'none', 'none', 0, 'auto', '', 1000,'', '', '')")
            # querylist.append("insert into " + table + " values (2, 'remote', 'MLT', 'none', 0, 0, '', 'on/off 1', 'none',1,0,0,65, '', '', 'none', 'none', 0, 'auto', '', 1000,'', '', '')")
            # querylist.append("insert into " + table + " values (3, 'remote', 'HLT', 'none', 0, 0, '', 'on/off 1', 'none',1,0,0,65, '', '', 'none', 'none', 0, 'auto', '', 1000,'', '', '')")

    if control_database.queued_queries:
        print('Executing queue:')
        print(control_database.queued_queries)
        control_database.execute_queue()

    # Check to see everything was created properly. Eventually we can check schema, once we check the schema
    table_names = control_database.get_table_names()
    for table in settings['tablelist']:
        if table not in table_names:
            print(table + ' DOES NOT EXIST')


"""
authlog
"""


def rebuild_sessions_db(**kwargs):

    from iiutilities import dblib
    from cupid.pilib import dirs

    settings = {
        'tablelist':tablenames.sessions,
        'migrate':True,
        'data_loss_ok':False
    }
    settings.update(kwargs)

    session_database = pilib.cupidDatabase(dirs.dbs.session)
    print(session_database.path)

    ### Session limits

    tablename = 'sessionlimits'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'username', 'primary':True},
            {'name':'sessionsallowed', 'type':'integer', 'default':5}
        ])
        if settings['migrate']:
            prev_table = session_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            prev_table = []
            session_database.create_table(tablename, schema, queue=True)

        inserts = [
            {'username': 'viewer', 'sessionsallowed': 5},
            {'username': 'controller', 'sessionsallowed': 5},
            {'username': 'administrator', 'sessionsallowed': 5},
            {'username': 'owner', 'sessionsallowed': 5},
            {'username': 'admin', 'sessionsallowed': 5},
            {'username': 'colin', 'sessionsallowed': 5}
        ]
        for insert in inserts:
            if not any(insert['username'] in prev_entry['username'] for prev_entry in prev_table):
                session_database.insert(tablename, insert, queue=True)

    ### Settings table

    tablename = 'settings'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'sessionlength', 'type':'real', 'default':600},
            {'name':'sessionlimitsenabled', 'type':'real', 'default':1},
            {'name':'updatefrequency','type':'real'}
        ])
        if settings['migrate']:
            prev_table = session_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            prev_table = []
            session_database.create_table(tablename, schema, queue=True)

        if not prev_table:
            session_database.insert(tablename, {'sessionlength':600, 'sessionlimitsenabled':1, 'updatefrequency':30}, queue=True)

    ### Session table

    tablename = 'sessions'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'username'},
            {'name':'sessionid'},
            {'name':'sessionlength'},
            {'name':'time'},
            {'name':'appip'},
            {'name':'realip'}
        ])
        if settings['migrate']:
            prev_table = session_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            session_database.create_table(tablename, schema, queue=True)

    ### Sessions summary

    tablename = 'sessionsummary'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'username', 'primary':True},
            {'name':'sessionsactive', 'type':'real'}
        ])
        if settings['migrate']:
            prev_table = session_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            session_database.create_table(tablename, schema, queue=True)

    ### Session log

    tablename = 'sessionlog'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'username'},
            {'name':'sessionid'},
            {'name':'time'},
            {'name':'action'},
            {'name':'apparentIP'},
            {'name':'realIP'}
        ])
        if settings['migrate']:
            prev_table = session_database.migrate_table(tablename, schema=schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            session_database.create_table(tablename, schema, queue=True)

    if session_database.queued_queries:
        session_database.execute_queue()

"""
System control and information
"""


def rebuild_system_db(**kwargs):
    from iiutilities import dblib
    from cupid.pilib import dirs

    settings = {
        'tablelist': tablenames.sessions,
        'migrate': True,
        'data_loss_ok': False
    }
    settings.update(kwargs)

    system_database = pilib.cupidDatabase(dirs.dbs.system)
    if not settings['tablelist']:
        settings['tablelist'] = tablenames.system

    tablename = 'netstatus'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'WANaccess', 'type':'boolean', 'default':0},
            {'name':'WANaccessrestarts', 'type':'integer', 'default':0},
            {'name':'SSID'},
            {'name':'latency', 'type':'real', 'default':0},
            {'name':'mode', 'default':'eth0wlan0bridge'},
            {'name':'onlinetime'},
            {'name':'offlinetime'},
            {'name':'lastnetreconfig'},
            {'name':'netstate','type':'integer', 'default':0},
            {'name':'netstateoktime'},
            {'name':'updatetime'},
            {'name':'statusmsg'},
            {'name':'netrebootcounter', 'type':'integer', 'default':0},
            {'name':'addresses'}
        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert_defaults(tablename, queue=True)

    tablename = 'wirelessnetworks'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'SSID', 'primary':True},
            {'name':'strength'},
            {'name':'data'}
        ])
        system_database.create_table(tablename, schema, queue=True)

    tablename = 'netconfig'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'requireWANaccess', 'type':'integer', 'default':1},
            {'name': 'WANretrytime', 'type':'integer', 'default':30},
            {'name': 'mode', 'default':'eth0wlan0bridge'},
            {'name': 'hamachiwatchdogip', 'default':'25.11.87.7'},
            {'name': 'SSID'},
            {'name': 'aprevert'},
            {'name': 'addtype', 'default':'dhcp'},
            {'name': 'address', 'default':'192.168.1.30'},
            {'name': 'gateway', 'default':'192.168.8.1'},
            {'name': 'dhcpstart', 'default':'192.168.8.70'},
            {'name': 'dhcpend', 'default':'192.168.8.99'},
            {'name': 'apreverttime', 'type':'integer','default':60},
            {'name': 'stationretrytime', 'type':'integer','default':300},
            {'name': 'laststationretry'},
            {'name': 'pingthreshold','type':'integer','default':2000},
            {'name': 'netstatslogenabled','type':'boolean','default':0},
            {'name': 'netstatslogfreq','type':'integer','default':60},
            {'name': 'apoverride','type':'boolean','default':0},
            {'name': 'apoverridepin','type':'integer','default':21},
            {'name': 'rebootonfail','type':'boolean','default':0},
            {'name': 'rebootfailperiod','type':'integer','default':900}
        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert_defaults(tablename, queue=True)

    tablename = 'systemflags'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'name'},
            {'name': 'value', 'type': 'boolean', 'default': 0}
        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert(tablename, [
            {'name':'reboot'},
            {'name':'netconfig'},
            {'name':'updateiicontrollibs'},
            {'name':'updatecupidweblib'}
        ], queue=True)

    tablename = 'metadata'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'name'},
            {'name':'value'}
            ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert(tablename, [
            {'name': 'devicename', 'value':'My CuPID'},
            {'name': 'groupname', 'value':'None'}
        ], queue=True)

    tablename = 'systemstatus'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'systemstatusenabled', 'type': 'boolean', 'default': 1},
            {'name': 'systemstatusstatus', 'type': 'boolean', 'default': 0},
            {'name': 'systemstatusfreq', 'type': 'integer', 'default': 15},
            {'name': 'lastsystemstatuspoll'},
            {'name': 'systemmessage'},

            {'name': 'webserver','default':'nginx'},

            {'name': 'picontrolenabled', 'type': 'boolean', 'default': 0},
            {'name': 'picontrolstatus', 'type': 'boolean', 'default': 0},
            {'name': 'picontrolfreq', 'type': 'integer', 'default': 15},
            {'name': 'lastpicontrolpoll'},

            {'name': 'updateioenabled', 'type': 'boolean', 'default': 0},
            {'name': 'updateiostatus', 'type': 'boolean', 'default': 0},
            {'name': 'updateiofreq', 'type': 'integer', 'default': 15},
            {'name': 'lastupdateiopoll'},

            {'name': 'serialhandlerenabled', 'type': 'boolean', 'default': 0},
            {'name': 'serialhandlerstatus', 'type': 'boolean', 'default': 0},

            {'name': 'sessioncontrolenabled', 'type': 'boolean', 'default': 0},
            {'name': 'sessioncontrolstatus', 'type': 'boolean', 'default': 0},
            {'name': 'sessioncontrolfreq', 'type': 'integer', 'default': 15},
            {'name': 'lastsessioncontrolpoll'},

            {'name': 'enableoutputs', 'type': 'boolean', 'default': 0},
            {'name': 'netstatusenabled', 'type': 'boolean', 'default': 0},
            {'name': 'netconfigenabled', 'type': 'boolean', 'default': 0},
            {'name': 'checkhamachistatus', 'type': 'boolean', 'default': 1},
            {'name': 'hamachistatus', 'type': 'boolean', 'default': 0},

        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert_defaults(tablename, queue=True)

    tablename = 'logconfig'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'network', 'type':'integer', 'default':4},
            {'name': 'io', 'type':'integer', 'default':4},
            {'name': 'system', 'type':'integer', 'default':4},
            {'name': 'control', 'type':'integer', 'default':4},
            {'name': 'daemon', 'type':'integer', 'default':4},
            {'name': 'remote', 'type':'integer', 'default':4},
            {'name': 'serial', 'type':'integer', 'default':4},
            {'name': 'notifications', 'type':'integer', 'default':4},
            {'name': 'daemonproc', 'type':'integer', 'default':4},
            {'name': 'error', 'type':'integer', 'default':4}
        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert_defaults(tablename, queue=True)

    tablename = 'notifications'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'item', 'primary':True},
            {'name': 'enabled', 'type':'boolean', 'default':0},
            {'name': 'options'},
            {'name': 'lastnotification'}
            ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert(tablename, [
            {'item':'unittests', 'enabled':1, 'options':'type:email,email:cupid_status@interfaceinnovations.org,frequency:600'},
            {'item':'daemonkillproc', 'enabled':1, 'options':'type:email,email:cupid_status@interfaceinnovations.org,frequency:600'},
            {'item':'boot', 'enabled':1, 'options':'type:email,email:cupid_status@interfaceinnovations.org,frequency:600'}
        ], queue=True)



    tablename = 'uisettings'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'setting'},
            {'name':'group'},
            {'name':'value'}
        ])
        system_database.create_table(tablename, schema, queue=True)
        system_database.insert(tablename, [
            {'setting': 'showinputgpiologs', 'group': 'dataviewer', 'value':'0'},
            {'setting': 'showinput1wirelogs', 'group': 'dataviewer', 'value':'1'},
            {'setting': 'showchannellogs', 'group': 'dataviewer', 'value':'1'},
            {'setting': 'showotherlogs', 'group': 'dataviewer', 'value':'1'},
        ], queue=True)

    tablename = 'versions'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'item', 'primary':True},
            {'name': 'version'},
            {'name': 'versiontime'},
            {'name': 'updatetime'}
            ])
        system_database.create_table(tablename, schema, queue=True)

    if system_database.queued_queries:
        print('executing queries')
        system_database.execute_queue()

    # Check to see everything was created properly. Eventually we can check schema, once we check the schema
    table_names = system_database.get_table_names()
    for table in settings['tablelist']:
        if table not in table_names:
            print(table + ' DOES NOT EXIST')



"""
recipesdata
"""


def rebuild_recipes_db(**kwargs):
    from iiutilities  import dblib
    from cupid.pilib import dirs

    recipes_db = pilib.cupidDatabase(dirs.dbs.recipe)

    settings = {
        'tablelist':['recipes']
    }
    settings.update(kwargs)
    if 'recipes' in settings['tablelist']:
        tablename = 'stdreflow'
        recipes_db.drop_table(tablename, queue=True)
        table_schema = dblib.sqliteTableSchema([
            {'name': 'stagenumber', 'type': 'integer', 'options': 'primary'},
            {'name': 'stagelength', 'type': 'real'},
            {'name': 'setpointvalue', 'type': 'real'},
            {'name': 'lengthmode', 'type': 'real'},
            {'name': 'controlalgorithm', 'type': 'real', 'options':"default 'on/off 1'"},
        ])
        recipes_db.create_table(tablename, table_schema, queue=True)

    if recipes_db.queued_queries:
        print('executing queue')
        recipes_db.execute_queue()

    print('reading table ...')
    recipes_db.read_table('stdreflow')

"""
Notifications (mail, IFFFT, etc) data
"""


def rebuild_notifications_db(**kwargs):
    from iiutilities import dblib
    from cupid.pilib import dirs

    settings = {
        'tablelist': tablenames.sessions,
        'migrate': True,
        'data_loss_ok': False
    }
    settings.update(kwargs)

    if not settings['tablelist']:
        settings['tablelist'] = tablenames.notifications

    notifications_database = pilib.cupidDatabase(dirs.dbs.notifications)

    tablename = 'queued'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'queuedtime','primary':True},
            {'name':'type','default':'email'},
            {'name':'message'},
            {'name':'options'},
        ])
        if settings['migrate']:
            notifications_database.migrate_table(tablename, schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            notifications_database.create_table(tablename, schema, queue=True)

    tablename = 'sent'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name':'queuedtime','primary':True},
            {'name':'senttime'},
            {'name':'type'},
            {'name':'message'},
            {'name':'options'}
        ])
        if settings['migrate']:
            notifications_database.migrate_table(tablename, schema, queue=True, data_loss_ok=settings['data_loss_ok'])
        else:
            notifications_database.create_table(tablename, schema, queue=True)

    if notifications_database.queued_queries:
        print(notifications_database.queued_queries)
        notifications_database.execute_queue()

    # Check to see everything was created properly. Eventually we can check schema, once we check the schema
    table_names = notifications_database.get_table_names()
    for table in settings['tablelist']:
        if table not in table_names:
            print(table + ' DOES NOT EXIST')

"""
Motes raw data
"""

def rebuild_motes_db(**kwargs):
    from cupid.pilib import dirs
    from iiutilities import dblib

    settings = {
        'tablelist': tablenames.sessions,
        'migrate': True,
        'data_loss_ok': False
    }
    settings.update(kwargs)

    motes_database = pilib.cupidDatabase(dirs.dbs.motes)

    tablename = 'read'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'time', 'primary':True},
            {'name': 'message'}
        ])
        motes_database.create_table(tablename, schema, queue=True)

    tablename = 'queued'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'queuedtime', 'primary': True},
            {'name': 'message'}
        ])
        motes_database.create_table(tablename, schema, queue=True)

    tablename = 'sent'
    if tablename in settings['tablelist']:
        schema = dblib.sqliteTableSchema([
            {'name': 'queuedtime', 'primary': True},
            {'name': 'senttime'},
            {'name': 'message'}
        ])
        motes_database.create_table(tablename, schema, queue=True)

    if motes_database.queue_queries:
        motes_database.execute_queue()


"""
userstabledata
"""


def rebuild_users_data(argument=None):
    from cupid.pilib import dirs
    from iiutilities.datalib import gethashedentry
    from iiutilities.dblib import sqlitemultquery

    querylist = []
    runquery = True

    querylist.append('drop table if exists users')
    enteringusers = True
    runquery = False
    index = 1
    querylist.append(
        'create table users (id integer primary key not null, name text unique, password text not null, email text not null, temp text not null, authlevel integer default 0)')
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
            userinput = input("Enter username or Q to stop: ")
            if userinput == 'Q':
                print('exiting ...')
                break
            passone = input("Enter password: ")
            passtwo = input("Confirm password: ")
            emailentry = input("Enter user email")
            authlevelentry = input("Enter authorization level (0-5)")

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


"""
# safedata
"""


def rebuild_wireless_data(preserve=True):
    from iiutilities.dblib import sqlitemultquery, gettablenames, readalldbrows
    from cupid.pilib import dirs

    querylist = []
    querylist.append('drop table if exists wireless')
    querylist.append('create table wireless (SSID text primary key, password text, auto integer default 1, priority integer default 1)')

    safetables = gettablenames(dirs.dbs.safe)
    print('tables : ')
    print(safetables)

    wirelessentries = []
    existing_ssids = []
    if 'wireless' in safetables:
        # print("wireless table found")
        wirelessentries = readalldbrows(dirs.dbs.safe, 'wireless')
        existing_ssids = [entry['SSID'] for entry in wirelessentries]

        for index,entry in enumerate(wirelessentries):
            querylist.append("insert into wireless values('" + entry['SSID'] + "','" + entry['password'] + "',1," + str(index+1) + ')')

    if 'leHouse' not in existing_ssids:
        querylist.append(
            "insert into wireless values('leHouse','ilovetheinternet',1,1)")

    # print(querylist)
    sqlitemultquery(dirs.dbs.safe, querylist)


def rebuild_ap_data(SSID='cupidwifi', password='cupidpassword'):
    from iiutilities.dblib import sqlitemultquery
    from cupid.pilib import dirs
    querylist = []
    querylist.append('drop table if exists apsettings')
    querylist.append("create table apsettings (SSID text default 'cupidwifi', password text default 'cupidpassword')")
    querylist.append(
                "insert into apsettings values('" + SSID + "','" + password + "')")
    sqlitemultquery(dirs.dbs.safe, querylist)


def rebuild_api_data():
    from iiutilities import dblib
    from cupid.pilib import dirs
    api_id = input('Enter API ID: ')
    api_key = input('Enter API Key: ')
    api_schema = dblib.sqliteTableSchema([{'name':'id','primary':True},{'name':'key'}])
    safe_db = pilib.cupidDatabase(dirs.dbs.safe)
    safe_db.create_table('api', api_schema, queue=True)
    safe_db.insert('api',{'id':api_id, 'key':api_key}, queue=True)
    safe_db.execute_queue()
    
    
def rebuild_data_agent():
    # We have a system data_agent table so that we can write to it without locking the io db.
    
    # data_agent_schema
    pass
    
def maketruetabledict(namelist):
    truetabledict = {}
    for name in namelist:
        truetabledict[name] = True
    return truetabledict

# default routine
if __name__ == "__main__":
    import sys

    # Check for DEFAULTS argument

    if len(sys.argv) > 1 and sys.argv[1] == 'DEFAULTS':
        print('making default databases')
        rebuild_wireless_data()

        # This checks the hostname, sets it as the hostname with 'cupid' prefix, and sets default password
        # Then it calls the file rebuild
        from netconfig import setdefaultapsettings
        setdefaultapsettings()
        rebuild_users_data('defaults')

        rebuild_control_db(tablelist=tablenames.control)
        rebuild_system_db(tablelist=tablenames.system)
        rebuild_motes_db(tablelist=tablenames.motes)
        rebuild_notifications_db(tablelist=tablenames.notifications)
        rebuild_recipes_db()
        rebuild_sessions_db(tablelist=tablenames.sessions)

        # rebuild data_agent dictionary
        from iiutilities.data_agent import rebuild_data_agent_db
        rebuild_data_agent_db()

    elif len(sys.argv) > 1:
        if sys.argv[1] in tablenames.control:
            print('running rebuild control tables for ' + sys.argv[1])
            rebuild_control_db(tablelist=[sys.argv[1]])
        elif sys.argv[1] in tablenames.system:
            print('running rebuild system tables for ' + sys.argv[1])
            rebuild_system_db(tablelist=[sys.argv[1]])
        elif sys.argv[1] in tablenames.motes:
            print('running rebuild motes tables for ' + sys.argv[1])
            rebuild_motes_db(tablelist=[sys.argv[1]])
        elif sys.argv[1] in ['notifications', 'Notifications']:
            print('running rebuilding notifications table')
            rebuild_notifications_db()
        elif sys.argv[1] in ['wirelessdata']:
            print('running rebuild wireless safedata')
            rebuild_wireless_data()
        elif sys.argv[1] in ['users']:
            rebuild_users_data('defaults')

    else:

        print("** Motes tables **")
        tablestorebuild = []
        execute = False
        for table in tablenames.motes:
            answer = input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuild_motes_db(maketruetabledict(tablestorebuild))

        print("** Control tables **")
        tablestorebuild = []
        execute = False
        for table in tablenames.control:
            answer = input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuild_control_db(maketruetabledict(tablestorebuild))

        print("** System tables **")
        tablestorebuild = []
        execute = False
        for table in tablenames.system:
            answer = input('Rebuild ' + table + ' table (y/N)?')
            if answer == 'y':
                execute = True
                tablestorebuild.append(table)
        if execute:
            rebuild_system_db(maketruetabledict(tablestorebuild))

        answer = input('Rebuild wireless table (y/N)?')
        if answer == 'y':
            rebuild_wireless_data()

        answer = input('Rebuild AP table (y/N)?')
        if answer == 'y':
            rebuild_ap_data()

        answer = input('Rebuild users table (y/N)?')
        if answer == 'y':
            rebuild_users_data()

        recipetabledict = {}
        answer = input('Rebuild recipes table (y/N)?')
        if answer == 'y':
            recipetabledict['recipes'] = True
        rebuild_recipes_db(recipetabledict)

        answer = input('Rebuild sessions table (y/N)?')
        if answer == 'y':
            rebuild_sessions_db()
