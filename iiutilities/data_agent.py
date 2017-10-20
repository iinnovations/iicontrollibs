#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys
from iiutilities import dblib
import simplejson as json

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from iiutilities.utility import Bunch

da_vars = Bunch()
da_vars.default_agent_item_options = {
        'mode':'single',
        'bunch_period':5.0,
        'transmit_period':60.0,
        'full_entry':True
    }

da_vars.schema = Bunch()
da_vars.schema.send_items = dblib.sqliteTableSchema([
    {'name': 'id', 'primary': True},
    {'name': 'enabled', 'type':'boolean', 'default':1},
    {'name': 'last_transmit'},
    {'name': 'options'}
])


def rebuild_data_agent_db(**kwargs):

    settings = {
        'path':'/var/www/data/dataagent.db',
        'tablelist':['send_items'],
        'migrate':True,
        'data_loss_ok':True
    }
    settings.update(kwargs)

    data_agent_db = dblib.sqliteDatabase(settings['path'])

    ### Data Agent table
    tablename = 'send_items'
    if tablename in settings['tablelist']:
        print('rebuilding {}'.format(tablename))

        if settings['migrate']:
            data_agent_db.migrate_table(tablename, schema=da_vars.schema.send_items, queue=True,
                                          data_loss_ok=settings['data_loss_ok'])
        else:
            data_agent_db.create_table(tablename, schema=da_vars.schema.send_items, queue=True)

        data_agent_db.insert(tablename, {'id': 'MOTE1_vbat', 'last_transmit': '',
                                             'options': json.dumps(da_vars.default_agent_item_options)}, queue=True)
        data_agent_db.insert(tablename, {'id': 'MOTE1_vout', 'last_transmit': '',
                                             'options': json.dumps(da_vars.default_agent_item_options)}, queue=True)

    # TODO: Add more details settings tables here.
    data_agent_db.execute_queue()


def get_client_tables(clientid='testclient', **kwargs):

    json_headers = {'content-type': 'application/json'}

    from iiutilities.netfun import post_data
    settings = {
        'id':'testclient',
        'key':'demo',
        'url':'https://cupidcontrol.com/cupidapi',
        'action':'get_client_tables',
    }
    settings.update(kwargs)
    data_dict = {
        'id': settings['id'],
        'key': settings['key'],
        'action':settings['action'],
        'read_clientid': clientid,
    }
    results = post_data(settings['url'], data_dict, headers=json_headers)
    tablenames = []
    if 'tablenames' in results:
        tablenames = results['tablenames']
    return {'results':results, 'tablenames':tablenames}


def post_client_data(**kwargs):

    # TODO: Build in return status on top of debug.

    from iiutilities.netfun import post_data

    json_headers = {'content-type': 'application/json'}
    # json_headers = {'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    settings = {
        'url':'https://cupidcontrol.com/cupidapi',
        'action':'post_data',
        'header_type':'json',
        'autofill_client':True,
        'debug':False
    }
    settings.update(kwargs)

    # Default to hostname and salted key.
    # TODO: Update to salt that does not live in a public repo.
    if 'client_id' not in kwargs or 'client_key' not in kwargs:
        if settings['autofill_client']:
            import socket
            from iiutilities.datalib import gethashedentry

            hostname = socket.gethostname()
            key = gethashedentry(hostname, '{}_pwd'.format(hostname), salt='my databot salt')

            settings['client_id'] = hostname
            settings['client_key'] = key
        else:
            if settings['debug']:
                print('Client id and/or key not provided, and autofill_client not selected. Aborting ')
            return None

    if not 'post_data' in settings:
        if settings['debug']:
            print(' No post_data provided. Aborting ')
        return None

    data_dict = {
        # 'id': settings['id'],
        'client_key': settings['client_key'],
        'action':settings['action'],
        'client_id': settings['client_id'],
        'post_data':settings['post_data']
    }
    if settings['debug']:
        print('sending {}'.format(data_dict))
    response = post_data(settings['url'], json.dumps(data_dict), headers=json_headers)
    return response


def test_post_client_data():
    from iiutilities.datalib import gettimestring
    from decimal import Decimal
    data = {
        'test_value': {
            'time':gettimestring(),
            'value':Decimal(99)
        }
    }
    response = post_client_data(**{'post_data':data})
    return response


