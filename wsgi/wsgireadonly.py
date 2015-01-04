def application(environ, start_response):
    import cgi
    import json

    # Set top folder to allow import of modules

    import os, sys, inspect

    top_folder = \
        os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0, top_folder)

    from cupid.pilib import dynamicsqliteread, gettablenames, sqlitequery, switchtablerows
    from time import time

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname = post.getvalue('name')
    output = {}
    d = {}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'
    # Run stuff as requested
    # We use the dynamic function to allow various  
    # types of queries
    if 'specialaction' in d:
        if d['specialaction'] == 'gettablenames':
            output['data'] = gettablenames(d['database'])
        elif d['specialaction'] == 'switchtablerows':
            switchtablerows(d['database'], d['table'], d['row1'], d['row2'], d['uniqueindex'])
        elif d['specialaction'] == 'modwsgistatus':
            output['processgroup'] = repr(environ['mod_wsgi.process_group'])
            output['multithread'] = repr(environ['wsgi.multithread'])

    # TODO: Add an action type here, like 'gettable'
    elif 'tables[]' in d:  # Get multiple tables
        data = []
        if 'start' in d:
            fixedstart = int(d['start'])
        else:
            fixedstart = 0
        if 'length' in d:
            fixedlength = int(d['length'])
        else:
            fixedlength = 1
        if 'lengths[]' in d:
            lengths = map(int, d['lengths[]'])
        else:
            lengths = []
        if 'starts[]' in d:
            starts = map(int, d['starts'])
        else:
            starts = []

        for index, table in enumerate(d['tables[]']):
            try:
                length = lengths[index]
            except IndexError:
                length = fixedlength
            try:
                start = starts[index]
            except IndexError:
                start = fixedstart

            data.append(dynamicsqliteread(d['database'], table, start, length))
            output['data']=data
    elif 'length' in d:  # Handle table row subset
        if not 'start' in d:
            d['start'] = 0
        thetime = time();
        output['data'] = dynamicsqliteread(d['database'], d['table'], d['start'], d['length'])
        output['querytime'] = time() - thetime
    elif 'row' in d:  # Handle table row
        thetime = time();
        output['data'] = dynamicsqliteread(d['database'], d['table'], d['row'])
        output['querytime'] = time() - thetime
    elif 'table' in d:  # Handle entire table
        thetime = time();
        if 'condition' in d:
            if not d['condition'] == '':
                output['data'] = dynamicsqliteread(d['database'], d['table'], condition=d['condition'])
            else:
                output['data'] = dynamicsqliteread(d['database'], d['table'])
        else:
            output['data'] = dynamicsqliteread(d['database'], d['table'])
        output['querytime'] = time() - thetime
    else:
        output['data'] = 'no data'
        output['message'] = 'no command matched'

    foutput = json.dumps(output, indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)

    return [foutput]

