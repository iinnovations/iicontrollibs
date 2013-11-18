def application(environ, start_response):
 
    import cgi
    import json
    
    import os,sys,inspect

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    from iicontrollibs.cupid.pilib import sqlitequery, gettimestring 
    import iicontrollibs.cupid.controllib as controllib

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')

    d={}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'

    if 'sessionid' in post.keys() and 'event' in post.keys() and 'realIP' in post.keys() and 'apparentIP' in post.keys():
        # sessionid contains the session id
        sessionid = post.getvalue('sessionid')
        if post.getvalue('event') == 'access':
            accesstime = gettimestring()
            username = post.getvalue('username')
            apparentIP = post.getvalue('apparentIP')
            realIP =  post.getvalue('realIP')
            sqlitequery('/var/www/data/authlog.db',"insert into sessionlog values ( \'" + username + "\',\'" + sessionid + "\',\'" + accesstime + "\'," + "\'access\' ,\'" + apparentIP + "\',\'" + realIP + "\' )")
        output = "Output processed for " + realIP + " & " + apparentIP

    else:
        output = 'error: no session field sent'  

    response_headers = [('Content-type', 'text/plain'), ('Content-Length',str(len(output)))]
    start_response(status,response_headers)
   
    return [output]


    

