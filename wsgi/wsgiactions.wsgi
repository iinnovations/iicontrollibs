def application(environ, start_response):

    import cgi
    import json
    from pilib import sqlitedatadump

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')
    data={}
    d={}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'

    # Run stuff as requested

    if 'dump' in d and 'database' in d and 'tablelist' in d and 'outputfile' in d:
        sqlitedatadump(d['database'],d['tablelist'],d['outputfile'])
        data='data dumped'
    elif 'dump' in d and 'database' in d and 'tablename' in d and 'outputfile' in d:
        sqlitedatadump(d['database'],[d['tablename']],d['outputfile'])
        data='data dumped'
    else:
        data='empty'

    output=json.dumps(data,indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status,response_headers)

    return [output]

