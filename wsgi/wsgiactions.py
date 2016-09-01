def application(environ, start_response):

    import cgi
    import json

    import os, sys, inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    import cupid.pilib as pilib
    import cupid.controllib as controllib
    from iiutilities import dblib, utility, datalib

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')
    output = {}
    output['message'] = 'Output Message: '
    d = {}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'
    wsgiauth = False
    authverified = False

    if wsgiauth:
        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in database.
        import hashlib
        from pilib import salt

        try:
            userdata = dblib.datarowtodict(pilib.dirs.dbs.users, 'users', dblib.sqlitequery(pilib.dirs.dbs.users, "select * from users where name='" + d['sessionuser'] + "'")[0])
        except:
            output['message'] += 'error in user sqlite query. '
            # unsuccessful authentication

        # Get session hpass to verify credentials
        hashedpassword = d['sessionhpass']
        hname = hashlib.new('sha1')
        hname.update(d['sessionuser'])
        hashedname = hname.hexdigest()
        hentry = hashlib.new('md5')
        hentry.update(hashedname + salt + hashedpassword)
        hashedentry = hentry.hexdigest()
        if hashedentry == userdata['password']:
            # successful auth
            output['message'] += 'Password verified. '
            authverified = True
    else:
        output['message'] += 'WSGI authorization not enabled. '

    if authverified or not wsgiauth:
        # Perform requested actions
        if 'action' in d:
            action = d['action']
            output['message'] += 'Found action. '
            if action == 'runquery':
                output['message'] += 'Query keyword found. '
                dbpath = pilib.dbnametopath(d['database'])
                if dbpath:
                    output['message'] += 'Friendly dbpath ' + dbpath + ' found. '
                    if 'query' in d:  # Take plain single query
                        result = dblib.sqlitequery(dbpath, d['query'])
                        output['response'] = result
                        output['message'] += 'Query ' + d['query'] + ' executed. '
                    elif 'queryarray[]' in d:  # Take query array, won't find
                        result = []
                        queryarray = d['queryarray[]']
                        for query in queryarray:
                            result.append(dblib.sqlitequery(dbpath, query))
                        output['response'] = result
                        output['message'] += 'Query array executed. '
                else:
                     output['message'] += 'Name "' + d['database'] + '"  unsuccessfully translated. '
            elif action == 'testmodule':
                output['message'] += 'Testing module: '
                if 'modulename' in d:
                    import cupid.cupidunittests
                    output['message'] += d['modulename']
                    output['data'] = cupid.cupidunittests.testmodule(d['modulename'])
                else:
                    output['message'] += 'Modulename not found. '
            elif action == 'testfunction':
                output['message'] += 'Testing function: '
                if 'testname' in d:
                    import cupid.cupidunittests
                    output['message'] += d['testname']
                    # output['data'] = cupid.tests.testfunction(d['testname'])
                    output['data'] = cupid.cupidunittests.testfunction(d['testname'])
                    # output['data'] = str(cupid.tests.testfunction('systemstatus'))
                else:
                    output['message'] += 'Testname not found. '
            elif action == 'dump':
                if 'database' in d:
                    dbpath = pilib.dbnametopath(d['database'])
                    if dbpath:
                        if 'tablelist' in d and 'outputfile' in d:
                            dbpath = pilib.dbnametopath(d['database'])
                            dblib.sqlitedatadump(dbpath, d['tablelist'], d['outputfile'])
                            output['message'] = 'data dumped'
                        elif 'tablename' in d and 'outputfile' in d:
                            dblib.sqlitedatadump(dbpath, [d['tablename']], d['outputfile'])
                            output['message'] = 'data dumped. '
                        else:
                            output['message'] += 'keys not present for dump. '
                    else:
                        output['message'] += 'keys not present for dump. '
                else:
                    output['message'] += 'keys not present for dump. '
            elif action in ['userdelete', 'useradd', 'usermodify']:

                # Ensure that we are authorized for this action
                if userdata['authlevel'] >= 4:
                    output['message'] += 'User selected has sufficient authorizations. '
                    if action == 'userdelete':
                        try:
                            dblib.sqlitequery(pilib.dirs.dbs.users, "delete from users where name='" + d['usertodelete'] + "'")
                        except:
                            output['message'] += 'Error in delete query. '
                        else:
                            output['message'] += 'Successful delete query. '
                    elif action == 'usermodify':
                        if 'usertomodify' in d:
                            querylist=[]
                            if 'newpass' in d:
                                # Get session hpass to verify credentials
                                hashedpassword = d['newpass']
                                hname = hashlib.new('sha1')
                                hname.update(d['usertomodify'])
                                hashedname = hname.hexdigest()
                                hentry = hashlib.new('md5')
                                hentry.update(hashedname + salt + hashedpassword)
                                hashedentry = hentry.hexdigest()
                                querylist.append('update users set password=' + hashedentry + " where name='" + d['usertomodify'] + "'")
                            if 'newemail' in d:
                                querylist.append("update users set email='" + d['newemail'] + "' where name='" + d['usertomodify'] + "'")
                            if 'newauthlevel' in d:
                                querylist.append("update users set authlevel='" + d['newauthlevel'] + "' where name='" + d['usertomodify'] + "'")

                            try:
                                dblib.sqlitemultquery(pilib.dirs.dbs.users, querylist)
                            except:
                                output['message'] += 'Error in modify/add query: ' + ",".join(querylist)
                            else:
                                output['message'] += 'Successful modify/add query. ' + ",".join(querylist)
                        else:
                            output['message'] += 'Need usertomodify in query. '
                    elif action == 'useradd':
                        try:
                            username = d['newusername']
                        except:
                            username = 'newuser'
                        try:
                            newemail = d['newemail']
                        except:
                            newemail = 'fakeemail@domain.com'
                        try:
                            newauthlevel = d['newauthlevel']
                        except:
                            newauthlevel = 0
                            query = "insert into users values(NULL,'" + username + "','','" + newemail + "',''," + str(newauthlevel) + ")"
                        try:
                            dblib.sqlitequery(pilib.dirs.dbs.users, query)
                        except:
                            output['message'] += "Error in useradd sqlite query: " + query + ' . '
                        else:
                            output['message'] += "Successful query: " + query + ' . '
                    else:
                        output['message'] += 'Unable to verify password. '
                else:
                    output['message'] = 'insufficient authorization level for current user. '
            elif action == 'getfiletext':
                try:
                    filepath = d['filepath']
                    if 'numlines' in d:
                        numlines = int(d['numlines'])
                    else:
                        numlines = 9999
                    output['message'] += 'Using numlines: ' + str(numlines) + ' for read action. '
                    if 'startposition' in d:
                        startposition = d['startposition']
                    else:
                        startposition = 'end'
                    output['message'] += 'Reading from position ' + startposition + '. '
                except KeyError:
                    output['message'] += 'Sufficient keys for action getfile text do not exist. '
                except:
                    output['message'] += 'Uncaught error in getfiletext. '
                else:
                    try:
                        file = open(filepath)
                        lines = file.readlines()
                    except:
                        output['message'] += 'Error reading file in getfiletext action. '
                    else:
                        output['data'] = []
                        if startposition == 'end':
                            try:
                                output['data'] = datalib.tail(file, numlines)[0]
                            except:
                                output['message'] += 'Error in tail read. '
                        else:
                            linecount = 0
                            for line in lines:
                                linecount += 1
                                if linecount > numlines:
                                    break
                                else:
                                    output['data'].append(line)
            elif action == 'getmbtcpdata':
                try:
                    clientIP = d['clientIP']
                    register = d['register']
                    length = d['length']
                except KeyError:
                    output['message'] += 'Sufficient keys do not exist for the command. Requires clientIP, register, and length. '
                else:
                    from iiutilities.netfun import readMBcodedaddresses
                    # try:
                    output['response'] = readMBcodedaddresses(clientIP, int(register), int(length))
            elif action == 'queuemessage':
                output['message'] += 'Queue message. '
                if 'message' in d:
                    try:
                        dblib.sqliteinsertsingle(pilib.dirs.dbs.motes, 'queuedmessages', [datalib.gettimestring(), d['message']])
                    except Exception, e:
                        output['message'] += 'Error in queue insert query: ' + str(e)
                    else:
                        output['message'] += 'Message insert successful'
                else:
                    output['message'] += 'No message present. '
            elif action == 'setsystemflag' and 'systemflag' in d:
                database = pilib.dirs.dbs.system
                dblib.setsinglevalue(database, 'systemflags', 'value', 1, "name=\'" + d['systemflag'] + "'")
            elif action == 'rundaemon':
                from cupiddaemon import rundaemon
                rundaemon()

            elif action == 'setvalue':
                utility.log(pilib.dirs.logs.control, "Setting value in wsgi", 1, 1)
                # we use the auxiliary 'setsinglecontrolvalue' to add additional actions to update
                if all(k in d for k in ('database', 'table', 'valuename', 'value')):
                    dbpath = pilib.dbnametopath(d['database'])
                    if dbpath:
                        output['message'] += 'Carrying out setvalue for value ' + d['valuename'] + ' on ' + d['table'] + ' in '  + dbpath
                        if 'condition' in d:
                            pilib.setsinglecontrolvalue(dbpath, d['table'], d['valuename'], d['value'], d['condition'])
                        elif 'index' in d:
                            condition = 'rowid= ' + d['index']
                            pilib.setsinglecontrolvalue(dbpath, d['table'], d['valuename'], d['value'], condition)
                        else:
                            pilib.setsinglecontrolvalue(dbpath, d['table'], d['valuename'], d['value'])
                    else:
                        output['message'] += 'Problem translating dbpath from friendly name: ' + d['database']
                else:
                    output['message'] += 'Insufficient data for setvalue '
            elif action == 'updateioinfo':
                if all(k in d for k in ['database', 'ioid', 'value']):
                    query = dblib.makesqliteinsert('ioinfo', [d['ioid'], d['value']], ['id', 'name'])
                    try:
                        dblib.sqlitequery(pilib.dirs.dbs.control, query)
                    except:
                        output['message'] += 'Error in updateioinfo query execution: ' + query +'. into database: ' + pilib.dirs.dbs.control
                        output['message'] += 'ioid: ' + d['ioid'] + ' . '
                    else:
                        output['message'] += 'Executed updateioinfo query. '
                else:
                    output['message'] += 'Insufficient data for updateioinfo query ! '

            # These are all very specific actions that could be rolled up or built into classes
            elif action == 'spchange' and 'database' in d:
                output['message'] += 'Spchanged. '
                dbpath = pilib.dbnametopath(d['database'])
                if dbpath:
                    if 'subaction' in d:
                        if d['subaction'] == 'incup':
                            controllib.incsetpoint(d['database'], d['channelname'])
                            output['message'] += 'incup. '
                        if d['subaction'] == 'incdown':
                            controllib.decsetpoint(d['database'], d['channelname'])
                            output['message'] += 'incdown. '
                        if d['subaction'] == 'setvalue':
                            controllib.setsetpoint(d['database'], d['channelname'], d['value'])
                            output['message'] += 'Setvalue: ' + d['database'] + ' ' + d['channelname'] + ' ' + d['value']
                    else:
                        output['message'] += 'subaction not found. '
                else:
                    output['message'] += 'Problem translating dbpath from friendly name: ' + d['database']
            elif action == 'togglemode' and 'database' in d:

                controllib.togglemode(d['database'], d['channelname'])
            elif action == 'setmode' and 'database' in d:
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setmode(dbpath, d['channelname'], d['mode'])
            elif action == 'setrecipe':
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setrecipe(dbpath, d['channelname'], d['recipe'])
            elif action == 'setcontrolinput':
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setcontrolinput(dbpath, d['channelname'], d['controlinput'])
            elif action == 'setchannelenabled':
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setchannelenabled(dbpath, d['channelname'], d['newstatus'])
            elif action == 'setchanneloutputsenabled':
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setchanneloutputsenabled(dbpath, d['channelname'], d['newstatus'])
            elif action == 'manualactionchange' and 'database' in d and 'channelname' in d and 'subaction' in d:
                dbpath = pilib.dbnametopath(d['database'])
                curchanmode = pilib.controllib.getmode(dbpath, d['channelname'])
                if curchanmode == 'manual':
                    if d['subaction'] == 'poson':
                        controllib.setaction(dbpath, d['channelname'], '100.0')
                    elif d['subaction'] == 'negon':
                        controllib.setaction(dbpath, d['channelname'], '-100.0')
                    else:
                        controllib.setaction(dbpath, d['channelname'], '0.0')
            elif action == 'setposoutput' and 'database' in d and 'channelname' in d and 'outputname' in d:
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setposout(dbpath, d['channelname'], d['outputname'])
            elif action == 'setnegoutput' and 'database' in d and 'channelname' in d:
                dbpath = pilib.dbnametopath(d['database'])
                controllib.setnegout(dbpath, d['channelname'], d['outputname'])
            elif action == 'actiondown' and 'database' in d and 'channelname' in d:
                dbpath = pilib.dbnametopath(d['database'])
                curchanmode = controllib.getmode(dbpath, d['channelname'])
                if curchanmode == "manual":
                    curaction = int(controllib.getaction(dbpath, d['channelname']))
                    if curaction == 100:
                        nextvalue = 0
                    elif curaction == 0:
                        nextvalue = -100
                    elif curaction == -100:
                        nextvalue = -100
                    else:
                        nextvalue = 0
                    controllib.setaction(dbpath, d['channelname'], d['nextvalue'])
            elif action == 'actionup' and 'database' in d and 'channelname' in d:
                dbpath = pilib.dbnametopath(d['database'])
                curchanmode = controllib.getmode(dbpath, d['channelname'])
                if curchanmode == "manual":
                    curaction = int(controllib.getaction(dbpath, d['channelname']))
                    if curaction == 100:
                        nextvalue = 100
                    elif curaction == 0:
                        nextvalue = 100
                    elif curaction == -100:
                        nextvalue = 0
                    else:
                        nextvalue = 0
                    controllib.setaction(dbpath, d['channelname'], nextvalue)
            elif action == 'deletechannelbyname' and 'database' in d and 'channelname' in d:
                dbpath = pilib.dbnametopath(d['database'])
                dblib.sqlitequery(dbpath, 'delete channelname from channels where name=\"' + d['channelname'] + '\"')
            elif action == 'updatecameraimage':
                output['message'] += 'Take camera image keyword. '
                import cupid.camera
                if 'width' in d:
                    width = d['width']
                else:
                    width = 800
                try:
                    values = cupid.camera.takesnap(width=width)
                except:
                    output['message'] += 'Error taking image. '
                else:
                    output['message'] += 'Appears successful. Path : ' + values['imagepath'] + '. Timestamp : ' + values['timestamp'] + '. '
                    output['data'] = values
            elif action == 'getcurrentcamtimestamp':
                output['message'] += 'getcurrentcamtimestamp keyword found. '
                try:
                    with open('/var/www/webcam/images/current.jpg.timestamp') as f:
                        data = f.read()
                except:
                    output['message'] += 'Error reading file as requested. '
                else:
                    output['data'] = data
            else:
                output['message'] += 'Action keyword present(' + action + '), but not handled. '
        else:
            output['message'] += 'action keyword not present. '
    else:
        output['message'] += 'Authentication unsuccessful'

    foutput = json.dumps(output, indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)

    return [foutput]