def auto_populate_data_agent_send_items(**kwargs):
    settings = {
        'debug': False,
        'agent_db_path': '/var/www/data/dataagent.db',
        'inputs_db_path': '/var/www/data/control.db',
        'inputs_table': 'inputs',
        'empty_table': True,
        'interface_includes': {
            'gpio':False,
            'mote':True,
            '1wire':True
        },
        'tablename':'send_items'
    }

    settings.update(kwargs)
    inputs_db = dblib.sqliteDatabase(settings['inputs_db_path'])
    agent_db = dblib.sqliteDatabase(settings['agent_db_path'])
    if settings['empty_table']:
        agent_db.empty_table(settings['tablename'], queue=True)

    for input_entry in inputs_db.read_table('inputs'):
        insert_this_entry = False
        if input_entry['interface'].lower() in settings['interface_includes'] and settings['interface_includes'][input_entry['interface'].lower()]:
            insert_this_entry = True

        if insert_this_entry:
            agent_db.insert(settings['tablename'], {'id': input_entry['id'], 'last_transmit': '',
                                               'options': json.dumps(da_vars.default_agent_item_options)}, queue=True)

    agent_db.execute_queue()


def run_data_agent(**kwargs):

    from iiutilities.datalib import gettimestring, timestringtoseconds

    settings = {
        'debug':False,
        'agent_db_path':'/var/www/data/dataagent.db',
        'inputs_db_path':'/var/www/data/control.db',
        'inputs_table':'inputs'
    }
    settings.update(kwargs)

    data_agent_db = dblib.sqliteDatabase(settings['agent_db_path'])
    inputs_db = dblib.sqliteDatabase(settings['inputs_db_path'])

    # get data_agent items
    data_agent_entries = data_agent_db.read_table('send_items')

    inputs = inputs_db.read_table('inputs')
    inputs_dict = {}
    for input in inputs:
        inputs_dict[input['id']] = input

    current_time = gettimestring()


    post_data = {
        'post_time':current_time,
        'data':{}
    }
    maybe_xmit = {}

    """ 
    Loop through to find things that definitely need to be transmitted. 
    Also, find if there are things that should be transmitted within a fixed window (bunch_period)
    If we are going to transmit anyway, attach these items. This way if we barely miss a transmit event, we will
    still send it and not waste data on two sets of headers.
    """

    for entry in data_agent_entries:
        if entry['enabled']:
            if settings['debug']:
                print('{} Enabled '.format(entry['id']))
            options = json.loads(entry['options'])

            da_vars.default_agent_item_options.update(options)
            options = da_vars.default_agent_item_options

            # TODO: Build in other modes besides single.
            # Build in modularity for other ordinates.

            send = False
            if not entry['last_transmit']:
                send = True
            else:
                elapsed_since_xmit = timestringtoseconds(current_time) - timestringtoseconds(entry['last_transmit'])
                if elapsed_since_xmit > options['transmit_period']:
                    send = True
                elif (elapsed_since_xmit + options['bunch_period']) > options['transmit_period']:
                    if entry['id'] in inputs_dict:
                        # maybe send.
                        if options['full_entry']:
                            maybe_xmit[entry['id']] = [inputs_dict[entry['id']]]
                        else:
                            maybe_xmit[entry['id']] = [{'polltime':inputs_dict[entry['id']]['polltime'], 'value': inputs_dict[entry['id']]['value']}]
        else:
            if settings['debug']:
                print('{} Disabled '.format(entry['id']))

        if send:
            if settings['debug']:
                print('Sending {}'.format(entry['id']))

            if entry['id'] in inputs_dict:
                if options['full_entry']:
                    post_data['data'][entry['id']] = [inputs_dict[entry['id']]]
                else:
                    post_data['data'][entry['id']] = [{'polltime':inputs_dict[entry['id']]['polltime'], 'value': inputs_dict[entry['id']]['value']}]

        else:
            if settings['debug']:
                print('Not sending {}'.format(entry['id']))
    """
    Now determine whether we have data that definitely needs to be sent. If so, throw the bunch data in.
    """

    if post_data['data']:
        post_data['data'].update(maybe_xmit)
        if settings['debug']:
            print('TIME TO SEND THIS STUFF')
            print(post_data)

    try:
        response = post_client_data(**{'post_data':post_data})
    except:

        import traceback
        trace_message = traceback.format_exc()
        if settings['debug']:
            print('Error, traceback: \n{}'.format(trace_message))
        return {'status':1, 'message':trace_message}
    else:
        if settings['debug']:
            print('SUCCESS')

        # Now we need to mark entries as sent
        for entry_name, entry in post_data['data'].items():
            data_agent_db.set_single_value('send_items', 'last_transmit', current_time, condition="id='{}'".format(entry_name), queue=True)

        data_agent_db.execute_queue()

    return response

if __name__ == '__main__':
    response = run_data_agent(debug=True)
    print('Full response: ')
    print(response)