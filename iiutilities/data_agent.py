#!/usr/bin/env python

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

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


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

    from iiutilities.netfun import post_data

    json_headers = {'content-type': 'application/json'}

    settings = {
        'client_id':'test_client',
        'key':'demo',
        'url':'https://cupidcontrol.com/cupidapi',
        'action':'post_data',
        'header_type':'json',
    }
    settings.update(kwargs)

    if not 'post_data' in settings:
        print(' No post_data provided. Aborting ')
        return None

    data_dict = {
        # 'id': settings['id'],
        'key': settings['key'],
        'action':settings['action'],
        'post_client_id': settings['client_id'],
        'post_data':settings['post_data']
    }
    results = post_data(settings['url'], data_dict, headers=json_headers)
    tablenames = []
    if 'tablenames' in results:
        tablenames = results['tablenames']
    return {'results':results, 'tablenames':tablenames}


def test_post_client_data():
    from iiutilities.datalib import gettimestring
    from decimal import Decimal
    data = {
        'time':gettimestring(),
        'value':Decimal(99)
    }
    post_client_data(**{'post_data':data})