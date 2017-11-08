def application(environ, start_response):
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
    from time import time

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    try:
        post = json.loads(request_body.decode('utf-8'))
    except:
        print('Error decoding: ')
        print(request_body.decode('utf-8'))
        post = {}

    output = {'message': ''}
    status = '200 OK'

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

    # if 'pathalias' in post:
    #     output['message'] += inventorylib.reloaddatapaths(pathalias=post['pathalias'])
    # else:
    #     output['message'] += 'No pathalias found in postictionary. '

    wsgiauth = True
    authverified = False

    if wsgiauth:

        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in postatabase.
        import hashlib

        safe_database = dblib.sqliteDatabase(inventorylib.sysvars.dirs.dbs.safe)
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
                output['message'] += 'error in user sqlite query for session user "' + post['username'] + '". '
                user_data = {'accesskeywords':'demo','admin':False}
            else:
                # Get session hpass to verify credentials
                hashedpassword = post['hpass']
                hname = hashlib.new('sha1')
                hname.update(post['username'].encode('utf-8'))
                hashedname = hname.hexdigest()
                hentry = hashlib.new('md5')
                hentry.update((hashedname + inventorylib.sysvars.salt + hashedpassword).encode('utf-8'))
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
                        user_meta_row = safe_database.read_table_row('usermeta', condition="user='" + post['username'] + "'")[0]
                    except:
                        print('error getting usermeta for username ' + post['username'])
                        output['message'] += 'error getting usermeta for username ' + post['username']
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
                        safe_database.insert('usermeta', {'user':post['username'], 'data':'pathalias:' + default_database})
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
        action = post['action']
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
            inventorylib.addeditstockpart(d, output)
            inventorylib.calcstockfromall()
        elif action == 'copypart':
            output['message'] += 'copypart keyword found. '
            inventorylib.copystockpart(d, output)
            inventorylib.calcstockfromall()
        elif action == 'deleteparts':
            output['message'] += 'deleteparts keyword found. '
            inventorylib.deletestockparts(d, output)
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
            inventorylib.editinventory(d, output)
            inventorylib.calcstockfromall()
        elif action == 'addinventory':
            output['message'] += 'addinventory keyword found. '
            inventorylib.createnewinventory(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteinventories':
            output['message'] += 'deleteinventories keyword found. '
            inventorylib.deleteinventories(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditinventorypart':
            output['message'] += 'addeditinventorypart keyword found. '
            inventorylib.addeditpartlist(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deletepartsfrominventory':
            output['message'] += 'deletepartsfrominventory keyword found. '
            inventorylib.deletepartsfrominventory(d, output)
            inventorylib.makeinventorymetadata()
            inventorylib.calcstockfromall()

        # Order functions
        elif action == 'editorder':
            output['message'] += 'editorder keyword found. '
            inventorylib.editorder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addorder':
            output['message'] += 'addorder keyword found. '
            inventorylib.createneworder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteorders':
            output['message'] += 'deleteorders keyword found. '
            inventorylib.deleteorders(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditorderpart':
            output['message'] += 'addeditorderpart keyword found. '
            inventorylib.addeditpartlist(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditorderparts':
            output['message'] += 'addeditorderparts keyword found. '
            if 'partsdata' in post:
                post['partsdata'] = json.loads(post['partsdata'])
                inventorylib.addeditpartlist(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()
        elif action == 'deletepartsfromorder':
            output['message'] += 'deletepartsfromorder keyword found. '
            inventorylib.deletepartsfromorder(d, output)
            inventorylib.makeordermetadata()
            inventorylib.calcstockfromall()

        # BOM functions
        elif action == 'copybom':
            output['message'] += 'copybom keyword found. '
            inventorylib.copybom(d, output)
            inventorylib.makebommetadata()
        elif action == 'addeditbom':
            output['message'] += 'addeditbom keyword found. '
            inventorylib.addeditbom(d, output)
            inventorylib.makebommetadata()
        elif action == 'addeditbomparts':
            output['message'] += 'addeditbomparts keyword found. '
            # Operate on partsdata
            post['partsdata'] = json.loads(post['partsdata'])
            inventorylib.addeditpartlist(d, output)
            inventorylib.makebommetadata()
        elif action == 'getbomcalcs':
            output['message'] += 'getbomcalcs keyword found. '
            inventorylib.calcbomprice(d, output)
        elif action == 'getquotecalcs':
            output['message'] += 'getquotecalcs keyword found. '
            output['message'] += 'function not written yet. '
            # inventorylib.calcbomprice(d, output)
        elif action == 'deletepartsfrombom':
            output['message'] += 'deletepartsfrombom keyword found. '
            inventorylib.deletepartsfrombom(d, output)
            inventorylib.makebommetadata()
        elif action == 'deleteboms':
            output['message'] += 'deleteboms keyword found. '
            inventorylib.deleteboms(d, output)
            inventorylib.makebommetadata()

        # Assembly functions
        elif action == 'copyassembly':
            output['message'] += 'copyassembly keyword found. '
            inventorylib.copyassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'copybomintoassembly':
            output['message'] += 'copybomintoassembly keyword found. '
            inventorylib.copybomintoassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditassembly':
            output['message'] += 'addeditassembly keyword found. '
            inventorylib.addeditassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'addeditassemblyparts':
            output['message'] += 'addeditassemblypart keyword found. '
            post['partsdata'] = json.loads(post['partsdata'])
            inventorylib.addeditpartlist(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
            
        elif action == 'getassemblycalcs':
            output['message'] += 'getassemblycalcs keyword found. '
            inventorylib.calcassemblyprice(d, output)
        elif action == 'deletepartsfromassembly':
            output['message'] += 'deletepartsfromassembly keyword found. '
            inventorylib.deletepartsfromassembly(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()
        elif action == 'deleteassemblys':
            output['message'] += 'deleteassemblys keyword found. '
            inventorylib.deleteassemblies(d, output)
            inventorylib.makeassemblymetadata()
            inventorylib.calcstockfromall()

        # Quotes
        elif action == 'deletequotes':
            output['message'] += 'deletequotes keyword found. '
            inventorylib.deletequotes(d, output)
            inventorylib.makebommetadata(database=inventorylib.sysvars.dirs.dbs.quotes)
        elif action == 'copyquotetoboms':
            output['message'] += 'copyquotetoboms keyword found. '
            inventorylib.copyquotetoboms(d, output)
            inventorylib.makebommetadata()

        # Export functions

        elif action == 'exportbomtopdf':
            output['message'] += 'exportbomtopdf keyword found. '
            inventorylib.writepanelbomtopdf(d, output)

            thetime = datalib.gettimestring()
            cleantime = thetime.replace(' ', '_').replace(':', '_')

            # Get bom from boms database
            bom = dblib.readalldbrows(inventorylib.sysvars.dirs.dbs.boms, post['name'])

            cleanbomname = post['name'].replace(' ','_').replace(':','_')
            filename = cleanbomname + '_' + cleantime
            outputroot = '/var/www/html/panelbuilder/data/downloads/'

            weblink = 'https://panelbuilder.interfaceinnovations.org/data/downloads/' + filename

            inventorylib.writepanelbomtopdf(**{'bomdata': bom,
                                      'title': 'Bom generated from ' + post['name'] + ' ' + cleantime,
                                          'outputfile': outputroot + filename})

            output['data']['weblink'] = weblink

        elif action == 'exportassemblytopdf':
            output['message'] += 'exportassemblytopdf keyword found. '

            thetime = datalib.gettimestring()
            cleantime = thetime.replace(' ', '_').replace(':', '_')

            # Get bom from boms database
            assemblydata = dblib.readalldbrows(inventorylib.sysvars.dirs.dbs.assemblies, post['name'])

            cleanname = post['name'].replace(' ','_').replace(':','_')
            filename = cleanname + '_' + cleantime + '.pdf'
            outputroot = '/var/www/html/panelbuilder/data/downloads/'

            weblink = 'https://panelbuilder.interfaceinnovations.org/data/downloads/' + filename

            inventorylib.writepanelbomtopdf(**{'bomdata': assemblydata,
                                      'title': 'Bom generated from ' + post['name'] + ' ' + thetime,
                                          'format':'picklist','outputfile': outputroot + filename})

            output['data'] = {'assemblydata':assemblydata}
            output['weblink'] = weblink

        # Panel builder
        elif action in ['panelcalcs', 'panelcalcsgenquote']:
            output['message'] += 'panelcalc keyword found. '
            import panelbuilder
            for key,value in post.items():
                # print(key, value)
                pass

            if 'paneldesc' in post:
                import json
                post['paneldesc'] = json.loads(post['paneldesc'])

            bomresults = panelbuilder.paneltobom(**d)

            output['data'] = {}
            # d needs to have a 'paneldesc' key with the panel spec data in it.
            output['data']['bomdescription'] = bomresults['bomdescription']
            output['data']['options'] = bomresults['options']
            output['data']['bomcalcs'] = inventorylib.calcbomprice({'bomdictarray':bomresults['bom']})['data']
            output['message'] += bomresults['message']

            # We don't actually want to return the full boms by default. We don't want this in the client, and it's
            # lot of data anyway
            if 'returnfullboms' not in post:
                for option, value in output['data']['options'].items():
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

                if 'paneltype' in post['paneldesc'] and post['paneldesc']['paneltype'] == 'brewpanel':
                    datedquotefilename = 'panelbuilder_brew_quote_' + cleantime + '.pdf'
                    datedbomfilename = 'panelbuilder_brew_bom_' + cleantime + '.pdf'
                    genericquotefilename = 'panelbuilder_brew_quote.pdf'
                    genericbomfilename = 'panelbuilder_brew_bom.pdf'
                elif 'paneltype' in post['paneldesc'] and post['paneldesc']['paneltype'] == 'temppanel':
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
                inventorylib.addeditbom({'bomdata':{'name':bomname}, 'database':panelbuilder.sysvars.dirs.dbs.quotes}, output)
                # print('** BOM **')
                # print(bomresults['bom'])
                inserts = []
                for part in bomresults['bom']:
                    inserts.append(dblib.makesqliteinsert(bomname, [part['partid'],part['qty']], ['partid','qty']))
                dblib.sqlitemultquery(inventorylib.sysvars.dirs.dbs.quotes, inserts)
                inventorylib.makebommetadata(database=inventorylib.sysvars.dirs.dbs.quotes)

                # inventorylib.addeditpartlist(d, output)


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
            inventorylib.refreshpartsfromstock(post, output)
            if 'bomname' in post:
                inventorylib.recalcpartdata(bomname=post['bomname'])
                inventorylib.makebommetadata()
            elif 'assemblyame' in post:
                inventorylib.recalcpartdata(assemblyname=post['assemblyname'])
                inventorylib.makeassemblymetadata()

        # Generic functions
        elif action == 'gettablenames':
            dbpath = inventorylib.dbnametopath(post['database'])
            try:
                output['data'] = dblib.gettablenames(dbpath)
            except:
                output['message'] += 'Error getting table names'
        elif action == 'switchtablerows':
            dbpath = inventorylib.dbnametopath(post['database'])
            dblib.switchtablerows(dbpath, post['tablename'], post['row1'], post['row2'], post['uniqueindex'])
        elif action == 'modwsgistatus':
            output['processgroup'] = repr(environ['mod_wsgi.process_group'])
            output['multithread'] = repr(environ['wsgi.multithread'])
        elif action == 'gettabledata':
            output['message']+='Gettabledata. '
            if 'database' in post:
                dbpath = inventorylib.dbnametopath(post['database'])
                if dbpath:
                    output['message'] += 'Friendly name ' + post['database'] + ' translated to path ' + dbpath + ' successfully. '

                    if 'tablenames' in post:  # Get multiple tables
                        output['message'] += 'Multiple tables. '
                        data = []
                        if 'start' in post:
                            fixedstart = int(post['start'])
                        else:
                            fixedstart = 0
                        if 'length' in post:
                            fixedlength = int(post['length'])
                        else:
                            fixedlength = 1
                        if 'lengths' in post:
                            lengths = map(int, post['lengths[]'])
                        else:
                            lengths = []
                        if 'starts' in post:
                            starts = map(int, post['starts'])
                        else:
                            starts = []

                        for index, table in enumerate(post['tablenames[]']):
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
                    elif 'length' in post:  # Handle table row subset
                        output['message']+='Length keyword. '
                        if not 'start' in post:
                            post['start'] = 0
                        thetime = time()
                        output['data'] = dblib.dynamicsqliteread(dbpath, post['tablename'], post['start'], post['length'])
                        output['querytime'] = time() - thetime
                    elif 'row' in post:  # Handle table row
                        output['message'] += 'Row keyword. ' + str(post['row'])
                        thetime = time()
                        output['data'] = dblib.dynamicsqliteread(dbpath, post['tablename'], post['row'])
                        output['querytime'] = time() - thetime
                    elif 'tablename' in post:  # Handle entire table
                        output['message'] += 'Tablename keyword: ' + post['tablename'] + '. '
                        thetime = time()
                        if 'condition' in post:
                            if not post['condition'] == '':
                                output['data'] = dblib.dynamicsqliteread(dbpath, post['tablename'], condition=post['condition'])
                            else:
                                output['data'] = dblib.dynamicsqliteread(dbpath, post['tablename'])
                        else:
                            try:
                                output['data'] = dblib.dynamicsqliteread(dbpath, post['tablename'])
                            except:
                                output['message'] += 'Error retrieving data. '
                            else:
                                output['message'] += 'Data query appears successful. '
                        output['querytime'] = time() - thetime
                else:
                    output['message'] += 'Friendly name ' + post['database'] + ' unsuccessfully translated. '
            else:
                output['message'] += 'No database present in action request'
        else:
            output['message'] = 'no command matched for action "' + action + '"'
    else:
        # status = '403 Forbidden'
        output['message'] += 'Not authorized for this action (or perhaps at all?) '

    print(' I AM HERE ')
    if 'data' in output:
        if output['data']:
            newetag = hashlib.md5(str(output['data']).encode('utf-8')).hexdigest()
            if 'etag' in post:
                if newetag == post['etag']:
                    status = '304 Not Modified'
                    output['data'] = ''
        else:
            newetag=''
    else:
        newetag=''

    if 'datasize' in post:
        output['datasize'] = sys.getsizeof(output['data'])

    output['etag'] = newetag
    # try:
    foutput = json.dumps(output, indent=1)
    print('FOUTPUT')
    print(type(foutput))
    # except:
    #     import csv
    #     w = csv.writer(open("/usr/lib/iicontrollibs/inventory/dumperr.log", "w"))
    #     for key, val in output.items():
    #         w.writerow([key, val])
    response_headers = [('Content-type', 'application/json')]
    response_headers.append(('Etag',newetag))
    start_response(status, response_headers)

    return foutput.encode('utf-8')

