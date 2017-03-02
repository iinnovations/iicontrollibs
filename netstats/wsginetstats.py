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

    import ii_netstats

    from iiutilities import dblib, datalib
    from iiutilities.utility import newunmangle
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
        # print(k)
        d[k] = post.getvalue(k)


    status = '200 OK'
    # Run stuff as requested
    # We use the dynamic function to allow various  
    # types of queries
    output['data'] = []
    output['message'] = ''

    # print('** original')
    # print(d)
    d = newunmangle(d)
    # print('** unmangled')
    # print(d)

    # Here we verify credentials of session data against those in the database.
    # While we authenticate in the browser, this does not stop POST queries to the API without the page provided
    # So we take the hpass stored in the dictionary and verify

    # First, let's get our pathalias and translate to a path, using our path reloader

    wsgiauth = False
    authverified = False

    if wsgiauth:
        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in database.
        import hashlib

        if 'sessionuser' in d:
            output['message'] += 'Session user is ' + d['sessionuser'] + '. '
        else:
            output['message'] += 'No session user found. '
            d['sessionuser'] = ''

        try:
            condition = "name='" + d['sessionuser'] + "'"
            userdata = dblib.readonedbrow(inventorylib.sysvars.dirs.dbs.safe, 'users', condition=condition)[0]
        except:
            output['message'] += 'error in user sqlite query for session user "' + d['sessionuser'] + '". '
            userdata = {'accesskeywords':'demo','admin':False}
        else:
            # Get session hpass to verify credentials
            hashedpassword = d['sessionhpass']
            hname = hashlib.new('sha1')
            hname.update(d['sessionuser'])
            hashedname = hname.hexdigest()
            hentry = hashlib.new('md5')
            hentry.update(hashedname + netstats.salt + hashedpassword)
            hashedentry = hentry.hexdigest()
            if hashedentry == userdata['password']:
                # successful auth
                output['message'] += 'Password verified. '
                authverified = True
    else:
        output['message'] += 'WSGI authorization not enabled. '

    if authverified or not wsgiauth:
        try:
            action = d['action']
        except KeyError:
            output['message'] = 'no action in request'
        else:
            # Stock functions
            if action == 'getnetstatsdata':
                output['message'] += 'getting netstats keyword found. '

                wired_history = dblib.readalldbrows(ii_netstats.netstats_dbpath, 'wired')
                if 'dataperiod' in d:
                    output['message'] += 'Limiting returned time to ' + d['dataperiod'] + '. '
                    if d['dataperiod'] == '6hrs':
                        period = 6 * 3600
                    elif d['dataperiod'] == '12hrs':
                        period = 12 * 3600
                    elif d['dataperiod'] == '24hrs':
                        period = 24 * 3600
                    elif d['dataperiod'] == '48hrs':
                        period = 48 * 3600
                    elif d['dataperiod'] == '7days':
                        period = 7 * 24 * 3600

                    unmodified_length = len(wired_history)

                    # return only data within last 6hrs
                    from operator import itemgetter
                    from iiutilities.datalib import timestringtoseconds
                    new_list = sorted(wired_history, key=itemgetter('time'), reverse=True)

                    output['message'] += 'Most recent data point: ' + new_list[0]['time'] + '. '
                    new_history = []
                    most_recent_time_in_seconds = timestringtoseconds(new_list[0]['time'])
                    output['message'] += 'Most recent time in seconds ' + str(most_recent_time_in_seconds) + '. '

                    output['message'] += 'Oldest time in seconds ' + str(timestringtoseconds(new_list[-1]['time']))
                    output['message'] += 'Span of ' + str(most_recent_time_in_seconds - timestringtoseconds(new_list[-1]['time']))  + '. '
                    output['message'] += 'Period of ' + str(period) + '. '


                    for item in new_list:
                        if most_recent_time_in_seconds - timestringtoseconds(item['time']) < period:
                            new_history.append(item)
                    output['data'] = new_history
                    modified_length = len(wired_history)

                    output['message'] += 'Shortened data from ' + str(unmodified_length) + ' to ' + str(modified_length)
                else:
                    output['data'] = wired_history
                try:
                    from urllib2 import urlopen
                    my_ip = urlopen('http://ip.42.pl/raw').read()
                except:
                    my_ip = 'unknown'
                output['host'] = my_ip
            elif action == 'gettraffichistodata':
                output['message'] += 'gettraffic histo keyword found. '
                access_db = dblib.sqliteDatabase(ii_netstats.access_dbpath)

                access_db_tablenames = access_db.get_table_names()
                # output['message'] += 'Tables to search through: ' + str(access_db_tablenames) + '. '

                tables_to_fetch = []
                for tablename in access_db_tablenames:
                    if tablename.find('remotehisto') >= 0 or tablename.find('metadata') >= 0:
                        tables_to_fetch.append(tablename)
                # output['message'] += 'Fetching tables ' + str(tables_to_fetch) + '. '
                output['data'] = {}
                for table_to_fetch in tables_to_fetch:
                    output['data'][table_to_fetch] = access_db.read_table(table_to_fetch)

            elif action == 'postwirelessdata':
                output['message'] += 'postwirelessdata keyword found. '

                # nothing here yet

    if 'data' in output:
        if output['data']:
            newetag = hashlib.md5(str(output['data'])).hexdigest()
            if 'etag' in d:
                if newetag == d['etag']:
                    status = '304 Not Modified'
                    output['data'] = ''
        else:
            newetag=''
    else:
        newetag=''

    if 'datasize' in d:
        output['datasize'] = sys.getsizeof(output['data'])

    output['etag'] = newetag
    try:
        foutput = json.dumps(output, indent=1)
    except:
        import csv
        w = csv.writer(open("/usr/lib/iicontrollibs/inventory/dumperr.log", "w"))
        for key, val in output.items():
            w.writerow([key, val])

    response_headers = [('Content-type', 'application/json')]
    response_headers.append(('Etag',newetag))
    start_response(status, response_headers)

    return [foutput]

