
def application(environ, start_response):
 
    import cgi
    import json
    from pilib import dynamicsqliteread, sqlitequery

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

    if 'length' in d:			# Handle table row subset 
        data=dynamicsqliteread(d['database'],d['table'],d['start'],d['length'])
    elif 'row' in d:			# Handle table row
        data=dynamicsqliteread(d['database'],d['table'],d['row'])
    elif 'table' in d: 			# Handle entire table
        data=dynamicsqliteread(d['database'],d['table'])
    elif 'query' in d:				# Take plain single query 
        result=sqlitequery(d['database'],d['query'])
        data=result
    elif 'queryarray[]' in d:		# Take query array, won't find 
	result=[]		
        for query in d['queryarray[]']:
            result.append(sqlitequery(d['database'],query))
        data=result
    else:
        data=['empty']

    output = json.dumps(data,indent=1) 

    response_headers = [('Content-type', 'application/json')]
    start_response(status,response_headers)
   
    return [output]

