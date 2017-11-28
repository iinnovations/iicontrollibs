from iiutilities import dblib
from iiutilities.utility import datalib


def application(environ, start_response):

    import cgi
    import json
    import os, sys, inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0, top_folder)

    # post_env = environ.copy()
    # post_env['QUERY_STRING'] = ''
    # post = cgi.FieldStorage(
    #     fp=environ['wsgi.input'],
    #     environ=post_env,
    #     keep_blank_values=True
    # )
    #
    # formname=post.getvalue('name')
    # data={}
    # post = {}
    # for k in post.keys():
    #     post[k] = post.getvalue(k)

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    post = json.loads(request_body.decode('utf-8'))

    output = {}
    output['message'] = ''

    status = '200 OK'

    # Get GPIO status
    # We return this status no matter what

    gpiolist = [18,23,24,25,4,17,21,22]
    import cupid.pilib as pilib
    inputs = dblib.readalldbrows(pilib.dirs.dbs.control, 'inputs')
    interfaces = dblib.readalldbrows(pilib.dirs.dbs.control, 'interfaces')

    statusdict={}
    for input in inputs:
        statusdict[input['id'] + 'value'] = input['value']
    for interface in interfaces:
        if interface['type'] == 'GPIO':
            options = datalib.parseoptions(interface['options'])
            statusdict[interface['id'] + 'mode'] = options['mode']

    # Execute commands
    if 'action' in post:
        querylist = []
        if post['action'] == 'toggleGPIOmode':
            print('stuff')
        elif post['action'] == 'toggleGPIOvalue':
            outputs = dblib.readalldbrows(pilib.dirs.dbs.control, 'outputs')
            for output in outputs:
                if output['id'] == post['GPIOid']:
                    curval = output['value']
                    if curval == 0:
                        setval = 1
                    else:
                        setval = 0
                    querylist.append('update outputs set value= ' + str(setval) + ' where id=\'' + post['GPIOid'] + '\'')
        elif post['action'] == 'wptoggleGPIOvalue':
            try:
                BCMpin = int(post['BCMpin'])
            except KeyError:
                data['message'] = 'No pin sent with command'
            else:
                from subprocess import check_output, call

                output = int(check_output(['gpio','-g','read',str(BCMpin)]).decode('utf-8'))
                # call(['gpio','export','18','output'])
                if output == 0:
                    call(['gpio','-g','write',str(BCMpin),'1'])
                else:
                    call(['gpio','-g','write',str(BCMpin),'0'])

        elif post['action'] == 'wptoggleGPIOmode':
            try:
                BCMpin = int(post['BCMpin'])
            except KeyError:
                data['message'] = 'No pin sent with command'
            else:
                from subprocess import check_output, call
                from cupid.pilib import getgpiostatus

                pinmode = ''
                allstatus = getgpiostatus()
                for status in allstatus:
                    if status['BCM'] == BCMpin:
                        pinmode = status['mode']

                if pinmode == 'OUT':
                    call(['gpio','-g','mode',BCMpin,'in'])
                else:
                    call(['gpio','-g','mode',BCMpin,'out'])

        elif post['action'] == 'wpgetgpiostatus':
            from cupid.pilib import getgpiostatus
            data = getgpiostatus()


    output = json.dumps(data, indent=1)
    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)

    return [output]




