def application(environ, start_response):
 
    import cgi
    import json

    # Set top folder to allow import of modules

    import os,sys,inspect
    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    import cupid.controllib as controllib
    import cupid.pilib as pilib

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    output=''

    formname=post.getvalue('name')

    d={}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'

    # assign current function

    action = post.getvalue("action")

    if 'subaction' not in post.keys():
        subaction = None 
    else:
        subaction = post.getvalue("subaction")

    if 'table' not in post.keys():
        table = None 
    else:
        table = post.getvalue("table")

    if 'valuename' not in post.keys():
        valuename = None 
    else:
        valuename = post.getvalue("valuename")

    if 'condition' not in post.keys():
        condition = None 
    else:
        condition = post.getvalue("condition")

    if 'value' not in post.keys():
        value = None 
    else:
        value = post.getvalue("value")

    if 'database' in post.keys():
        database = post.getvalue("database")
    else:
        database = None

    if 'channelname' in post.keys():
        channelname = post.getvalue("channelname")
    else:
        channelname = None 

    if 'newmode' in post.keys():
        newmode = post.getvalue("newmode")
    else:
        newmode = None 

    if 'outputname' in post.keys():
        outputname = post.getvalue("outputname")
    else:
        outputname = None 

    if 'index' in post.keys():
        index = post.getvalue("index")
    else:
        index = None 

    # carry out generic set value
    if action=='setvalue' and database and table and valuename and value:
        output+='Carrying out setvalue. '
        if condition:
            pilib.setsinglevalue(database,table,valuename,value,condition)
        elif index:
            condition='rowid= ' + index
            pilib.setsinglevalue(database,table,valuename,value,condition)
        else:
            pilib.setsinglevalue(database,table,valuename,value)
        
        
    # act on action

    if action=='spchange' and database:
        output+='Spchanged. '
        if subaction=='incup':
            controllib.incsetpoint(database,channelname)
            output+='incup. '
        if subaction=='incdown':
            controllib.decsetpoint(database,channelname)
            output+='incdown. '
        if subaction=='setvalue':
            controllib.setsetpoint(database,channelname,value)
            output+='Setvalue: ' + database + ' ' + channelname + ' ' + value
    elif action=='togglemode' and database!='none':
        controllib.togglemode(database,channelname)
    elif action=='setmode' and database!='none':
        controllib.setmode(database,channelname,mode)
    elif action=='setrecipe':
        recipe=post.getvalue('recipe')
        controllib.setrecipe(database,channelname,recipe)
    elif action=='setcontrolinput':
        controlinput=post.getvalue('controlinput')
        controllib.setcontrolinput(database,channelname,controlinput)
    elif action=='setchannelenabled':
        newstatus=post.getvalue('newstatus') 
        controllib.setchannelenabled(database,channelname,newstatus)
    elif action=='setchanneloutputsenabled':
        newstatus=post.getvalue('newstatus') 
        controllib.setchanneloutputsenabled(database,channelname,newstatus)

    elif action=='manualactionchange' and database!='none' and channelname!='none' and subaction != 'none':
        curchanmode=controllib.getmode(database,channelname)
        if curchanmode == 'manual':
            if subaction == 'poson': 
                controllib.setaction(database,channelname,'100.0')
            elif subaction == 'negon': 
                controllib.setaction(database,channelname,'-100.0')
            else: 
                controllib.setaction(database,channelname,'0.0')
    elif action=='setposoutput' and database!='none' and channelname!='none' and outputname!='none':
        controllib.setposout(database,channelname,outputname)
    elif action=='setnegoutput' and database!='none' and channelname!='none':
        controllib.setnegout(database,channelname,outputname)
    elif action=='actiondown' and database!='none' and channelname!='none':
        curchanmode=controllib.getmode(database,channelname)
        if curchanmode=="manual":
            curaction=int(controllib.getaction(database,channelname))
            if curaction==100:
	        nextvalue=0
            elif curaction==0:
                nextvalue=-100
            elif curaction==-100:
                nextvalue=-100
            else:
                nextvalue=0
            controllib.setaction(database,channelname,nextvalue) 
    elif action=='actionup' and database!='none' and channelname!='none':

        curchanmode=controllib.getmode(database,channelname)
        if curchanmode=="manual":
            curaction=int(controllib.getaction(database,channelname))
            if curaction==100:
	        nextvalue=100
            elif curaction==0:
                nextvalue=100
            elif curaction==-100:
                nextvalue=0
            else:
                nextvalue=0
            controllib.setaction(database,channelname,nextvalue) 
    output += 'Status complete.'  

    response_headers = [('Content-type', 'text/plain'), ('Content-Length',str(len(output)))]
    start_response(status,response_headers)
   
    return [output]


    

