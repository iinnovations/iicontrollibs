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
    output = ''

    formname=post.getvalue('name')

    d={}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'

    # assign current function

    action = post.getvalue("action")

    if 'subaction' in d:
        subaction = d["subaction"]
    else:
        subaction = False

    if 'table' in d:
        table = d["table"]
    else:
        table = False

    if 'valuename' in d:
        valuename = d["valuename"]
    else:
        valuename = False

    if 'condition' in d:
        condition = d["condition"]
    else:
        condition = False

    if 'value' in d:
        value = d["value"]
    else:
        value = False

    if 'database' in d:
        database = d["database"]
    else:
        database = False

    if 'channelname' in d:
        channelname = d["channelname"]
    else:
        channelname = False

    if 'newmode' in d:
        newmode = d["newmode"]
    else:
        newmode = False

    if 'outputname' in d:
        outputname = d["outputname"]
    else:
        outputname = False

    if 'index' in d:
        index = d["index"]
    else:
        index = False

    if 'systemflag' in d:
        systemflag = d['systemflag']

    # carry out generic set value
    if action == 'setsystemflag':
        database = pilib.systemdatadatabase
        pilib.setsinglevalue(database, 'systemflags', 'value', 1, "name=\'" + systemflag + "'")
    elif action == 'rundaemon':
        from cupiddaemon import rundaemon
        rundaemon()
    elif action=='setvalue':
        if database and table and valuename and value:
            output+='Carrying out setvalue. '
            if condition:
                pilib.setsinglevalue(database,table,valuename,value,condition)
            elif index:
                condition='rowid= ' + index
                pilib.setsinglevalue(database,table,valuename,value,condition)
            else:
                pilib.setsinglevalue(database,table,valuename,value)
        else:
             output+='Insufficient data for setvalue '
    elif action == 'spchange' and database:
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
    elif action=='togglemode' and database!='None':
        controllib.togglemode(database,channelname)
    elif action=='setmode' and database!='None':
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
    elif action=='manualactionchange' and database and channelname and subaction:
        curchanmode=controllib.getmode(database,channelname)
        if curchanmode == 'manual':
            if subaction == 'poson': 
                controllib.setaction(database,channelname,'100.0')
            elif subaction == 'negon': 
                controllib.setaction(database,channelname,'-100.0')
            else: 
                controllib.setaction(database,channelname,'0.0')
    elif action=='setposoutput' and database and channelname and outputname:
        controllib.setposout(database,channelname,outputname)
    elif action=='setnegoutput' and database and channelname:
        controllib.setnegout(database,channelname,outputname)
    elif action=='actiondown' and database and channelname:
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
    elif action=='actionup' and database and channelname:
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
    elif action=='deletechannelbyname' and database and channelname:
        pilib.sqlitequery(database, 'delete channelname from channels where name=\"' + channelname + '\"')
    output += 'Status complete.'  

    response_headers = [('Content-type', 'text/plain'), ('Content-Length',str(len(output)))]
    start_response(status,response_headers)
   
    return [output]


    

