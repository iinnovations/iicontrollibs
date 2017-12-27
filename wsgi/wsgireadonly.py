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

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    try:
        post = json.loads(request_body.decode('utf-8'))
    except:
        print('Error decoding: ')
        print(request_body.decode('utf-8'))
        post = {}

    output = {'message': ''}

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
        if 'username' in post and post['username']:
            output['message'] += 'Session user is ' + post['username'] + '. '
        else:
            output['message'] += 'No session user found. '
            post['username'] = ''

        if post['username']:
            condition = "name='" + post['username'] + "'"
            user_data = safe_database.read_table_row('users', condition=condition)[0]

            try:
                condition = "name='" + post['username'] + "'"
                user_data = safe_database.read_table_row('users', condition=condition)[0]
            except:
                output['message'] += 'Error in user sqlite query for session user "' + post['username'] + '". '
                # output['message'] += 'Condition {}'.format(condition)
                output['message'] += 'Condition: ' + condition + '. Path: ' + pilib.dirs.dbs.safe
                user_data = {'accesskeywords': 'demo', 'admin': False}
            else:
                # Get session hpass to verify credentials
                hashedpassword = post['hpass']
                hname = hashlib.new('sha1')
                hname.update(post['username'])
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
            action = post['action']
        except KeyError:
            output['message'] = 'no action in request'
        else:
            if action == 'gettablenames':
                dbpath = pilib.dbnametopath(post['database'])
                try:
                    output['data'] = dblib.gettablenames(dbpath)
                except:
                    output['message'] += 'Error getting table names'
            elif action == 'modwsgistatus':
                output['processgroup'] = repr(environ['mod_wsgi.process_group'])
                output['multithread'] = repr(environ['wsgi.multithread'])
            elif action == 'gettabledata':
                output['message']+='Gettabledata. '
                if 'database' in post:
                    dbpath = pilib.dbnametopath(post['database'])
                    if dbpath:
                        output['message'] += 'Friendly name ' + post['database'] + ' translated to path ' + dbpath + ' successfully. '

                        the_database = dblib.sqliteDatabase(dbpath)
                        if 'tablenames' in post:  # Get multiple tables
                            output['message'] += 'Multiple tables. '
                            data = []
                            if 'start' in post:
                                fixedstart = int(post['start'])
                            else:
                                fixedstart = 0
                            if 'length' in post:
                                fixedlength = int(post['length'])
                            else:
                                fixedlength = 0
                            if 'lengths' in post:
                                lengths = map(int, post['lengths[]'])
                            else:
                                lengths = []
                            if 'starts' in post:
                                starts = map(int, post['starts'])
                            else:
                                starts = []

                            for index, table in enumerate(post['tablenames']):
                                output['message'] += 'Reading table {}. '.format(table)
                                try:
                                    length = lengths[index]
                                except IndexError:
                                    length = fixedlength
                                try:
                                    start = starts[index]
                                except IndexError:
                                    start = fixedstart
                                if not fixedlength: # get all rows if length not specified
                                    db_data = the_database.read_table(table)
                                else:
                                    db_data = the_database.read_table_rows(table, start, length)
                                output['message'] += 'Read {} rows of data. '.format(len(db_data))
                                data.append(db_data)
                                output['data']=data

                        elif 'length' in post:  # Handle table row subset
                            output['message']+='Length keyword. '
                            if not 'start' in post:
                                post['start'] = 0
                            thetime = time()
                            output['data'] = the_database.read_table_rows(post['tablename'], post['start'], post['length'])
                            output['querytime'] = time() - thetime
                        elif 'row' in post:  # Handle table row
                            output['message'] += 'Row keyword. ' + str(post['row'])
                            thetime = time()
                            output['data'] = the_database.read_table_rows(post['tablename'], post['row'])
                            output['querytime'] = time() - thetime
                        elif 'tablename' in post:  # Handle entire table
                            output['message'] += 'Tablename keyword: {}. '.format(post['tablename'])
                            thetime = time()
                            if 'condition' in post:
                                if not post['condition'] == '':
                                    output['message'] += 'Condition : "{}" .'.format(post['condition'])
                                    output['data'] = the_database.read_table(post['tablename'], condition=post['condition'])
                                else:
                                    output['data'] = the_database.read_table(post['tablename'])
                            else:
                                try:
                                    output['data'] = the_database.read_table(post['tablename'])
                                except:
                                    output['message'] += 'Error retrieving data. '
                                else:
                                    output['message'] += 'Data query appears successful. '
                                    # output['message'] += str(output['data'][0])
                            output['querytime'] = time() - thetime

                    else:
                        output['message'] += 'Friendly name ' + post['database'] + ' unsuccessfully translated. '
                else:
                    output['message'] += 'No database present in action request'

            elif action =='get_archive_info':
                from iiutilities.utility import get_directory_listing
                directory_list = get_directory_listing(pilib.dirs.archive)
                output['data'] = {}
                output['data']['lognames'] = []
                for filename in directory_list['filenames']:
                    if filename[-3:] == '.db':
                        output['data']['lognames'].append(filename[:-3])
                    else:
                        directory_list['filenames'].remove(filename)

                output['data']['metadata'] = []
                output['message'] += 'Retrieved db logs {}. '.format(directory_list['filenames'])
                for filename, logname in zip(directory_list['filenames'], output['data']['lognames']):

                    archive_db = dblib.sqliteDatabase(pilib.dirs.archive + filename)
                    try:
                        metadata = archive_db.read_table('metadata')[0]
                    except:
                        output['message'] += 'Error retrieving metadata for log table {}. '.format(filename)
                        output['data']['metadata'].append({})
                    else:
                        metadata['name'] = logname
                        output['data']['metadata'].append(metadata)

            else:
                output['message'] = 'no command matched for action ' + action
    else:
        output['message'] += 'Authentication unsuccessful'

    if output['data']:
        newetag = hashlib.md5(str(output['data'])).hexdigest()
        if 'etag' in post:
            if newetag == post['etag']:
                status = '304 Not Modified'
                output['data'] = ''
    else:
        newetag=''

    if 'datasize' in post:
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

