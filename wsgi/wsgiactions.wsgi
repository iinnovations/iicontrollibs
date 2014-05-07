def application(environ, start_response):

    import cgi
    import json

    import os,sys,inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    from cupid.pilib import sqlitedatadump, sqlitequery, sqlitemultquery, usersdatabase, datarowtodict

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')
    data={}
    data['message']=''
    d={}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'

    # Run stuff as requested
    if 'action' in d:
        action = d['action']
        if action == 'dump':
            if 'database' in d and 'tablelist' in d and 'outputfile' in d:
                sqlitedatadump(d['database'],d['tablelist'],d['outputfile'])
                data='data dumped'
            elif 'database' in d and 'tablename' in d and 'outputfile' in d:
                sqlitedatadump(d['database'],[d['tablename']],d['outputfile'])
                data='data dumped'
            else:
                data = 'keys not present for dump'
        elif action in ['userdelete', 'useradd', 'usermodify']:
            data['message'] += 'Found action. '
            # Ensure that we are authorized for this action
            try:
                userdata = datarowtodict(usersdatabase, 'users', sqlitequery(usersdatabase, "select * from users where name='" + d['sessionuser'] + "'")[0])
            except:
                data['message'] += 'error in sqlite query. '
            else:
                # Verify the credentials of the user are sufficient so we don't bother checking hash if not.

                if userdata['authlevel'] >= 4:
                    data['message'] += 'User selected has sufficient authorizations. '

                    # Verfiy that session login information is legit: hashed password, with salt and username, match
                    # hash stored in database.
                    import hashlib
                    from cupid.pilib import salt

                    # Get session hpass to verify credentials
                    hashedpassword = d['sessionhpass']
                    hname = hashlib.new('sha1')
                    hname.update(d['sessionuser'])
                    hashedname = hname.hexdigest()
                    hentry = hashlib.new('md5')
                    hentry.update(hashedname + salt + hashedpassword)
                    hashedentry = hentry.hexdigest()

                    if hashedentry == userdata['password']:
                        data['message'] += 'Password verified. '
                        if action == 'userdelete':
                            try:
                                sqlitequery(usersdatabase, "delete from users where name='" + d['usertodelete'] + "'")
                            except:
                                data['message'] += 'Error in delete query. '
                            else:
                                data['message'] += 'Successful delete query. '
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
                                    sqlitemultquery(usersdatabase, querylist)
                                except:
                                    data['message'] += 'Error in modify/add query: ' + ",".join(querylist)
                                else:
                                    data['message'] += 'Successful modify/add query. ' + ",".join(querylist)
                            else:
                                data['message'] += 'Need usertomodify in query. '
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
                                sqlitequery(usersdatabase, query)
                            except:
                                data['message'] += "Error in useradd sqlite query: " + query + ' . '
                            else:
                                data['message'] += "Successful query: " + query + ' . '
                    else:
                        data['message'] += 'Unable to verify password. '

                else:
                    data['message'] = 'insufficient authorization level for current user. '


    else:
        data['message']+='action keyword not present. '

    output = json.dumps(data,indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status,response_headers)

    return [output]

