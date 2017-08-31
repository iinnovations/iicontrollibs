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

    import inventorylib
    from iiutilities import dblib, datalib
    from iiutilities.utility import newunmangle
    from time import time

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    formname = post.getvalue('name')


    output = {}
    output['keys'] = ''

    if 'REMOTE_ADDR' in environ:
        output['remote_ip'] = environ['REMOTE_ADDR']

    d = {}
    for k in post.keys():
        # print(k)
        d[k] = post.getvalue(k)

    status = '200 OK'
    # Run stuff as requested
    # We use the dynamic function to allow various  
    # types of queries
    output['data'] = []
    output['message'] = ''

    # print('** original')
    # print(d)
    d = newunmangle(d)
    # print('** unmangled')
    # print(d)

    """
    Here we verify credentials of session data against those in the database.
    While we authenticate in the browser, this does not stop POST queries to the API without the page provided
    So we take the hpass stored in the dictionary and verify.

    * Which databases are available are stored in users table, column accesskeywords
    * Which one is currently in use is stored in table usermeta, data where user=username. data is json-encoded metadata
        pathalias field

    * What path extension this corresponds to is stored in pathaliases

    """

    # I dont' think this will be used. We will get pathalias from database. Let's deal with changing it later.

    # First, let's get our pathalias and translate to a path, using our path reloader

    # if 'pathalias' in d:
    #     output['message'] += inventorylib.reloaddatapaths(pathalias=d['pathalias'])
    # else:
    #     output['message'] += 'No pathalias found in dictionary. '

    wsgiauth = True
    authverified = False

    if wsgiauth:

        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in database.
        import hashlib

        safe_database = dblib.sqliteDatabase(inventorylib.sysvars.dirs.dbs.safe)
        if 'username' in d and d['username']:
            output['message'] += 'Session user is ' + d['username'] + '. '
        else:
            output['message'] += 'No session user found. '
            d['username'] = ''

        if d['username']:
            try:
                condition = "name='" + d['username'] + "'"
                user_data = safe_database.read_table_row('users', condition=condition)[0]
            except:
                output['message'] += 'error in user sqlite query for session user "' + d['username'] + '". '
                user_data = {'accesskeywords':'demo','admin':False}
            else:
                # Get session hpass to verify credentials
                hashedpassword = d['hpass']
                hname = hashlib.new('sha1')
                hname.update(d['username'])
                hashedname = hname.hexdigest()
                hentry = hashlib.new('md5')
                hentry.update(hashedname + inventorylib.sysvars.salt + hashedpassword)
                hashedentry = hentry.hexdigest()
                if hashedentry == user_data['password']:
                    # successful auth
                    output['message'] += 'Password verified. '
                    authverified = True
                    # output['message'] += 'accesskeywords : ' + str(userdata)
                    output['accesskeywords'] = user_data['accesskeywords']
                    if output['accesskeywords'].find(',') >= 0:
                        accesskeywords = output['accesskeywords'].split(',')
                        accesskeywords = [accesskeyword.strip() for accesskeyword in accesskeywords]
                    else:
                        accesskeywords = output['accesskeywords'].strip()

                    path_aliases = safe_database.read_table('pathaliases')

                    # Find usermeta entry and grab which database is selected. If one is not selected, update selection
                    # to first that user is allowed to access
                    try:
                        user_meta_row = safe_database.read_table_row('usermeta', condition="user='" + d['username'] + "'")[0]
                    except:
                        print('error getting usermeta for username ' + d['username'])
                        output['message'] += 'error getting usermeta for username ' + d['username']
                        user_meta_row = []
                        return

                    path_alias = ''
                    if not user_meta_row:
                        output['message'] += 'User meta entry not found. Attempting to create. '

                        # assign default database
                        default_database = accesskeywords[0]

                        output['message'] += 'Choosing pathalias from first in keywords: ' + default_database + '. '
                        if any(default_database == path_alias['alias'] for path_alias in path_aliases):
                            output['message'] += 'Verified that default alias exists in pathaliases database. '
                        else:
                            output['message'] += 'ERROR: first entry in keywords (' +default_database + ') not found in aliases. '

                        # Insert usermeta entry. This should never happen.
                        safe_database.insert('usermeta', {'user':d['username'], 'data':'pathalias:' + default_database})
                        path_alias = default_database
                    else:
                        output['message'] += 'User meta entry found with text ' + str(user_meta_row) + '. '

                        # Parse the string into json and ensure that the pathalias is in there
                        user_meta_dict = datalib.parseoptions(user_meta_row['data'])
                        if 'pathalias' in user_meta_dict:
                            path_alias = user_meta_dict['pathalias']
                            output['message'] += 'pathalias found: ' + user_meta_dict['pathalias'] + '. '

                            if any(path_alias == stored_path_alias['alias'] for stored_path_alias in path_aliases):
                                output['message'] += 'Verified that default alias exists in pathaliases database. '

                    if path_alias:
                        # reload datapaths with path alias
                        reload_message = inventorylib.reloaddatapaths(pathalias=path_alias)

                        # DEFINITELY COMMENT THIS OUT FOR SECURITY SAKE (absolute paths are secret!!)
                        output['message'] += reload_message
        else:
            # Demo status
            authverified = True
            user_data = {'authlevel':0}

    else:
        output['message'] += 'WSGI authorization not enabled. '

    if authverified or not wsgiauth:
        output['authorized'] = True
    else:
        output['authorized'] = False

    try:
        action = d['action']
    except KeyError:
        output['message'] = 'no action in request'
        action = ''

    if output['authorized'] and action:
        output['action_allowed'] = inventorylib.check_action_auths(action, user_data['authlevel'])
    else:
        output['action_allowed'] = False

    if output['authorized'] and output['action_allowed']:

        # Stock functions
        if action == 'addeditpart':
            output['message'] += 'addpart keyword found. '
            output = inventorylib.addeditstockpart(d, output)
            inventorylib.calcstockfromall()
        elif action == 'copypart':
            output['message'] += 'copypart keyword found. '
            output = inventorylib.copystockpart(d, output)
            inventorylib.calcstockfromall()
        elif action == 'deleteparts':
            output['message'] += 'deleteparts keyword found. '
            output = inventorylib.deletestockparts(d, output)
            inventorylib.calcstockfromall()
        elif action == 'gettrackedpartdata':
            output['message'] += 'gettrackedpartdata keyword found. '
            output['data'] = inventorylib.calcstockfromall(**d)['trackedpart']
        elif action =='generateorders':
            output['message'] += 'generate orders keyword found. '
            inventorylib.generateandaddorders()

        # Inventory functions
        # Edit and add are separated, as names are autogenerated
        elif action == 'editinventory':
            output['message'] += 'editinventory keyword found. '
            output = inventorylib.editinventory(d, output)
            inventorylib.calcstockfromall()
        elif action == 'addinventory':
            output['message'] += 'addinventory keyword found. '
            output = inventorylib.createnewinventory(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteinventories':
            output['message'] += 'deleteinventories keyword found. '
            output = inventorylib.deleteinventories(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditinventorypart':
            output['message'] += 'addeditinventorypart keyword found. '
            output = inventorylib.addeditpartlist(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deletepartsfrominventory':
            output['message'] += 'deletepartsfrominventory keyword found. '
            output = inventorylib.deletepartsfrominventory(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()

        # Order functions
        elif action == 'editorder':
            output['message'] += 'editorder keyword found. '
            output = inventorylib.editorder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addorder':
            output['message'] += 'addorder keyword found. '
            output = inventorylib.createneworder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteorders':
            output['message'] += 'deleteorders keyword found. '
            output = inventorylib.deleteorders(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditorderpart':
            output['message'] += 'addeditorderpart keyword found. '
            output = inventorylib.addeditpartlist(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditorderparts':
            output['message'] += 'addeditorderparts keyword found. '
            if 'partsdata' in d:
                output = inventorylib.addeditpartlist(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'deletepartsfromorder':
            output['message'] += 'deletepartsfromorder keyword found. '
            output = inventorylib.deletepartsfromorder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()

        # BOM functions
        elif action == 'copybom':
            output['message'] += 'copybom keyword found. '
            output = inventorylib.copybom(d, output)
            inventorylib.makebommetadata()
        elif action == 'addeditbom':
            output['message'] += 'addeditbom keyword found. '
            output = inventorylib.addeditbom(d, output)
            inventorylib.makebommetadata()
        elif action == 'addeditbomparts':
            output['message'] += 'addeditbomparts keyword found. '
            # Operate on partsdata
            d['partsdata'] = json.loads(d['partsdata'])
            output = inventorylib.addeditpartlist(d, output)
            inventorylib.makebommetadata()
        elif action == 'getbomcalcs':
            output['message'] += 'getbomcalcs keyword found. '
            output = inventorylib.calcbomprice(d, output)
        elif action == 'getquotecalcs':
            output['message'] += 'getquotecalcs keyword found. '
            output['message'] += 'function not written yet. '
            # output = inventorylib.calcbomprice(d, output)
        elif action == 'deletepartsfrombom':
            output['message'] += 'deletepartsfrombom keyword found. '
            output = inventorylib.deletepartsfrombom(d, output)
            inventorylib.makebommetadata()
        elif action == 'deleteboms':
            output['message'] += 'deleteboms keyword found. '
            output = inventorylib.deleteboms(d, output)
            inventorylib.makebommetadata()

        # Assembly functions
        elif action == 'copyassembly':
            output['message'] += 'copyassembly keyword found. '
            output = inventorylib.copyassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'copybomintoassembly':
            output['message'] += 'copybomintoassembly keyword found. '
            output = inventorylib.copybomintoassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditassembly':
            output['message'] += 'addeditassembly keyword found. '
            output = inventorylib.addeditassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditassemblypart':
            output['message'] += 'addeditassemblypart keyword found. '
            output = inventorylib.addeditpartlist(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'getassemblycalcs':
            output['message'] += 'getassemblycalcs keyword found. '
            output = inventorylib.calcassemblyprice(d, output)
        elif action == 'deletepartsfromassembly':
            output['message'] += 'deletepartsfromassembly keyword found. '
            output = inventorylib.deletepartsfromassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteassemblys':
            output['message'] += 'deleteassemblys keyword found. '
            output = inventorylib.deleteassemblies(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()

        # Quotes
        elif action == 'deletequotes':
            output['message'] += 'deletequotes keyword found. '
            output = inventorylib.deletequotes(d, output)
            inventorylib.makebommetadata(database=inventorylib.sysvars.dirs.dbs.quotes)
        elif action == 'copyquotetoboms':
            output['message'] += 'copyquotetoboms keyword found. '
            output = inventorylib.copyquotetoboms(d, output)
            inventorylib.makebommetadata()

        # Export functions

        elif action == 'exportbomtopdf':
            output['message'] += 'exportbomtopdf keyword found. '
            output = inventorylib.writepanelbomtopdf(d, output)

            thetime = datalib.gettimestring()
            cleantime = thetime.replace(' ', '_').replace(':', '_')

            # Get bom from boms database
            bom = dblib.readalldbrows(inventorylib.sysvars.dirs.dbs.boms, d['name'])

            cleanbomname = d['name'].replace(' ','_').replace(':','_')
            filename = cleanbomname + '_' + cleantime
            outputroot = '/var/www/html/panelbuilder/data/downloads/'

            weblink = 'https://panelbuilder.interfaceinnovations.org/data/downloads/' + filename

            inventorylib.writepanelbomtopdf(**{'bomdata': bom,
                                      'title': 'Bom generated from ' + d['name'] + ' ' + cleantime,
                                          'outputfile': outputroot + filename})

            output['data']['weblink'] = weblink

        elif action == 'exportassemblytopdf':
            output['message'] += 'exportassemblytopdf keyword found. '

            thetime = datalib.gettimestring()
            cleantime = thetime.replace(' ', '_').replace(':', '_')

            # Get bom from boms database
            assemblydata = dblib.readalldbrows(inventorylib.sysvars.dirs.dbs.assemblies, d['name'])

            cleanname = d['name'].replace(' ','_').replace(':','_')
            filename = cleanname + '_' + cleantime + '.pdf'
            outputroot = '/var/www/html/panelbuilder/data/downloads/'

            weblink = 'https://panelbuilder.interfaceinnovations.org/data/downloads/' + filename

            inventorylib.writepanelbomtopdf(**{'bomdata': assemblydata,
                                      'title': 'Bom generated from ' + d['name'] + ' ' + thetime,
                                          'format':'picklist','outputfile': outputroot + filename})

            output['data'] = {'assemblydata':assemblydata}
            output['weblink'] = weblink

        # Panel builder
        elif action in ['panelcalcs', 'panelcalcsgenquote']:
            output['message'] += 'panelcalc keyword found. '
            import panelbuilder
            for key,value in d.iteritems():
                # print(key, value)
                pass

            if 'paneldesc' in d:
                import json
                d['paneldesc'] = json.loads(d['paneldesc'])

            bomresults = panelbuilder.paneltobom(**d)

            output['data'] = {}
            # d needs to have a 'paneldesc' key with the panel spec data in it.
            output['data']['bomdescription'] = bomresults['bomdescription']
            output['data']['options'] = bomresults['options']
            output['data']['bomcalcs'] = inventorylib.calcbomprice({'bomdictarray':bomresults['bom']})['data']
            output['message'] += bomresults['message']

            # We don't actually want to return the full boms by default. We don't want this in the client, and it's
            # lot of data anyway
            if 'returnfullboms' not in d:
                for option, value in output['data']['options'].iteritems():
                    if 'bom' in value:
                        print('Deleting bom from option ' + str(option))

                        del output['data']['options'][option]['bom']
                    if 'flatbom' in value:
                        print('Deleting flatbom from option ' + str(option))
                        del output['data']['options'][option]['flatbom']

            if action == 'panelcalcsgenquote':
                thetime = datalib.gettimestring()
                cleantime = thetime.replace(' ','_').replace(':','_')
                outputroot = '/var/www/html/panelbuilder/data/downloads/'

                if 'paneltype' in d['paneldesc'] and d['paneldesc']['paneltype'] == 'brewpanel':
                    datedquotefilename = 'panelbuilder_brew_quote_' + cleantime + '.pdf'
                    datedbomfilename = 'panelbuilder_brew_bom_' + cleantime + '.pdf'
                    genericquotefilename = 'panelbuilder_brew_quote.pdf'
                    genericbomfilename = 'panelbuilder_brew_bom.pdf'
                elif 'paneltype' in d['paneldesc'] and d['paneldesc']['paneltype'] == 'temppanel':
                    datedquotefilename = 'panelbuilder_temp_quote_' + cleantime + '.pdf'
                    datedbomfilename = 'panelbuilder_temp_bom_' + cleantime + '.pdf'
                    genericquotefilename = 'panelbuilder_temp_quote.pdf'
                    genericbomfilename = 'panelbuilder_temp_bom.pdf'
                else:
                    datedquotefilename = 'panelbuilder_quote_' + cleantime + '.pdf'
                    datedbomfilename = 'panelbuilder_bom_' + cleantime + '.pdf'
                    genericquotefilename = 'panelbuilder_quote.pdf'
                    genericbomfilename = 'panelbuilder_bom.pdf'

                weblink = 'https://panelbuilder.interfaceinnovations.org/data/downloads/' + datedquotefilename

                # until we can get this to format properly in the pdf, we are going to leave it generic
                # description = output['data']['bomdescription']
                description = 'Control panel quote generated by panelbuilder.'
                datedquotes = True

                # Create quote pdf from BOM
                if datedquotes:

                    inventorylib.writepanelquotetopdf(**{'bomdata': bomresults['bom'], 'options': bomresults['options'],
                        'title':'Quote auto-generated by panelbuilder   \t\t' +
                        datalib.gettimestring(), 'price': str(output['data']['bomcalcs']['totalprice']),
                    'outputfile': outputroot + datedquotefilename, 'description':description})

                inventorylib.writepanelquotetopdf(**{'bomdata': bomresults['bom'], 'options': bomresults['options'],
                        'title':'Quote auto-generated by panelbuilder '+ thetime,
                       'price': output['data']['bomcalcs']['totalprice'], 'outputfile':outputroot + genericquotefilename})

                # Create database entry BOM

                # Create table
                # print('** DATABASE')
                # print(panelbuilder.sysvars.dirs.dbs.quotes)

                bomname = 'quote_' + cleantime
                output = inventorylib.addeditbom({'bomdata':{'name':bomname}, 'database':panelbuilder.sysvars.dirs.dbs.quotes}, output)
                # print('** BOM **')
                # print(bomresults['bom'])
                inserts = []
                for part in bomresults['bom']:
                    inserts.append(dblib.makesqliteinsert(bomname, [part['partid'],part['qty']], ['partid','qty']))
                dblib.sqlitemultquery(inventorylib.sysvars.dirs.dbs.quotes, inserts)
                inventorylib.makebommetadata(database=inventorylib.sysvars.dirs.dbs.quotes)

                # output = inventorylib.addeditpartlist(d, output)


                # Create pdfs

                if datedquotes:
                    inventorylib.writepanelbomtopdf(**{'bomdata': bomresults['bom'], 'options': bomresults['options'],
                        'title':'Quote auto-generated by panelbuilder '
                      + thetime, 'outputfile': outputroot + datedbomfilename})

                inventorylib.writepanelbomtopdf(**{'bomdata': bomresults['bom'], 'title': 'panelbuilder BOM generated ' + thetime,
                                 'outputfile': outputroot + genericbomfilename, 'totalprice': output['data']['bomcalcs']['totalprice']})

                output['data']['quotelink'] = weblink
                from iiutilities.utility import gmail
                mymail = gmail(subject="Quote generated")
                mymail.message = 'Quote generated at ' + cleantime + '\r\n'

                if 'remote_ip' in output:
                    mymail.message = 'IP address ' + output['remote_ip'] + '\r\n'

                mymail.message += bomresults['bomdescription']
                mymail.recipient = 'quotes@interfaceinnovations.org'
                mymail.sender = 'II Panelbuilder'
                mymail.send()


        # Multi-use
        elif action == 'reloaditemdatafromstock':
            output['message'] += 'reloaditemdatafromstock keyword found. '
            output = inventorylib.refreshpartsfromstock(d, output)
            if 'bomname' in d:
                inventorylib.recalcpartdata(bomname=d['bomname'])
                inventorylib.makebommetadata()
            elif 'assemblyame' in d:
                inventorylib.recalcpartdata(assemblyname=d['assemblyname'])
                inventorylib.makeassemblymetadata()

        # Generic functions
        elif action == 'gettablenames':
            dbpath = inventorylib.dbnametopath(d['database'])
            try:
                output['data'] = dblib.gettablenames(dbpath)
            except:
                output['message'] += 'Error getting table names'
        elif action == 'switchtablerows':
            dbpath = inventorylib.dbnametopath(d['database'])
            dblib.switchtablerows(dbpath, d['tablename'], d['row1'], d['row2'], d['uniqueindex'])
        elif action == 'modwsgistatus':
            output['processgroup'] = repr(environ['mod_wsgi.process_group'])
            output['multithread'] = repr(environ['wsgi.multithread'])
        elif action == 'gettabledata':
            output['message']+='Gettabledata. '
            if 'database' in d:
                dbpath = inventorylib.dbnametopath(d['database'])
                if dbpath:
                    output['message'] += 'Friendly name ' + d['database'] + ' translated to path ' + dbpath + ' successfully. '

                    if 'tablenames[]' in d:  # Get multiple tables
                        output['message'] += 'Multiple tables. '
                        data = []
                        if 'start' in d:
                            fixedstart = int(d['start'])
                        else:
                            fixedstart = 0
                        if 'length' in d:
                            fixedlength = int(d['length'])
                        else:
                            fixedlength = 1
                        if 'lengths[]' in d:
                            lengths = map(int, d['lengths[]'])
                        else:
                            lengths = []
                        if 'starts[]' in d:
                            starts = map(int, d['starts'])
                        else:
                            starts = []

                        for index, table in enumerate(d['tablenames[]']):
                            try:
                                length = lengths[index]
                            except IndexError:
                                length = fixedlength
                            try:
                                start = starts[index]
                            except IndexError:
                                start = fixedstart

                            data.append(dblib.dynamicsqliteread(dbpath, table, start, length))
                            output['data']=data
                    elif 'length' in d:  # Handle table row subset
                        output['message']+='Length keyword. '
                        if not 'start' in d:
                            d['start'] = 0
                        thetime = time()
                        output['data'] = dblib.dynamicsqliteread(dbpath, d['tablename'], d['start'], d['length'])
                        output['querytime'] = time() - thetime
                    elif 'row' in d:  # Handle table row
                        output['message'] += 'Row keyword. ' + str(d['row'])
                        thetime = time()
                        output['data'] = dblib.dynamicsqliteread(dbpath, d['tablename'], d['row'])
                        output['querytime'] = time() - thetime
                    elif 'tablename' in d:  # Handle entire table
                        output['message'] += 'Tablename keyword: ' + d['tablename'] + '. '
                        thetime = time()
                        if 'condition' in d:
                            if not d['condition'] == '':
                                output['data'] = dblib.dynamicsqliteread(dbpath, d['tablename'], condition=d['condition'])
                            else:
                                output['data'] = dblib.dynamicsqliteread(dbpath, d['tablename'])
                        else:
                            try:
                                output['data'] = dblib.dynamicsqliteread(dbpath, d['tablename'])
                            except:
                                output['message'] += 'Error retrieving data. '
                            else:
                                output['message'] += 'Data query appears successful. '
                        output['querytime'] = time() - thetime
                else:
                    output['message'] += 'Friendly name ' + d['database'] + ' unsuccessfully translated. '
            else:
                output['message'] += 'No database present in action request'
        else:
            output['message'] = 'no command matched for action "' + action + '"'
    else:
        # status = '403 Forbidden'
        output['message'] += 'Not authorized for this action (or perhaps at all?) '

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

