def application(environ, start_response):

    import cgi
    import json

    import os,sys,inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    from cupid.pilib import sqlitedatadump

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')
    data={}
    d = {}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'


    # Execute commands


    # Get GPIO status

    gpiolist = [18,23,24,25,4,17,21,22]
    import cupid.pilib as pilib
    inputs = pilib.readalldbrows(pilib.controldatabase, 'inputs')
    interfaces = pilib.readalldbrows(pilib.controldatabase, 'interfaces')

    statusdict={}
    for input in inputs:
        statusdict[input['id'] + 'value'] = input['value']
    for interface in interfaces:
        if interface['type'] == 'GPIO':
            options = pilib.parseoptions(interface['options'])
            statusdict[interface['id'] + 'mode'] = options['mode']

    output = json.dumps(statusdict, indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status,response_headers)

    return [output]

