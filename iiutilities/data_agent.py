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
try:
    import simplejson as json
except:
    import json

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

from iiutilities import dblib
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
            '1wire':True,
            'lan':True
        },
        'tablename':'send_items',
        'debug':True
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

    if settings['debug']:
        print(agent_db.queued_queries)
    agent_db.execute_queue()


def run_data_agent(**kwargs):

    from iiutilities.datalib import gettimestring, timestringtoseconds

    settings = {
        'debug':False,
        'agent_db_path':'/var/www/data/dataagent.db',
        'inputs_db_path':'/var/www/data/control.db',
        'inputs_table':'inputs',
        'send_all':False
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

    """ 
    Loop through to find things that definitely need to be transmitted. 
    Also, find if there are things that should be transmitted within a fixed window (bunch_period)
    If we are going to transmit anyway, attach these items. This way if we barely miss a transmit event, we will
    still send it and not waste data on two sets of headers.
    """

    """ 
    Data has following format:
    post_data = 
    {
      'post_time':current_time,
      'data': [
        {
          id : data_id,
          name : common name (optional)
          data : [
            data entry,
            data entry,
            ...
        }
      ],
      ...
    }
    """
    post_data = {
        'post_time': current_time,
        'data': []
    }
    maybe_xmit = []

    for agent_entry in data_agent_entries:
        if agent_entry['enabled']:
            if settings['debug']:
                print('{} Enabled '.format(agent_entry['id']))
            options = json.loads(agent_entry['options'])

            da_vars.default_agent_item_options.update(options)
            options = da_vars.default_agent_item_options

            # TODO: Build in other modes besides single.
            # Build in modularity for other ordinates.

            # Create the entry
            if agent_entry['id'] not in inputs_dict:
                if settings['debug']:
                    print('input id {} not found '.format(agent_entry['id']))
                continue

            inputs_entry = inputs_dict[agent_entry['id']]

            send_entry = {
                'id': agent_entry['id']
            }
            if 'name' in inputs_dict[agent_entry['id']]:
                send_entry['name'] = inputs_entry['name']

            if options['full_entry']:
                send_entry['data'] = [inputs_entry]
            else:
                send_entry['data'] = [{'id': agent_entry['id'], 'polltime':inputs_entry['polltime'],
                                   'value': inputs_entry['value']}]

            send = False
            maybe_send = False
            if not agent_entry['last_transmit'] or settings['send_all']:
                send = True
            else:
                elapsed_since_xmit = timestringtoseconds(current_time) - timestringtoseconds(agent_entry['last_transmit'])
                if elapsed_since_xmit > options['transmit_period']:
                    send = True
                elif (elapsed_since_xmit + options['bunch_period']) > options['transmit_period']:
                    maybe_send = True

        else:
            if settings['debug']:
                print('{} Disabled '.format(agent_entry['id']))

        if send:
            if settings['debug']:
                print('Sending "{}"'.format(agent_entry['id']))
            post_data['data'].append(send_entry)

        elif maybe_send:
            if settings['debug']:
                print('Sending "{}"'.format(agent_entry['id']))
            maybe_send.append(send_entry)

        else:
            if settings['debug']:
                print('Not sending {}'.format(agent_entry['id']))
    """
    Now determine whether we have data that definitely needs to be sent. If so, throw the bunch data in.
    """

    if post_data['data']:
        post_data['data'].extend(maybe_xmit)
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
        for entry in post_data['data']:
            data_agent_db.set_single_value('send_items', 'last_transmit', current_time, condition="id='{}'".format(entry['id']), queue=True)

        data_agent_db.execute_queue()

    return response

if __name__ == '__main__':
    response = run_data_agent(debug=True, send_all=True)
    print('Full response: ')
    print(response)