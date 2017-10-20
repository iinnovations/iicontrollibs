def application(environ, start_response):

    import cgi
    import json

    import os, sys, inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    from cupid import pilib, controllib
    from iiutilities import dblib, utility, datalib

    # post_env = environ.copy()
    # post_env['QUERY_STRING'] = ''
    # post = cgi.FieldStorage(
    #     fp=environ['wsgi.input'],
    #     environ=post_env,
    #     keep_blank_values=True
    # )
    #
    # formname=post.getvalue('name')
    # output = {}
    # output['message'] = 'Output Message: '
    # for k in post.keys():
    #     d[k] = post.getvalue(k)

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    post = json.loads(request_body.decode('utf-8'))

    output = {}
    output['message'] = ''

    status = '200 OK'
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
            try:
                condition = "name='" + post['username'] + "'"
                user_data = safe_database.read_table_row('users', condition=condition)[0]
            except:
                output['message'] += 'Error in user sqlite query for session user "' + post['username'] + '". '
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
            # Demo status
            authverified = True
            user_data = {'authlevel':0}

    else:
        output['message'] += 'WSGI authorization not enabled. '

    if authverified or not wsgiauth:
        output['authorized'] = True

    try:
        action = post['action']
    except KeyError:
        output['message'] = 'no action in request'
        action = ''
    else:
        output['message'] += '{} action keyword found'.format(action)

    if output['authorized'] and action:
        output['action_allowed'] = pilib.check_action_auths(action, user_data['authlevel'])
    else:
        output['action_allowed'] = False

    if output['authorized'] and output['action_allowed']:

        output['message'] += 'Found action. '

        if action == 'testdbvn':
            from iiutilities.dblib import dbvntovalue
            try:
                output['data'] = dbvntovalue(post['dbvn'])
            except:
                output['message'] += 'Error in dbvn evaluation. '
                output['data'] = 'error'
            else:
                output['message'] += 'Seems to have worked out. '
        elif action == 'testlogical':
            from iiutilities.datalib import evaldbvnformula
            try:
                output['data'] = evaldbvnformula(post['logical'])
            except:
                output['message'] += 'Error in logical evaluation. '
                output['data'] = 'error'
            else:
                output['message'] += 'Seems to have worked out. '

        elif action == 'testmodule':
            output['message'] += 'Testing module: '
            if 'modulename' in post:
                import cupid.cupidunittests
                output['message'] += post['modulename']
                output['data'] = cupid.cupidunittests.testmodule(post['modulename'])
            else:
                output['message'] += 'Modulename not found. '
        elif action == 'testfunction':
            output['message'] += 'Testing function: '
            if 'testname' in post:
                import cupid.cupidunittests
                output['message'] += post['testname']
                # output['data'] = cupid.tests.testfunction(d['testname'])
                output['data'] = cupid.cupidunittests.testfunction(post['testname'])
                # output['data'] = str(cupid.tests.testfunction('systemstatus'))
            else:
                output['message'] += 'Testname not found. '

        elif action == 'modifychannelalarm':
            controllib.handle_modify_channel_alarm(post, output)
            from cupid.actions import processactions

            # process only this action.
            processactions(name=post['actionname'])

        elif action == 'modifychannel':
            controllib.handle_modify_channel(post, output)

        elif action == 'getalarmscount':
            control_db = dblib.sqliteDatabase(pilib.dirs.dbs.control)
            actions = control_db.read_table('actions')
            output['data'] = {'totalalarms':len(actions),'channelalarms':0, 'activealarms':0, 'activechannelalarms':0}
            for action in actions:
                if action['conditiontype'] == 'channel':
                    output['data']['channelalarms'] += 1
                    if action['active']:
                        output['data']['activechannelalarms'] += 1

                if action['active']:
                    output['data']['activealarms'] += 1

        elif action == 'copy_log_to_archive':
            pilib.app_copy_log_to_archive(post, output)

        elif action == 'getlogscount':
            logtablenames = dblib.sqliteDatabase(pilib.dirs.dbs.log).get_table_names()
            output['data'] = {'logscount':len(logtablenames)}


        elif action == 'test_action':
            output['message'] += 'Testing action. '
            controldb = dblib.sqliteDatabase(pilib.dirs.dbs.control)
            actiondict = controldb.read_table('actions',condition='"name"=\'' + post['actionname'] + "'")[0]
            from cupid.actions import action
            test_action = action(actiondict)
            test_action.test()

        elif action == 'update_network':
            safe_database = dblib.sqliteDatabase(pilib.dirs.dbs.safe)
            safe_database.set_single_value('wireless', 'password', post['password'], "SSID='" + post['ssid'] + "'")

        elif action == 'add_network':
            safe_database = dblib.sqliteDatabase(pilib.dirs.dbs.safe)
            insert = {'SSID':post['ssid'], 'auto':1, 'priority':1}
            if 'password' in post:
                insert['password'] = post['password']
            safe_database.insert('wireless',insert)

        elif action == 'delete_network':
            safe_database = dblib.sqliteDatabase(pilib.dirs.dbs.safe)
            safe_database.delete('wireless', "SSID='" + post['ssid'] + "'")

        # elif action == 'dump':
        #     # this has to go.
        #     if 'database' in d:
        #         dbpath = pilib.dbnametopath(d['database'])
        #         if dbpath:
        #             if 'tablelist' in d and 'outputfile' in d:
        #                 dbpath = pilib.dbnametopath(d['database'])
        #                 dblib.sqlitedatadump(dbpath, d['tablelist'], d['outputfile'])
        #                 output['message'] = 'data dumped'
        #             elif 'tablename' in d and 'outputfile' in d:
        #                 dblib.sqlitedatadump(dbpath, [d['tablename']], d['outputfile'])
        #                 output['message'] = 'data dumped. '
        #             else:
        #                 output['message'] += 'keys not present for dump. '
        #         else:
        #             output['message'] += 'keys not present for dump. '
        #     else:
        #         output['message'] += 'keys not present for dump. '
        elif action in ['userdelete', 'useradd', 'usermodify']:
            """
            This needs to be consolidate with the other useradd, modify algorithm written already.
            Probably do this when we update the user permissions interface.
            """
            # Ensure that we are authorized for this action
            if action == 'userdelete':
                try:
                    dblib.sqlitequery(pilib.dirs.dbs.users, "delete from users where name='" + post['usertodelete'] + "'")
                except:
                    output['message'] += 'Error in delete query. '
                else:
                    output['message'] += 'Successful delete query. '
            elif action == 'usermodify':

                if 'usertomodify' in post:
                    querylist=[]
                    if 'newpass' in post:
                        from pilib import salt
                        # Get session hpass to verify credentials
                        hashedpassword = post['newpass']
                        hname = hashlib.new('sha1')
                        hname.update(post['usertomodify'])
                        hashedname = hname.hexdigest()
                        hentry = hashlib.new('md5')
                        hentry.update(hashedname + salt + hashedpassword)
                        hashedentry = hentry.hexdigest()
                        querylist.append('update users set password=' + hashedentry + " where name='" + post['usertomodify'] + "'")

                    if 'newemail' in post:
                        querylist.append("update users set email='" + post['newemail'] + "' where name='" + post['usertomodify'] + "'")
                    if 'newauthlevel' in post:
                        querylist.append("update users set authlevel='" + post['newauthlevel'] + "' where name='" + post['usertomodify'] + "'")

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
                    username = post['newusername']
                except:
                    username = 'newuser'
                try:
                    newemail = post['newemail']
                except:
                    newemail = 'fakeemail@domain.com'
                try:
                    newauthlevel = post['newauthlevel']
                except:
                    newauthlevel = 0
                    query = "insert into users values(NULL,'" + username + "','','" + newemail + "',''," + str(newauthlevel) + ")"
                try:
                    dblib.sqlitequery(pilib.dirs.dbs.users, query)
                except:
                    output['message'] += "Error in useradd sqlite query: " + query + ' . '
                else:
                    output['message'] += "Successful query: " + query + ' . '
        elif action == 'getfiletext':
            try:
                filepath = post['filepath']
                if 'numlines' in post:
                    numlines = int(post['numlines'])
                else:
                    numlines = 9999
                output['message'] += 'Using numlines: ' + str(numlines) + ' for read action. '
                if 'startposition' in post:
                    startposition = post['startposition']
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
                clientIP = post['clientIP']
                register = post['register']
                length = post['length']
            except KeyError:
                output['message'] += 'Sufficient keys do not exist for the command. Requires clientIP, register, and length. '
            else:
                from iiutilities.netfun import readMBcodedaddresses
                # try:
                output['response'] = readMBcodedaddresses(clientIP, int(register), int(length))
        elif action == 'queuemessage':
            output['message'] += 'Queue message. '
            if 'message' in post:
                try:
                    dblib.sqliteinsertsingle(pilib.dirs.dbs.motes, 'queuedmessages', [datalib.gettimestring(), post['message']])
                except:
                    import traceback
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    output['message'] += 'Error in queue insert query: {}. '.format(traceback.format_exc())
                else:
                    output['message'] += 'Message insert successful'
            else:
                output['message'] += 'No message present. '

        elif action == 'setsystemflag' and 'systemflag' in post:
            database = pilib.dirs.dbs.system
            dblib.setsinglevalue(database, 'systemflags', 'value', 1, "name=\'" + post['systemflag'] + "'")
        elif action == 'rundaemon':
            from cupiddaemon import rundaemon
            rundaemon()

        # TODO: Eliminate this scary thing.
        elif action == 'setvalue' and False:
            utility.log(pilib.dirs.logs.control, "Setting value in wsgi", 1, 1)

            # we use the auxiliary 'setsinglecontrolvalue' to add additional actions to update
            if all(k in post for k in ('database', 'table', 'valuename', 'value')):
                dbpath = pilib.dbnametopath(post['database'])
                if dbpath:
                    output['message'] += 'Carrying out setvalue for value ' + post['valuename'] + ' on ' + post['table'] + ' in '  + dbpath
                    if 'condition' in post:
                        pilib.setsinglecontrolvalue(dbpath, post['table'], post['valuename'], post['value'], post['condition'])
                    elif 'index' in post:
                        condition = 'rowid= ' + post['index']
                        pilib.setsinglecontrolvalue(dbpath, post['table'], post['valuename'], post['value'], condition)
                    else:
                        pilib.setsinglecontrolvalue(dbpath, post['table'], post['valuename'], post['value'])
                else:
                    output['message'] += 'Problem translating dbpath from friendly name: ' + post['database']
            else:
                output['message'] += 'Insufficient data for setvalue '
        elif action == 'updateioinfo':
            if all(k in post for k in ['database', 'ioid', 'value']):
                query = dblib.makesqliteinsert('ioinfo', [post['ioid'], post['value']], ['id', 'name'])
                try:
                    dblib.sqlitequery(pilib.dirs.dbs.control, query)
                except:
                    output['message'] += 'Error in updateioinfo query execution: ' + query +'. into database: ' + pilib.dirs.dbs.control
                    output['message'] += 'ioid: ' + post['ioid'] + ' . '
                else:
                    output['message'] += 'Executed updateioinfo query. '
            else:
                output['message'] += 'Insufficient data for updateioinfo query ! '


        # TODO: properly incorporate and test channel class functions here, and then sub it.
        elif action == 'modify_channel':
            controllib.app_modify_channel(post, output)

        elif action == 'deletechannelbyname' and 'database' in post and 'channelname' in post:
            dbpath = pilib.dbnametopath(post['database'])
            dblib.sqlitequery(dbpath, 'delete channelname from channels where name=\"' + post['channelname'] + '\"')
        elif action == 'updatecameraimage':
            output['message'] += 'Take camera image keyword. '
            import cupid.camera
            if 'width' in post:
                width = post['width']
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
        output['message'] += 'Authentication unsuccessful or action not authorized.'
        status = '401 Not Authorized'

    foutput = json.dumps(output, indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)

    return [foutput]

