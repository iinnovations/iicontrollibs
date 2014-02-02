def application(environ, start_response):
 
    import cgi
    import json

    # Set top folder to allow import of modules

    import os,sys,inspect
    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    from cupid.pilib import dynamicsqliteread, gettablenames, sqlitequery, switchtablerows

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
    # We use the dynamic function to allow various  
    # types of queries
    if 'specialaction' in d:
        if d['specialaction']=='gettablenames':
            data=gettablenames(d['database'])
        elif d['specialaction']=='switchtablerows':
            switchtablerows(d['database'],d['table'],d['row1'],d['row2'],d['uniqueindex'])
    elif 'length' in d:			# Handle table row subset 
        data=dynamicsqliteread(d['database'],d['table'],d['start'],d['length'])
    elif 'row' in d:			# Handle table row
        data=dynamicsqliteread(d['database'],d['table'],d['row'])
    elif 'table' in d: 			# Handle entire table
        data=dynamicsqliteread(d['database'],d['table'])
    elif 'tables[]' in d: 		# Get multiple tables
        data=[]
        for table in d['tables[]']:
            data.append(dynamicsqliteread(d['database'],table))
    elif 'query' in d:				# Take plain single query 
        result=sqlitequery(d['database'],d['query'])
        data=result
    elif 'queryarray[]' in d:		# Take query array, won't find
        result=[]
        queryarray=d['queryarray[]']
        for query in queryarray:
            result.append(sqlitequery(d['database'],query))
        data=result
    else:
        data=['empty. blurg']

    output = json.dumps(data,indent=1) 

    response_headers = [('Content-type', 'application/json')]
    start_response(status,response_headers)
   
    return [output]

