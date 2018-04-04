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

    # post_env = environ.copy()
    # post_env['QUERY_STRING'] = ''
    # post = cgi.FieldStorage(
    #     fp=environ['wsgi.input'],
    #     environ=post_env,
    #     keep_blank_values=True
    # )
    # formname = post.getvalue('name')
    #
    # output = {}
    #
    # d = {}
    # for k in post.keys():
    #     # print(k)
    #     d[k] = post.getvalue(k)

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    post = json.loads(request_body.decode('utf-8'))


    status = '200 OK'
    output = {'data': [], 'message': ''}

    d = post

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
                import datetime
                the_day = datetime.date.today()
                if 'day' in d:
                    # We will pass in a day in format yyyy-mm-dd or keywords, like 'today'
                    import datetime, time
                    today = datetime.date.today()
                    if d['day'] == 'today':
                        pass
                    elif d['day'] == 'prev_day':
                        the_day = today - datetime.timedelta(days=1)
                    elif d['day'] == 'prev_2_day':
                        the_day = today - datetime.timedelta(days=2)
                    elif d['day'] == 'prev_3_day':
                        the_day = today - datetime.timedelta(days=3)
                    elif d['day'] == 'prev_4_day':
                        the_day = today - datetime.timedelta(days=4)

                if the_day == datetime.date.today():
                    db_path = ii_netstats.netstats_dbpath
                else:
                    db_path_root = ii_netstats.netstats_dbpath.split('.db')[0]
                    date_string = '{}-{:02d}-{:02d}'.format(the_day.year, the_day.month, the_day.day)
                    db_path = '{}_{}.db'.format(db_path_root, date_string)

                print('** DBPATH: {} '.format(db_path))
                netstats_db = dblib.sqliteDatabase(db_path)

                output['message'] += 'db path {} chosen. '.format(db_path)

                wired_history =netstats_db.read_table('wired')
                if 'dataperiod' in d:
                    output['message'] += 'Limiting returned time to ' + d['dataperiod'] + '. '
                    # default 6hrs
                    period = 6 * 3600
                    if d['dataperiod'] == '6_hrs':
                        period = 6 * 3600
                    elif d['dataperiod'] == '12_hrs':
                        period = 12 * 3600
                    elif d['dataperiod'] == '24_hrs':
                        period = 24 * 3600
                    elif d['dataperiod'] == '48_hrs':
                        period = 48 * 3600
                    elif d['dataperiod'] == '7_days':
                        period = 7 * 24 * 3600

                    unmodified_length = len(wired_history)

                    # return only data within last period
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

