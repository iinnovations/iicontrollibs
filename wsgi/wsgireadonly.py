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

    from cupid import pilib
    from iiutilities import dblib
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

    wsgiauth = True
    authverified = False

    if wsgiauth:
        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in database.
        import hashlib

        safe_database = dblib.sqliteDatabase(pilib.dirs.dbs.users)
        if 'username' in d and d['username']:
            output['message'] += 'Session user is ' + d['username'] + '. '
        else:
            output['message'] += 'No session user found. '
            d['username'] = ''

        if d['username']:
            try:
                condition = "name='" + d['username'] + "'"
                user_data = safe_database.read_table_row('users', condition=condition)[0]
            except:
                output['message'] += 'Error in user sqlite query for session user "' + d['username'] + '". '
                output['message'] += 'Condition: ' + condition + '. Path: ' + pilib.dirs.dbs.safe
                user_data = {'accesskeywords': 'demo', 'admin': False}
            else:
                # Get session hpass to verify credentials
                hashedpassword = d['hpass']
                hname = hashlib.new('sha1')
                hname.update(d['username'])
                hashedname = hname.hexdigest()
                hentry = hashlib.new('md5')
                hentry.update(hashedname + pilib.salt + hashedpassword)
                hashedentry = hentry.hexdigest()
                if hashedentry == user_data['password']:
                    # successful auth
                    output['message'] += 'Password verified. '
                    authverified = True

                    # TODO: implement usermeta

    else:
        output['message'] += 'WSGI authorization not enabled. '
    if authverified or not wsgiauth:
        try:
            action = d['action']
        except KeyError:
            output['message'] = 'no action in request'
        else:
            if action == 'gettablenames':
                dbpath = pilib.dbnametopath(d['database'])
                try:
                    output['data'] = dblib.gettablenames(dbpath)
                except:
                    output['message'] += 'Error getting table names'
            elif action == 'switchtablerows':
                dbpath = pilib.dbnametopath(d['database'])
                dblib.switchtablerows(dbpath, d['tablename'], d['row1'], d['row2'], d['uniqueindex'])
            elif action == 'modwsgistatus':
                output['processgroup'] = repr(environ['mod_wsgi.process_group'])
                output['multithread'] = repr(environ['wsgi.multithread'])
            elif action == 'gettabledata':
                output['message']+='Gettabledata. '
                if 'database' in d:
                    dbpath = pilib.dbnametopath(d['database'])
                    if dbpath:
                        output['message'] += 'Friendly name ' + d['database'] + ' translated to path ' + dbpath + ' successfully. '

                        the_database = dblib.sqliteDatabase(dbpath)
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

                                data.append(the_database.read_table_rows(table, start, length))
                                output['data']=data

                        elif 'length' in d:  # Handle table row subset
                            output['message']+='Length keyword. '
                            if not 'start' in d:
                                d['start'] = 0
                            thetime = time();
                            output['data'] = the_database.read_table_rows(d['tablename'], d['start'], d['length'])
                            output['querytime'] = time() - thetime
                        elif 'row' in d:  # Handle table row
                            output['message'] += 'Row keyword. ' + str(d['row'])
                            thetime = time();
                            output['data'] = the_database.read_table_rows(dbpath, d['tablename'], d['row'])
                            output['querytime'] = time() - thetime
                        elif 'tablename' in d:  # Handle entire table
                            output['message'] += 'Tablename keyword: ' + d['tablename'] + '. '
                            thetime = time();
                            if 'condition' in d:
                                if not d['condition'] == '':
                                    output['data'] = the_database.read_table_rows(dbpath, d['tablename'], condition=d['condition'])
                                else:
                                    output['data'] = the_database.read_table_rows(dbpath, d['tablename'])
                            else:
                                try:
                                    output['data'] = the_database.read_table_rows(dbpath, d['tablename'])
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
    else:
        output['message'] += 'Authentication unsuccessful'

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

    try:
        foutput = json.dumps(output, indent=1)
    except:
        print('*** THERE WAS AN ERROR DECODING DATA ***')
        print(output)
        foutput = json.dumps({'message': 'Error in json dumps'})

    response_headers = [('Content-type', 'application/json')]
    response_headers.append(('Etag',newetag))
    start_response(status, response_headers)

    return [foutput]

