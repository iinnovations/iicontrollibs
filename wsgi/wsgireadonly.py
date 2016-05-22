def application(environ, start_response):
    import cgi
    import json
    import hashlib

    # Set top folder to allow import of modules

    import os, sys, inspect

    top_folder = \
        os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0, top_folder)

    from cupid.pilib import dbnametopath
    from cupid.dblib import dynamicsqliteread
    from cupid.dblib import gettablenames
    from cupid.dblib import switchtablerows
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
    output['data'] = []
    output['message'] = ''


    # Need to do auths in here.

    try:
        action = d['action']
    except KeyError:
        output['message'] = 'no action in request'
    else:
        if action == 'gettablenames':
            dbpath = dbnametopath(d['database'])
            try:
                output['data'] = gettablenames(dbpath)
            except:
                output['message'] += 'Error getting table names'
        elif action == 'switchtablerows':
            dbpath = dbnametopath(d['database'])
            switchtablerows(dbpath, d['tablename'], d['row1'], d['row2'], d['uniqueindex'])
        elif action == 'modwsgistatus':
            output['processgroup'] = repr(environ['mod_wsgi.process_group'])
            output['multithread'] = repr(environ['wsgi.multithread'])
        elif action == 'gettabledata':
            output['message']+='Gettabledata. '
            if 'database' in d:
                dbpath = dbnametopath(d['database'])
                if dbpath:
                    output['message'] += 'Friendly name ' + d['database'] + ' translated to path ' + dbpath + ' successfully. '

                    if 'tablenames[]' in d:  # Get multiple tables
                        output['message'] += 'Multiple tables. '
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

                        for index, table in enumerate(d['tablenames[]']):
                            try:
                                length = lengths[index]
                            except IndexError:
                                length = fixedlength
                            try:
                                start = starts[index]
                            except IndexError:
                                start = fixedstart

                            data.append(dynamicsqliteread(dbpath, table, start, length))
                            output['data']=data
                    elif 'length' in d:  # Handle table row subset
                        output['message']+='Length keyword. '
                        if not 'start' in d:
                            d['start'] = 0
                        thetime = time();
                        output['data'] = dynamicsqliteread(dbpath, d['tablename'], d['start'], d['length'])
                        output['querytime'] = time() - thetime
                    elif 'row' in d:  # Handle table row
                        output['message'] += 'Row keyword. ' + str(d['row'])
                        thetime = time();
                        output['data'] = dynamicsqliteread(dbpath, d['tablename'], d['row'])
                        output['querytime'] = time() - thetime
                    elif 'tablename' in d:  # Handle entire table
                        output['message'] += 'Tablename keyword: ' + d['tablename']
                        thetime = time();
                        if 'condition' in d:
                            if not d['condition'] == '':
                                output['data'] = dynamicsqliteread(dbpath, d['tablename'], condition=d['condition'])
                            else:
                                output['data'] = dynamicsqliteread(dbpath, d['tablename'])
                        else:
                            try:
                                output['data'] = dynamicsqliteread(dbpath, d['tablename'])
                            except:
                                output['message'] += 'Error retrieving data. '
                            else:
                                output['message'] += 'Data query appears successful. '
                        output['querytime'] = time() - thetime
                else:
                    output['message'] += 'Friendly name ' + d['database'] + ' unsuccessfully translated. '
            else:
                output['message'] += 'No database present in action request'
        else:
            output['message'] = 'no command matched for action ' + action

    if output['data']:
        newetag = hashlib.md5(str(output['data'])).hexdigest()
        if 'etag' in d:
            if newetag == d['etag']:
                status = '304 Not Modified'
                output['data'] = ''
    else:
        newetag=''

    if 'datasize' in d:
        output['datasize'] = sys.getsizeof(output['data'])

    output['etag'] = newetag

    foutput = json.dumps(output, indent=1)

    response_headers = [('Content-type', 'application/json')]
    response_headers.append(('Etag',newetag))
    start_response(status, response_headers)

    return [foutput]

