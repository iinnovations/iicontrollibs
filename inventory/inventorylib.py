#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


from iiutilities import utility

sysvars = utility.Bunch()
sysvars.dirs = utility.Bunch()

sysvars.salt = 'my inventory salt'

sysvars.dirs.dbs = utility.Bunch()

sysvars.defaultdbalias = 'demo'
sysvars.dirs.safedataroot = '/var/www/credentials/inventory/'
sysvars.dirs.dbs.safe = sysvars.dirs.safedataroot + 'safe.db'
sysvars.dirs.dbs.authlog = sysvars.dirs.safedataroot + 'authlog.db'

# Set a default dataroot here. We do this mostly for code completion, but also for quick development
# ( reimport without having to reload paths each time )

sysvars.dirs.defaultdataroot = '/var/www/html/inventory/data/iiinventory/'

sysvars.dirs.dataroot = sysvars.dirs.defaultdataroot
sysvars.dirs.download = sysvars.dirs.dataroot + 'download/'

sysvars.dirs.dbs.system = sysvars.dirs.dataroot + 'system.db'
sysvars.dirs.dbs.stock = sysvars.dirs.dataroot + 'stock.db'
sysvars.dirs.dbs.boms = sysvars.dirs.dataroot + 'boms.db'
sysvars.dirs.dbs.inventories = sysvars.dirs.dataroot + 'inventories.db'
sysvars.dirs.dbs.orders = sysvars.dirs.dataroot + 'orders.db'
sysvars.dirs.dbs.assemblies = sysvars.dirs.dataroot + 'assemblies.db'


tableitems = utility.Bunch()
tableitems.stockpartproperties = ['partid', 'description', 'qtystock', 'qtyonorder', 'qtyreserved', 'qtyavailable',
                           'cost', 'costqty', 'costqtyunit', 'supplier', 'supplierpart', 'manufacturer',
                           'manufacturerpart', 'notes', 'partdata', 'datasheet', 'inuse', 'datecreated',
                           'createdby', 'inventory', 'minqty', 'type']
tableitems.bompartproperties = ['partid', 'description', 'qty', 'qtyunit', 'cost', 'price', 'totalcost', 'totalprice', 'costqty', 'costqtyunit',
                             'supplier', 'supplierpart', 'manufacturer', 'manufacturerpart', 'notes', 'partdata',
                             'datasheet', 'type', 'marginmethod', 'margin', 'inventory']
tableitems.orderpartproperties = ['partid', 'description', 'qty', 'qtyunit', 'cost', 'price', 'totalcost', 'totalprice', 'costqty', 'costqtyunit',
                             'supplier', 'supplierpart', 'manufacturer', 'manufacturerpart', 'notes', 'partdata',
                             'datasheet', 'type', 'marginmethod', 'margin', 'inventory', 'received']

# Experimental -- use complete databaseentry description. Could roll this up into a dict, but this is more condensed

tableitems.assemblypartproperties = ['partid', 'description', 'qty', 'qtyunit', 'cost', 'price', 'totalcost', 'totalprice', 'costqty', 'costqtyunit',
                             'supplier', 'supplierpart', 'manufacturer', 'manufacturerpart', 'notes', 'partdata',
                             'datasheet', 'type', 'marginmethod', 'margin', 'inventory']

tableitems.assemblyparttypes = ['text', 'text', 'real', 'text', 'real', 'real', 'real', 'real', 'real', 'real', 'text',
                                'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'real', 'text']

tableitems.assemblypartoptions = ['primary', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '' ]

tableitems.inventorypartproperties = ['partid', 'qtystock']

tableitems.bommetaitems = ['status', 'name', 'cost', 'price', 'profit', 'modified', 'created', 'used', 'notes']
tableitems.bommetadefaultvalues = ['active','','','','','','','','']

tableitems.ordermetaitems = ['status', 'orderstatus', 'executed', 'name', 'supplier', 'desc', 'cost', 'price', 'modified', 'created', 'used', 'notes']
tableitems.ordermetadefaultvalues = ['active', '', '', '','','','', '', '', '','','']

tableitems.inventorymetaitems = ['status', 'executed', 'name', 'desc', 'modified', 'created', 'used', 'notes']
tableitems.inventorymetadefaultvalues = ['active', '', '','','','','','']

tableitems.assemblymetaitems = ['status', 'executed', 'reserved', 'name', 'cost', 'price', 'modified', 'created', 'used', 'notes']
tableitems.assemblymetadefaultvalues = ['active', '', '','', '','','','','','']


def reloaddatapaths(**kwargs):
    from iiutilities import dblib, datalib

    # default, reset in absolute path option
    sysvars.dirs.dataroot = '/var/www/html/inventory/data/'

    message = 'Running reloaddatapaths. '
    reload = False
    if 'relativepath' in kwargs:
        message += 'Relativepath keyword found. '
        relpath = kwargs['relpath']
        sysvars.dirs.dataroot = '/var/www/html/inventory/data/' + relpath + '/'
        reload = True

    elif 'absolutepath' in kwargs:
        message += 'absolutepath keyword found. '
        sysvars.dirs.dataroot = kwargs['absolutepath']
        reload = True

    elif 'pathalias' in kwargs:
        # Get path for alia
        message += 'Pathalias keyword '+ kwargs['pathalias'] +' found. '
        relpath = dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'pathaliases', 'path', "alias='" + kwargs['pathalias'] + "'")
        message += 'relpath ' + relpath  + ' retrieved. '
        sysvars.dirs.dataroot = '/var/www/html/inventory/data/' + relpath + '/'
        reload = True

    elif 'user' in kwargs:
        # Set path to default for user
        message += 'user: ' + kwargs['user'] + '. '
        usermeta = datalib.parseoptions(dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'data', "user='" + kwargs['user'] + "'"))
        message += 'database' + usermeta['database'] + '. '
        relpath = dblib.getsinglevalue(dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'pathaliases', 'path', "alias='" + usermeta['database']))
        message += 'relpath: ' + relpath + '. '
        sysvars.dirs.dataroot = '/var/www/html/inventory/data/' + relpath + '/'
        reload = True
    else:
        message += 'no keywords found. reverting to default: ' + sysvars.defaultdbalias + '. '

        try:
            relpath = dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'pathaliases', 'path', "alias='" +
                                                                sysvars.defaultdbalias + "'")
        except:
            message += 'error in relpath query on default for default from database: ' + sysvars.dirs.dbs.safe + '. '
            message += 'query was: ' + dblib.makegetsinglevaluequery('pathaliases', 'path', "alias='" +
                                                                sysvars.defaultdbalias)  + "'" + '. '
            message += 'reverting to empty relpath' + '. '
            relpath = ''
        else:
            message += 'relpath "' + relpath + '" successfully retrieved. ' + '. '
        sysvars.dirs.dataroot = '/var/www/html/inventory/data/' + relpath + '/'
        reload = True

    if reload:
        message += 'reloading' + '. '
        message += 'dataroot: ' + sysvars.dirs.dataroot + '. '

        sysvars.dirs.dbs.system = sysvars.dirs.dataroot + 'system.db'
        sysvars.dirs.dbs.stock = sysvars.dirs.dataroot + 'stock.db'
        sysvars.dirs.dbs.boms = sysvars.dirs.dataroot + 'boms.db'
        sysvars.dirs.dbs.inventories = sysvars.dirs.dataroot + 'inventories.db'
        sysvars.dirs.dbs.orders = sysvars.dirs.dataroot + 'orders.db'
        sysvars.dirs.dbs.assemblies = sysvars.dirs.dataroot + 'assemblies.db'
    else:
        message += 'not reloading (no keyword found?)' + '. '

    return message


"""
Utilities
"""


def dbnametopath(friendlyname):
    friendlynames = ['stockdb', 'bomsdb', 'inventoriesdb', 'ordersdb', 'assembliesdb']
    paths = [sysvars.dirs.dbs.stock, sysvars.dirs.dbs.boms, sysvars.dirs.dbs.inventories, sysvars.dirs.dbs.orders,
             sysvars.dirs.dbs.assemblies]
    path = None
    if friendlyname in friendlynames:
        path = paths[friendlynames.index(friendlyname)]
    return path


def exportbomtopdf(**kwargs):
    output = {'message':'', 'status':0}
    if 'bomname' not in kwargs:
        output['message'] += 'No bomname in arguments. Exiting. '
        return output

    fields = ['partid','qty','description']
    if 'fields' in kwargs:
        fields = kwargs['fields']
    from iiutilities import utility
    try:
        pdfreturn = utility.writetabletopdf(**{'database':sysvars.dirs.dbs.boms, 'tablename':kwargs['bomname'],
                                               'outputfile':sysvars.dirs.download + kwargs['bomname'] + '.pdf', 'fields':fields})
    except:
        output['message'] += 'Uncaught error in make pdf routine. '
        output['status'] = 1
        return output
    else:
        if pdfreturn['status']:
            output['message'] += 'Caught error in write pdf: "' + pdfreturn['message'] + '". '
            return output
        else:
            output['message'] += 'That seemed to work out. '

    return output


"""
Shared Functions
"""


def recalcpartdata(**kwargs):

    """
    Recalculating part quantities is a common thing, so we condense it for different tables here.

    Stock:
    * if margintype is not 'custom', retrieve and set margin for each item
    * calculate qtyavailable, qtystatus
    * cost and price of stock, onorder, available, totalcost

    BOMs:
    * if margintype is not 'custom', retrieve and set margin for each item
    * calculate cost and price of each item

    Orders:
    * if margintype is not 'custom', retrieve and set margin for each item
    * calculate cost and price of each item
    """

    if 'output' not in kwargs:
        output = {'message':''}

    from iiutilities import dblib

    if 'stock' in kwargs:
        type='stock'
        database = sysvars.dirs.dbs.stock
        tablenames = ['stock']
    elif 'ordername' in kwargs:
        type='order'
        database = sysvars.dirs.dbs.orders
        tablenames = [str(kwargs['ordername'])]
    elif 'orders' in kwargs:
        type='orders'
        database = sysvars.dirs.dbs.orders
        if kwargs['orders']:
            # Run array of orders
            tablenames = kwargs['orders']
        else:
            # Run all orders
            tablenames = dblib.gettablenames(database).remove('metadata')

    elif 'bomname' in kwargs:
        type='bom'
        database = sysvars.dirs.dbs.boms
        tablenames = [kwargs['bomname']]

    elif 'boms' in kwargs:
        type='boms'
        database = sysvars.dirs.dbs.boms

        if kwargs['boms']:
            # Run array of orders
            tablenames = kwargs['boms']
        else:
            # Run all orders
            # print(database)
            tablenames = dblib.gettablenames(database)
            # print(tablenames)
            tablenames.remove('metadata')

    elif 'partdictarray' in kwargs:
        type = 'partdictarray'
        # Run on partdictarray sent through
        tablenames = ['placeholder']

    else:
        output['message'] += 'No appropriate keyword found. '
        return output


    # print('Tables')
    # print(tablenames)

    newtables = []
    for tablename in tablenames:
        if type == 'partdictarray':
            if 'dictarray' in kwargs:
                table = kwargs['dictarray']
            else:
                output['message'] += 'here keyword received, but no dictarray present. '
                return
        else:
            table = dblib.readalldbrows(database, tablename)

        newtable = []
        for item in table:
            # Items we want to update
            # Update number available
            # print(type)

            if type == 'stock':

                try:
                    temp = float(item['qtystock'])
                except:
                    item['qtystock']=0

                try:
                    temp = float(item['qtyreserved'])
                except:
                    item['qtyreserved']=0

                try:
                    temp = float(item['qtyonorder'])
                except:
                    item['qtyonorder']=0


                item['qtyavailable'] = float(item['qtystock']) + float(item['qtyonorder']) - float(item['qtyreserved'])

                # Update qty status based on  inventory available
                if item['qtyavailable'] > 0:
                    item['qtystatus'] = 'available'
                elif item['qtyavailable'] == 0:
                    item['qtystatus'] = 'none'
                elif item['qtyavailable'] < 0:
                    item['qtystatus'] = 'toorder'

                # Update total cost on stock and onorder qty
                try:
                    temp = float(item['cost'])
                except:
                    item['cost']=0

                try:
                    temp = float(item['costqty'])
                except:
                    item['costqty']=1

                try:
                    item['stockcost'] = float(item['qtystock']) * float(item['cost']) / float(item['costqty'])
                except:
                    item['stockcost'] = 0
                try:
                    item['onordercost'] = float(item['qtyonorder']) * float(item['cost']) / float(item['costqty'])
                except:
                    item['onordercost'] = 0
                item['totalcost'] = item['stockcost'] + item['onordercost']


            # Get margin
            if 'marginmethod' in item and 'margin' in item:
                if not item['marginmethod']:
                    item['marginmethod']='type'
                if item['marginmethod'] == 'type':
                    try:
                        item['margin'] = dblib.getsinglevalue(sysvars.dirs.dbs.system, 'calcs', 'value', "item='" + item['type'] + "margin'")
                        # print('margin: '  + str(item['margin']))
                    except:
                        item['margin'] = 0

            if type == 'stock':
                # Calc prices based on margin
                item['stockprice'] = (1 + float(item['margin'])) * item['stockcost']
                item['onorderprice'] = (1 + float(item['margin'])) * item['stockcost']
                item['totalprice'] = item['stockprice'] + item['onorderprice']
                try:
                    item['price'] = (1 + float(item['margin'])) * float(item['cost'])
                except:
                    item['price'] = 0

            # This will weed out stock, as stock does not have the plain 'qty' field

            if all(key in item for key in ['cost', 'totalcost', 'qty', 'costqty']):
                # Fill in blank quantity with zero
                try:
                    item['qty']=float(item['qty'])
                except:
                    item['qty']=0

                try:
                    item['totalcost'] = float(item['qty']) * float(item['cost']) / float(item['costqty'])
                except:
                    item['totalcost'] = 0
                try:
                    item['price'] = (1 + float(item['margin'])) * float(item['cost'])
                except:
                    item['price'] = 0

            if all(key in item for key in ['price', 'totalprice', 'qty', 'costqty']):
                try:
                    item['totalprice'] = (1 + float(item['margin'])) * item['totalcost']
                except:
                    # print('FAIL')
                    # print(tablename)
                    # print(item['partid'])
                    return



            newtable.append(item)
        print(len(newtable))
        newtables.append(newtable)

    if type == 'stock':
        dblib.insertstringdicttablelist(database, 'stock', newtables[0], droptable=False)
    if type in ['order', 'orders', 'bom', 'boms']:
        for tablename, anewtable in zip(tablenames, newtables):
            # print('TABLENAME')
            # print(tablename)
            # print('TABLE')
            # print(anewtable)
            if len(anewtable) > 0:
                dblib.insertstringdicttablelist(database, tablename, anewtable, droptable=True)
            else:
                # print('empty table')
                pass
    return {'tables': newtables, 'output': output}


def addeditpartlist(d, output={'message':''}):


    """

    We are going to use this for BOMs, orders, and assemblies.
    Minor differences are contained in meta, with exceptions for items:

    Order and assembly items have status field. This will just magically appear in the items, however, as taken
    from the itemslist in the globals


    We typically grab all properties of a part from the stock database before we call this, in the UI populated fields.
    We don't always want to, however, so we have the option of filling from the stock database. This means we can be
    incomplete. So 'add three of part A003' with 'copystock'='missing' will add all of the part data to the BOM or
    order, minimizing required data transfer and simplifying operations. 'copystock'='all' will overwrite all sent data
    except for quantity and partid.

    So to use this function as a 'refresh data from stock', simply call it, for example, with a bomname and a list of
    parts with 'copystock'='all'

    """

    stockdb = sysvars.dirs.dbs.stock
    ordersdb = sysvars.dirs.dbs.orders
    bomsdb = sysvars.dirs.dbs.boms
    inventoriesdb = sysvars.dirs.dbs.inventories
    assembliesdb = sysvars.dirs.dbs.assemblies

    if 'bomname' in d:
        output['message'] += 'bomname key present. '
        type = 'bom'
        activedb = bomsdb
        tablekey = 'bomname'
        listpartproperties = tableitems.bompartproperties

    elif 'ordername' in d:
        output['message'] += 'ordername key present. '
        type = 'order'
        activedb = ordersdb
        tablekey = 'ordername'
        listpartproperties = tableitems.orderpartproperties

    elif 'assemblyname' in d:
        output['message'] += 'assemblyname key present. '
        type = 'assembly'
        activedb = assembliesdb
        tablekey = 'assemblyname'
        listpartproperties = tableitems.assemblypartproperties

    elif 'inventoryname' in d:
        output['message'] += 'inventoryname key present. '
        type = 'inventory'
        activedb = inventoriesdb
        tablekey = 'inventoryname'
        listpartproperties = tableitems.inventorypartproperties


    else:
        output['message'] += 'No suitable keyword present for command. Terminating. '
        return output

    if 'partdata' not in d:
        output['message'] += 'No partdata present in request. Terminating. '
        return output

    if 'message' not in output:
        output['message'] = ''

    if 'copystock' not in d:
        d['copystock'] = 'none'

    from iiutilities import dblib, datalib

    tablename = str(d[tablekey])

    # Determine whether or not the part already exists in the BOM
    listparts = dblib.readalldbrows(activedb, tablename)

    # This is just columns
    # Eventually this should be more robust and actually enforce types by pragma
    ordercolumns = dblib.getpragmanames(activedb,tablename)
    # print(ordercolumns)
    # return

    if d['copystock'] in ['all', 'missing']:
        # Get the stock part entry for reference and backfill purposes
        try:
            stockpart = dblib.readonedbrow(stockdb, 'stock', condition="partid='" + d['partdata']['partid'] + "'")[0]
        except:
            stockpart = None
            pass
            # print('error in stockpart result')

        # revert to no copystock if we can't find the part
        if not stockpart:
            d['copystock'] = 'none'
            stockpart = {}
    else:
        stockpart = {}

    # print('MATCH PART STOCK ITEM')
    # print(stockpart)

    """
    We are going to totally rebuild the database, in case part database format changes.

    We are only going to do
    this, however, if a sample part that exists in the database does not contain all the fields of the new entry
    We do this because there are concurrency issues with recreating simultaneously with, for example multiple
    asynchronous calls. Insert operations are atomic, however, so if we can run insert whenever possible, we will
    do that.
    """

    # Test: (again, this should eventually test pragma and properly form a database using types)
    inclusive = True
    if ordercolumns:
        for property in listpartproperties:
            if property not in ordercolumns:
                inclusive = False
                break

    newparts = []
    thenewpart = {}

    """
    We iterate over every part in the order.
    We make a new part.
    If the part we are modifying matches, matchpart = True and partexists = True
    """

    partexists = False
    for orderpart in listparts:

        newpart = {'partid': orderpart['partid']}
        matchpart = False
        if orderpart['partid'] == d['partdata']['partid']:
            output['message'] += 'Part ' + orderpart['partid'] + ' / ' + d['partdata']['partid'] + ' was found. '
            matchpart = True
            partexists = True

        # If we have a match, copy all data from previous part and stockpart where appropriate
        # depending on backfill options.

        for property in listpartproperties:
            if matchpart:

                if d['copystock'] == 'all' and property != 'qty':
                    # get all part data from stock entry
                    # except qty, which is special
                    newpart[property] = stockpart[property]
                else:
                    if property in d['partdata']:
                        # print('property ' + property + ' found in partdata')
                        # make sure not empty
                        if d['partdata'][property]:
                            newpart[property] = d['partdata'][property]
                            continue

                    # Combined elif via continue
                    # Have to protect against properties that are in order and not stock
                    if d['copystock'] == 'missing' and property in stockpart:
                        # get part data if available from stock entry
                        newpart[property] = stockpart[property]
                    else:
                        # print('empty property  ' + property)
                        newpart[property] = ''

            # If we don't have a match, just copy existing properties, mapped appropriately
            else:
                if property in orderpart:
                    newpart[property] = orderpart[property]
                else:
                    newpart[property] = ''


        # We make a single copy to use if we are not reconstructing database
        newparts.append(newpart)
        if matchpart:
            thenewpart = newpart.copy()

    if not partexists:
        output['message'] += 'Part not found. Creating from scratch. '
        if 'partid' in d['partdata']:
            output['message'] += 'key partdata[partid] found in d with value ' + d['partdata']['partid'] + '. '
            newpart = {'partid':d['partdata']['partid']}

            for property in listpartproperties:
                if d['copystock'] == 'all' and property != 'qty':
                    # get all part data from stock entry
                    # except qty, which is special
                    newpart[property] = stockpart[property]
                else:
                    if property in d['partdata']:
                        # print('property ' + property + ' found')

                        # make sure not empty
                        if d['partdata'][property]:
                            newpart[property] = d['partdata'][property]
                            continue
                        else:
                            # print('property empty.')
                            pass

                    # Have to protect against properties that are in order and not stock
                    # print('input dictionary' )
                    # print(d)
                    if d['copystock'] == 'missing':
                        # print('at copystock for property ' + property)
                        pass
                    if d['copystock'] == 'missing' and property in stockpart:
                        # get part data if available from stock entry
                        newpart[property] = stockpart[property]
                    else:
                        newpart[property] = ''

            newparts.append(newpart)
            thenewpart = newpart.copy()
        else:
            output['message'] += 'key partdata[partid] not found in d. '

    output['message'] += 'Reinserting. '
    if inclusive:
        output['message'] += 'Structure was found to be inclusive. Not rebuilding. '
        if partexists:
            dblib.sqlitedeleteitem(activedb, tablename, "partid='" + thenewpart['partid'] + "'")

        # print(thenewpart)
        try:
            dblib.insertstringdicttablelist(activedb, tablename, [thenewpart], droptable=False)
        except:
            output['message'] += 'Error in query on "' + activedb + '" + and table "' + tablename + '. '
    else:
        output['message'] += 'Structure was not found to be inclusive. rebuilding. '
        dblib.insertstringdicttablelist(activedb, tablename, newparts, droptable=True)

    # Recalculate quantities. Autotyped based on kwargs
    recalcpartdata(**{tablekey: tablename})

    return output


def refreshpartsfromstock(d, output={'message':''}):

    from iiutilities import dblib

    notouchkeys = ['qty','partid']
    if 'bomname' in d:
        output['message'] += 'bomname found. '
        if 'partids' in d:
            output['message'] += 'partids found. '
            for partid in d['partids']:
                output['message'] += 'processing ' + partid + '. '
                condition = "partid='" + partid + "'"
                try:
                    stockpart = dblib.readonedbrow(sysvars.dirs.dbs.stock, 'stock', condition=condition)[0]
                except:
                    output['message'] += 'No stock part found for condition ' + condition + '. '
                    return output

                try:
                    bomentry = dblib.readonedbrow(sysvars.dirs.dbs.boms, d['bomname'], condition=condition)[0]
                except:
                    output['message'] += 'No bomentry found for condition ' + condition + '. '
                    return output

                for key, value in stockpart.iteritems():
                    if key not in notouchkeys and key in bomentry:
                        bomentry[key] = stockpart[key]
                dblib.sqlitedeleteitem(sysvars.dirs.dbs.boms, d['bomname'], condition=condition)
                # print(bomentry)
                dblib.insertstringdicttablelist(sysvars.dirs.dbs.boms, d['bomname'], [bomentry])


    return output



"""
Stock functions
"""


def addeditstockpart(d, output={'message': ''}):

    from iiutilities import dblib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    requiredkeywords = ['partid', 'description']
    # requiredkeywords = ['partid', 'description', 'manufacturer', 'manufacturerpart']
    try:
        allowedkeywords = dblib.getpragmanames(sysvars.dirs.dbs.stock, 'stock')
    except:
        output['message'] += 'Error getting allowedkeywords from table automatically. Reverting to defaults. '
        allowedkeywords = tableitems.stockpartproperties


    # requiredkeys = []
    # for keyword in requiredkeywords:
    #     requiredkeys.append('partdata[' + keyword + ']')
    #
    # allowedkeys = []
    # for keyword in allowedkeywords:
    #     allowedkeys.append('partdata[' + keyword + ']')


    addpart = True
    for keyword in requiredkeywords:
        if keyword not in d['partdata']:
            output['message'] += 'Keyword ' + keyword + ' not found in partdata. '
            addpart = False
        elif d['partdata'][keyword] == '':
            output['message'] += 'Keyword partdata[' + keyword + '] empty. '
            addpart = False
        else:
            output['message'] += 'Keyword partdata[' + keyword + '] found. '

        # maybe check to see if the part exists? Simple query. Otherwise it will just fail
        # gracefully, which is ok.

    if addpart:
        # If we are modifying the partid of an existing part, we will first update the old part to have the new partid.
        # Then we will grab it as if it always had that partid.
        if 'originalpartid' in d['partdata']:
            output['message'] += 'Found original partid. '
            if d['partdata']['originalpartid'] != '' and d['partdata']['originalpartid'] != d['partdata']['partid']:
                output['message'] += 'Found original partid. Updating ' + d['partdata']['originalpartid'] + ' to ' + d['partdata']['partid'] + ". "
                dblib.setsinglevalue(sysvars.dirs.dbs.stock, 'stock', 'partid', d['partdata']['partid'], "partid='" + d['partdata']['originalpartid'] + "'")
            else:
                output['message'] += 'Original part id is same as new partid. '

        # Pull the part and begin to update it
        matchparts = dblib.readalldbrows(sysvars.dirs.dbs.stock, 'stock', "partid='" + d['partdata']['partid'] + "'")
        if len(matchparts) > 0:
            # Part exists already
            output['message'] += 'Part exists already. '
            item = matchparts[0]
        else:
            output['message'] += 'Part does not already exist. '
            item = {}

        output['message'] += 'All necessary keywords found. Executing query. Values: '
        values = []
        valuenames = []
        # try:
        for keyword in allowedkeywords:
            if keyword in d['partdata']:
                # try:
                    values.append(d['partdata'][keyword])
                    # take the non-mangled version
                    valuenames.append(keyword)
                    item[keyword] = d['partdata'][keyword]
                    output['message'] += keyword + ':' + d['partdata'][keyword] + ','
                # except:
                #     output['message'] += 'Error with ' + key + ',' + keyword + '. '
        # except:
        #     output['message'] += 'Error getting values'


        try:
            # dblib.sqliteinsertsingle(sysvars.dirs.dbs.stock, 'stock', values, valuenames)
            dblib.insertstringdicttablelist(sysvars.dirs.dbs.stock, 'stock', [item], droptable=False)
        except:
            query = dblib.makesqliteinsert('stock', values, valuenames, True)
            output['message'] += 'Error executing query ' + query

    else:
        output['message'] += "No part data found. No action taken. "
        for key, value in d.iteritems():
            output['message'] += key + ': ' + value + '. '

    return output


def copystockpart(d={'partdata':{'partid': 'P001', 'description': 'testpart'}}, output={'message': ''}):

    from iiutilities import dblib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partdata' in d:
        if 'partid' in d['partdata']:
            pass
        else:
            output['message'] += 'No partid found in copy request dictionary. '
            return output
    else:
        output['message'] += 'No partdata found in copy request dictionary'

    matchparts = dblib.readalldbrows(sysvars.dirs.dbs.stock, 'stock', "partid='" + d['partdata']['partid'] + "'")
    if len(matchparts) > 0:
        # Part exists already
        output['message'] += 'Part does exist. '
        item = matchparts[0]
        item['partid'] += '_copy'
    else:
        output['message'] += 'Part not found. '
        return output

    try:
        dblib.insertstringdicttablelist(sysvars.dirs.dbs.stock, 'stock', [item], droptable=False)
    except:
        output['message'] += 'Error inserting copied part.'

    return output


def deletestockparts(d, output={'message': ''}):

    from iiutilities import dblib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    # Single element will not come through as list, unfortunately
    if 'partids' in d:
        if not isinstance(d['partids'],list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids found in copy request dictionary. '
        return output

    output['message'] += 'Partids: '  + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery('stock',"partid='" + id + "'"))

    dblib.sqlitemultquery(sysvars.dirs.dbs.stock, querylist)

    return output


def makestockmetadata(database=sysvars.dirs.dbs.stock):
    from iiutilities import dblib

    '''
    Calculate total worth of inventory parts.

    '''

    allstock = dblib.readalldbrows(database, 'stock')

    newstockdata = []
    for item in allstock:
        newstockdata.append(item.copy())
        pass


    dblib.dropcreatetexttablefromdict(database, 'metadata', newstockdata)


"""
Inventory functions
"""


def makeinventorymetadata(database=sysvars.dirs.dbs.inventories):
    from iiutilities import dblib

    '''

    << I think this can be the exact same for orders and inventories >>

    This recalculates really basic metadata. What it does NOT do is recalculate entry data.

    An inventory is a really simple table consisting of only partid and quantity.
    The metadata table will count items and total count, and most important keep data about
    execution, namely whether it has been executed, and when.

    Current Inventory meta has the format:
    << see table items >>

    This entry should be created when the BOM is created, and modified when it is modified
    '''

    allcurrentmeta = dblib.readalldbrows(database, 'metadata')

    tabledata = []
    tablenames = dblib.gettablenames(database)

    metaitems = tableitems.inventorymetaitems
    metadefaultvalues = tableitems.inventorymetadefaultvalues

    if not tablenames:
        print('no inventory tables')
        return

    for tablename in tablenames:
        if tablename == 'metadata':
            continue

        meta={}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentmeta in allcurrentmeta:
            if 'name' in currentmeta:
                if currentmeta['name'] == tablename:
                    meta = currentmeta

        # initialize if not found
        if not meta:
            meta = {}
            for item, value in zip(metaitems, metadefaultvalues):
                meta[item] = value

            # Then insert name to default dictionary
            meta['name'] = tablename

        # Get metadata for each table
        itemcount = dblib.gettablesize(database, tablename)
        meta['itemcount'] = itemcount
        print(meta)
        tabledata.append(meta)
    if tabledata:
        dblib.dropcreatetexttablefromdict(database, 'metadata', tabledata)
    else:
        dblib.sqlitedeleteallrecords(database, 'metadata')


def editinventory(d, output={'message': ''}):

    from iiutilities import dblib, datalib
    database = sysvars.dirs.dbs.inventories

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    try:
        data = d['inventorydata']
    except:
        output['message'] += 'Error extracting data from message. '
        return output

    if 'name' not in data:
        output['message'] += 'No inventoryname found in edit request dictionary. '
        return output


    # Pull the bom metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    # First we try to pull it. If it does not exist, we have to create it and then recreate the metadata table
    tablenames = dblib.gettablenames(database)
    tablenames.remove('metadata')
    tablenames.sort()
    mostrecenttablename = tablenames[-1]

    # print(d['bomdata']['name'])
    # print(bomnames)
    if data['name'] not in tablenames:
        output['message'] += 'tablename "' + data['name'] + '" does not exist. This should not have happened. '
        return output

    else:
        output['message'] += 'Item appears to exist. Continuing to edit. '

    # Now we revise the existing entry
    allowedkeywords = ['notes', 'desc', 'executed']

    for keyword in allowedkeywords:
        modified = False
        if keyword in data:
            modified = True
            condition = "name='" + data['name'] + "'"
            output['message'] += 'keyword ' + keyword + ' found with value: ' + data[keyword] + '. Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

        if modified:
            dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


def createnewinventory(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    # Going to leave this as items to make it generic. Inventories and orders are the same thing

    if 'database' in d:
        database = d['database']
    else:
        database = sysvars.dirs.dbs.inventories

    existingitems = dblib.gettablenames(database)
    try:
        existingitems.remove('metadata')
    except:
        # no metadata table for some reason
        pass

    if existingitems:
        try:
            existingitems.remove('metadata')
        except:
            pass
            # metadata was not in there (?!)
        existingitems.sort()
        newitemnumber = int(existingitems[-1])+1
    else:
        newitemnumber=1

    # Create a table with a single entry and then empty it
    emptydict = {}
    for item in tableitems.inventorypartproperties:
        emptydict[item] = ''
    dblib.dropcreatetexttablefromdict(database, str(newitemnumber), emptydict)
    dblib.sqlitedeleteallrecords(database, str(newitemnumber))

    if 'partsdictarray' in d:
        # sort by partid
        from operator import itemgetter
        partsdictarray = sorted(d['partsdictarray'], key=itemgetter('partid'))

        dblib.insertstringdicttablelist(database, str(newitemnumber), partsdictarray)

    makeinventorymetadata(database)

    # Set created date in meta
    dblib.setsinglevalue(database, 'metadata', 'created', datalib.gettimestring(), "name='" + str(newitemnumber) + "'")

    output['newitemnumber'] = newitemnumber

    return output


def deleteinventories(d, output={'message':''}):

    from iiutilities import dblib

    if 'inventoryname' in d:
        output['message'] += 'Single inventoryname found. '
        inventorynames = [d['bomname']]
    elif 'inventorynames' in d:
        output['message'] += 'Inventorynames keyword found. '
        if not d['inventorynames']:
            output['message'] += 'Empty inventorynames value. '
            return output
        else:
            inventorynames = d['inventorynames']

    for inventoryname in inventorynames:
        output['message'] += 'Deleting inventory with name' + inventoryname + '. '
        dblib.sqlitedroptable(sysvars.dirs.dbs.inventories, inventoryname)

    return output


def calcstockfromall(inventoriesdatabase=sysvars.dirs.dbs.inventories,
                     stockdatabase=sysvars.dirs.dbs.stock, ordersdatabase=sysvars.dirs.dbs.orders,
                     assembliesdatabase=sysvars.dirs.dbs.assemblies):

    from iiutilities import dblib, datalib
    inventorytables = dblib.gettablenames(inventoriesdatabase)
    orderstables = dblib.gettablenames(ordersdatabase)
    assembliestables = dblib.gettablenames(assembliesdatabase)

    allitems = []

    # print('** Inventories')
    inventorytables.sort()
    for inventorytable in inventorytables:
        # Date is in metadata table
        if inventorytable == 'metadata':
            continue

        # print(inventorytable)

        try:
            metaentry = dblib.readonedbrow(inventoriesdatabase, 'metadata', condition="name='" + inventorytable + "'")[0]
        except:
            # print('NO METAENTRY. OOPS')
            pass
        else:
            # inventory has been executed and should be reviewed
            if metaentry['executed']:
                # print('executed')
                inventoryitems = dblib.readalldbrows(inventoriesdatabase, inventorytable)

                for inventoryitem in inventoryitems:
                    # print('received: ' + inventoryitem['partid'])
                    summaryitem = {'date':metaentry['executed'], 'partid':inventoryitem['partid'], 'qtystock': inventoryitem['qtystock'], 'mode':'inventory'}
                    allitems.append(summaryitem)

    # print('** Orders')
    orderstables.sort()
    for orderstable in orderstables:
        # Date is in metadata table
        if orderstable == 'metadata':
            continue

        # print(orderstable)

        try:
            metaentry = dblib.readonedbrow(ordersdatabase, 'metadata', condition="name='" + orderstable + "'")[0]
        except:
            pass
            # print('NO METAENTRY. OOPS')
        else:
            # order has been executed and should be reviewed
            if metaentry['executed']:
                # print('executed')
                orderitems = dblib.readalldbrows(ordersdatabase, orderstable)

                for orderitem in orderitems:
                    if orderitem['received']:
                        # Denote as received into stock
                        # print('received: ' + orderitem['partid'])
                        summaryitem = {'date':orderitem['received'], 'partid':orderitem['partid'], 'qtystock': orderitem['qty'], 'mode':'change'}
                        allitems.append(summaryitem)
                    else:
                        # Denote as on order
                        # print('reserved: ' + orderitem['partid'])
                        summaryitem = {'date':orderitem['received'], 'partid':orderitem['partid'], 'qtyonorder': orderitem['qty'], 'mode':'change'}
                        allitems.append(summaryitem)
    
    
    print('** Assemblies')
    assembliestables.sort()
    for assembliestable in assembliestables:
        # Date is in metadata table
        if assembliestable == 'metadata':
            continue

        try:
            metaentry = dblib.readonedbrow(assembliesdatabase, 'metadata', condition="name='" + assembliestable + "'")[0]
        except:
            pass
            # print('NO METAENTRY. OOPS')
        else:
            # order has been executed and should be reviewed
            if metaentry['executed']:
                print('executed')
                orderitems = dblib.readalldbrows(assembliesdatabase, assembliestable)

                for orderitem in orderitems:
                    # Denote as taking out of stock
                    # print('executed: ' + orderitem['partid'])
                    summaryitem = {'date':metaentry['executed'], 'partid':orderitem['partid'], 'qtystock': -1 * float(orderitem['qty']), 'mode':'change'}
                    allitems.append(summaryitem)
            elif metaentry['reserved']:
                # print('reserved')
                orderitems = dblib.readalldbrows(assembliesdatabase, assembliestable)

                for orderitem in orderitems:
                    # Denote as taking out of stock
                    # print('reserved: ' + orderitem['partid'])
                    summaryitem = {'date':metaentry['reserved'], 'partid':orderitem['partid'], 'qtyreserved': orderitem['qty'], 'mode':'change'}
                    allitems.append(summaryitem)


    # Now iterate over all items to create a comprehensive stock
    # First sort by date
    from operator import itemgetter
    orderedlist = sorted(allitems, key=itemgetter('date'))

    # print(orderedlist)

    newstockparts = []

    # keep an index handy
    newstockpartids = []
    elementtypes = ['qtystock', 'qtyreserved', 'qtyonorder']
    for element in orderedlist:
        for elementtype in elementtypes:
            if elementtype in element:
                # print(elementtype)
                # print(element)
                valueexists = False
                partexists = False
                if element['partid'] in newstockpartids:
                    partexists = True
                    # print('part exists')
                    existingindex = newstockpartids.index(element['partid'])
                    existingelement = newstockparts[existingindex]
                    # print(existingelement)

                    # So we can have an element exist without the value type we are attempting to modify here.
                    if elementtype in existingelement:
                        valueexists = True

                if not partexists:
                    if element['mode'] == 'change':
                        pass
                        # print('warning: assigning part qty from change before inventory on item ' + element['partid'])

                    # This will be the typical new item inventory add here.
                    newstockparts.append({'partid':element['partid'], elementtype:element[elementtype]})
                    newstockpartids.append(element['partid'])

                else:
                    if valueexists:
                        if element['mode'] == 'change':
                            # print('changing existing value for part ' + element['partid'])
                            # print('old value: ' + str(newstockparts[existingindex][elementtype]))
                            newstockparts[existingindex][elementtype] = float(newstockparts[existingindex][elementtype]) + float(element[elementtype])
                            # print('new value: ' + str(newstockparts[existingindex][elementtype]))

                        elif element['mode'] == 'inventory':
                            newstockparts[existingindex][elementtype] = float(element[elementtype])

                    else:
                        print('value does not exist for part ' + element['partid'])
                        # This will be for adding a new vaue to an existing part, e.g. onorder to a qtystock item
                        # print('part exists but value does not. Setting new value. ')
                        newstockparts[existingindex][elementtype] = element[elementtype]


    # print(newstockparts)
    starttime = datalib.gettimestring()

    # set zero queries. This assumes the part already exists, which could prove problematic.
    queries = []
    queries.append('update stock set qtyreserved=0')
    queries.append('update stock set qtystock=0')
    queries.append('update stock set qtyonorder=0')
    for part in newstockparts:
        for elementtype in elementtypes:
            if elementtype in part:
                queries.append(dblib.makesinglevaluequery('stock', elementtype, str(part[elementtype]), condition="partid='" + part['partid'] + "'"))

    dblib.sqlitemultquery(stockdatabase, queries)

    elapsedtime = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(starttime)
    # print('Elapsed time: ' + str(elapsedtime))
    recalcpartdata(**{'stock':''})

    return queries

    
    # completeinventory=[]
    # partids=[]
    # for table in inventorytables:
    #     inventory = dblib.readalldbrows(database, table)
    #     for item in inventory:
    #         if item['partid'] in partids:
    #             index = partids.index(item['partid'])
    #             completeinventory[index] = item
    #         else:
    #             completeinventory.append(item)
    #             partids.append(item['partid'])
    #
    # dblib.insertstringdicttablelist(database, inventorytables[-1] + '_complete', completeinventory)


def deletepartsfrominventory(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    database = sysvars.dirs.dbs.inventories

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partids' in d and 'inventoryname' in d:
        if not isinstance(d['partids'],list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or inventoryname found in copy request dictionary. '
        return output

    output['message'] += 'inventoryname ' + d['inventoryname']
    output['message'] += 'Partids: '  + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['inventoryname'],"partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)


    # Update metadata
    condition = "name='"+ d['inventoryname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)


    return output


def importstockfromcsv(filename, database=sysvars.dirs.dbs.stock):

    from iiutilities import datalib, dblib
    if not filename:
        # print('no file selected')
        return None

    # Read csv datamap file
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1, keystolowercase=True)

    requiredkeys = ['partid', 'description']
    # iterate over header to make sure key quantities are found
    foundkeys = []
    for itemname in datamapdictarray[0]:
        if itemname in tableitems.stockpartproperties:
            # print('*** FOUND: ' + itemname)
            foundkeys.append(itemname)

    if all(key in foundkeys for key in requiredkeys):
        # print('ALL REQUIRE KEYS FOUND')
        pass
    else:
        # print("NOT ALL REQUIRED KEYS FOUND")
        return

    insertarray = []
    for dict in datamapdictarray:

        newitem = {}
        for key in foundkeys:
            newitem[key] = dict[key]

        # make sure necessary fields exist and are non-empty
        if all(newitem[key] for key in requiredkeys):
            insertarray.append(newitem)
        else:
            # print('item did not have proper keys')
            for key in requiredkeys:
                # print(key + ' : ' + dict[key])
                pass

    print(str(len(insertarray)) + ' items prepared for insertion from ' + str(len(datamapdictarray)))

    for insert in insertarray:
        result = dblib.insertstringdicttablelist(database, 'stock', [insert], droptable=False)
        if result['status']:
            # print('error on entry: ' + str(insertarray.index(insert)))
            # print(result['query'])
            # print(result['tb'])
            return


def updatepartnumbersfromcsv(filename, database=sysvars.dirs.dbs.stock):

    from iiutilities import datalib, dblib
    if not filename:
        # print('no file selected')
        return None

    # Read csv datamap file
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1, keystolowercase=True)

    if 'partid' in datamapdictarray[0] and 'manufacturerpart' in datamapdictarray[0]:
        print('fields found')
    else:
        return None

    subarray = []
    for dict in datamapdictarray:
        if dict['partid'] and dict['manufacturerpart']:
            subarray.append({'partid':dict['partid'], 'manufacturerpart':dict['manufacturerpart']})

    print(subarray)
    print(database)

    querylist=[]
    for sub in subarray:
        condition = "partid='" + sub['partid'] +"'"
        print(condition)
        print(sub['manufacturerpart'])
        query = dblib.makesinglevaluequery('stock', 'manufacturerpart', sub['manufacturerpart'], condition=condition)
        try:
            dblib.sqlitequery(database, query)
            print(query)
        except:
            print('Error with query:')
            print(query)

    for sub in subarray:
        condition = "partid='" + sub['partid'] +"'"
        print(condition)
        print(sub['manufacturerpart'])
        query = dblib.makesinglevaluequery('stock', 'supplierpart', sub['manufacturerpart'], condition=condition)
        try:
            dblib.sqlitequery(database, query)
            print(query)
        except:
            print('Error with query:')
            print(query)

    print('*** BOMS')
    bomnames=dblib.gettablenames(sysvars.dirs.dbs.boms)
    for bomname in bomnames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] +"'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(bomname, 'manufacturerpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.boms, query)
                print(query)
            except:
                print('Error with query:')
                print(query)

            query = dblib.makesinglevaluequery(bomname, 'supplierpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.boms, query)
                print(query)
            except:
                print('Error with query:')
                print(query)

    print('*** ASSEMBLIES')
    assemblynames=dblib.gettablenames(sysvars.dirs.dbs.assemblies)
    for assemblyname in assemblynames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] +"'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(assemblyname, 'manufacturerpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.assemblies, query)
                print(query)
            except:
                print('Error with query:')
                print(query)
            query = dblib.makesinglevaluequery(assemblyname, 'supplierpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.assemblies, query)
                print(query)
            except:
                print('Error with query:')
                print(query)

    print('*** ORDERS')
    ordernames=dblib.gettablenames(sysvars.dirs.dbs.orders)
    for ordername in ordernames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] +"'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(ordername, 'manufacturerpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.orders, query)
                print(query)
            except:
                print('Error with query:')
                print(query)
            query = dblib.makesinglevaluequery(ordername, 'supplierpart', sub['manufacturerpart'], condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.orders, query)
                print(query)
            except:
                print('Error with query:')
                print(query)


def createinventoryfromcsv(filename, database=sysvars.dirs.dbs.inventories):

    from iiutilities import datalib, dblib
    if not filename:
        # print('no file selected')
        return None

    # Read csv datamap file
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1, keystolowercase=True)

    requiredkeys = ['partid', 'qtystock']
    # iterate over header to make sure key quantities are found
    foundkeys = []
    for itemname in datamapdictarray[0]:
        if itemname in tableitems.inventorypartproperties:
            # print('*** FOUND: ' + itemname)
            foundkeys.append(itemname)

    print(foundkeys)
    if all(key in foundkeys for key in requiredkeys):
        # print('ALL REQUIRE KEYS FOUND')
        pass
    else:
        print("NOT ALL REQUIRED KEYS FOUND")
        return

    insertarray = []
    for dict in datamapdictarray:

        newitem = {}
        for key in foundkeys:
            newitem[key] = dict[key]

        # make sure necessary fields exist and are non-empty
        if all(newitem[key] for key in requiredkeys):
            insertarray.append(newitem)
        else:
            # print('item did not have proper keys')
            for key in requiredkeys:
                # print(key + ' : ' + dict[key])
                pass

    print(str(len(insertarray)) + ' items prepared for insertion from ' + str(len(datamapdictarray)))

    createnewinventory({'partsdictarray':insertarray})

    makeinventorymetadata()

    # for insert in insertarray:
    #     result = dblib.insertstringdicttablelist(database, 'stock', [insert], droptable=False)
    #     if result['status']:
    #         # print('error on entry: ' + str(insertarray.index(insert)))
    #         # print(result['query'])
    #         # print(result['tb'])
    #         return

"""
BOM Functions
"""


def makebommetadata(database=sysvars.dirs.dbs.boms):
    from iiutilities import dblib

    '''

    This recalculates really basic BOM metadata. What it does NOT do is recalculate bom entry data. This should be
    called before this function with recalculatepartdata(bomname=d['bomname']) or similar.

    Current BOM meta has the format:
    name text, active text, itemcount text, created text, modified text, notes text

    This entry should be created when the BOM is created, and modified when it is modified
    '''

    allcurrentbommeta = dblib.readalldbrows(database, 'metadata')

    bomtabledata = []
    bomtablenames = dblib.gettablenames(database)
    for tablename in bomtablenames:
        if tablename == 'metadata':
            continue

        bommeta={}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentbommeta in allcurrentbommeta:
            if 'name' in currentbommeta:
                if currentbommeta['name'] == tablename:
                    bommeta = currentbommeta

        # initialize if not found
        if not bommeta:
            bommeta = {}
            for item, value in zip(tableitems.bommetaitems, tableitems.bommetadefaultvalues):
                bommeta[item] = value

            # Then insert name to default dictionary
            bommeta['name'] = tablename

        # Get metadata for each table
        itemcount = dblib.gettablesize(database, tablename)
        bommeta['itemcount'] = itemcount

        # Calc some other data
        bomitems = dblib.readalldbrows(database, tablename)
        cost = 0
        price = 0
        for item in bomitems:
            if item['totalcost']:
                cost += float(item['totalcost'])
            if item['totalprice']:
                price += float(item['totalprice'])

        bommeta['price'] = price
        bommeta['cost'] = cost
        bommeta['profit'] = price-cost

        bomtabledata.append(bommeta)

    if bomtabledata:
        dblib.dropcreatetexttablefromdict(database, 'metadata', bomtabledata)
    else:
        dblib.sqlitedeleteallrecords(database, 'metadata')


# We can feed this either a BOMname or a raw BOM dict array
def calcbomprice(d, output={'message':''}, recalc=True):

    from iiutilities import dblib

    # Use the already written recalc routine here
    if recalc and 'bomname' in d:
        # This will reload all margin data and do multipliers, so no need to
        # futz with multiplication elsewhere
        recalcpartdata(**{'bomname': d['bomname']})

    bomresults = {'cost':0, 'price': 0}
    if 'bomdictarray' in d:
        # directly calculate bom price
        output['message'] == 'bomdictarray keyword found. '
        pass
    elif 'bomname' in d:
        output['message'] += 'bomname keyword found. '
        bomdictarray = dblib.readalldbrows(sysvars.dirs.dbs.boms, d['bomname'])

    else:
        return None

    calcvalues = {}
    calcdicts = dblib.readalldbrows(sysvars.dirs.dbs.system, 'calcs')
    for calcdict in calcdicts:
        calcvalues[calcdict['item']] = calcdict['value']
        bomresults[calcdict['item']] = calcdict['value']

    #dblib.getsinglevalue(sysvars.dirs.dbs.stock, '', )

    totalcost = 0
    totalprice = 0
    for bomitem in bomdictarray:

        # Use existing results to calculate totalprice, totalcost, and
        # Prices for each part category

        # If cost, margin, etc. are not found, retrieve them from stockpartdata. This will allow us to
        # feed a BOM dict array in and get answers out.

        # qtymultiplier = bomitem['qty'] / stockitem['priceqty']
        # itemcost = bomitem['totalcost']
        try:
            itemcost = float(bomitem['totalcost'])
        except:
            itemcost = 0

        bomresults['cost'] += itemcost

        itemtype = bomitem['type']

        if itemtype + 'cost' not in bomresults:
            bomresults[itemtype + 'cost'] = 0

        bomresults[itemtype + 'cost'] += itemcost
        totalcost += itemcost

        if itemtype + 'margin' in bomresults:
            margin = float(calcvalues[itemtype + 'margin'])
            bomresults[itemtype + 'margin'] = margin

        if itemtype + 'price' not in bomresults:
            bomresults[itemtype + 'price'] = 0

        itemprice = float(bomitem['totalprice'])

        bomresults[itemtype + 'price'] += itemprice
        bomresults[itemtype + 'profit'] = bomresults[itemtype + 'price'] - bomresults[itemtype + 'cost']

        bomresults['price'] += itemprice

        totalprice += itemprice

    bomresults['totalcost'] = totalcost
    bomresults['totalprice'] = totalprice
    bomresults['totalprofit'] = totalprice - totalcost
    bomresults['totalmargin'] = totalprice / totalcost - 1
    bomresults['totalmarginjustparts'] = totalprice / bomresults['partscost'] - 1

    output['data'] = bomresults
    return output


def deletepartsfrombom(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    database = sysvars.dirs.dbs.boms

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partids' in d and 'bomname' in d:
        if not isinstance(d['partids'],list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or bomname found in copy request dictionary. '
        return output

    output['message'] += 'Bomname ' + d['bomname']
    output['message'] += 'Partids: '  + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['bomname'],"partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Recalc bom
    recalcpartdata(bomname=d['bomname'])
    makebommetadata()

    # Update metadata
    condition = "name='"+ d['bomname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)


    return output


def deleteboms(d, output={'message':''}):

    from iiutilities import dblib

    if 'bomname' in d:
        output['message'] += 'Single bomname found. '
        bomnames = [d['bomname']]
    elif 'bomnames' in d:
        output['message'] += 'Bomnames keyword found. '
        if not d['bomnames']:
            output['message'] += 'Empty bomnames value. '
            return output
        else:
            bomnames = d['bomnames']

    for bomname in bomnames:
        output['message'] += 'Deleting bom with name' + bomname + '. '
        dblib.sqlitedroptable(sysvars.dirs.dbs.boms, bomname)

    return output


def copybom(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    database = sysvars.dirs.dbs.boms

    if 'bomname' in d:
        pass
    else:
        output['message'] += 'No bomname found in copy request dictionary. '
        return output

    bomnames = dblib.gettablenames(database)
    try:
        bomnames.index(d['bomname'])
    except:
        output['message'] += 'Bomname ' + d['bomname'] + ' not found in list of tables. '
        return output
    else:
        if 'newbomname' in d:
            newbomname = d['newbomname']
        else:
            newbomname = d['bomname'] + '_copy'

        try:
            dblib.sqliteduplicatetable(database, d['bomname'], newbomname)
        except:
            output['message'] += "Error copying BOM. "
        else:
            output['message'] += 'BOM copy appears to have been successful. '

    # Make a new bommeta entry so we can edit it
    makebommetadata()

    # Update metadata
    condition = "name='"+ d['bomname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modifieddata', datalib.gettimestring(), condition)

    return output


def addeditbom(d, output={'message': ''}):

    from iiutilities import dblib, datalib
    database = sysvars.dirs.dbs.boms

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'name' not in d['bomdata']:
        output['message'] += 'No bomname found in edit request dictionary. '
        return output

    # If we are modifying the partid of an existing part, we will first update the old part to have the new partid.
    # Then we will grab it as if it always had that partid.
    if 'originalname' in d['bomdata']:
        output['message'] += 'Found original bomname. '
        if d['bomdata']['originalname'] != '' and d['bomdata']['originalname'] != d['bomdata']['name']:

            output['message'] += 'Found original bomname. Moving ' + d['bomdata']['originalname'] + ' to ' + d['bomdata']['name'] + ". "
            dblib.sqlitemovetable(database, d['bomdata']['originalname'], d['bomdata']['name'])

            # Now instead of autocreating the metadata, which would lose the existing fields, we are going to move the
            # metadata entry as well, then edit it and autocreate. All information should be retained.

            output['message'] += 'Updating metadata entry. '
            dblib.setsinglevalue(database, 'metadata', 'name', d['bomdata']['name'], "name='" + d['bomdata']['originalname'] + "'")
        else:
            output['message'] += 'Original bomname is same as new bomname. '

    # Pull the bom metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    # First we try to pull it. If it does not exist, we have to create it and then recreate the metadata table
    bomnames = dblib.gettablenames(database)
    bomnames.remove('metadata')
    bomnames.sort()
    mostrecentbomname = bomnames[-1]

    # print(d['bomdata']['name'])
    # print(bomnames)
    if d['bomdata']['name'] not in bomnames:
        output['message'] += 'BOM does not exist. Creating. '

        # We are going to copy the most recent BOM and rename.
        # This is lazy but ensures the most recent structure is used.

        dblib.sqliteduplicatetable(database, mostrecentbomname, d['bomdata']['name'])

        # Now we clean out the table
        dblib.sqlitedeleteallrecords(database, d['bomdata']['name'])

        # And make a new metadata entry
        makebommetadata(database)

        # Now update with creation data
        condition = "name='"+ d['bomdata']['name'] + "'"
        dblib.setsinglevalue(database, 'metadata', 'creationdata', datalib.gettimestring(), condition)

    else:
        output['message'] += 'Bom appears to exist. Continuing to edit. '

    # Now we revise the existing entry
    allowedkeywords = ['notes', 'status']

    for keyword in allowedkeywords:
        # mangledkeyword = 'bomdata[' + keyword + ']'
        modified = False
        if keyword in d['bomdata']:
            modified = True
            condition = "name='"+ d['bomdata']['name'] + "'"
            output['message'] += 'keyword ' + keyword + ' found with value: ' + d['bomdata'][keyword] + '. Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, d['bomdata'][keyword], condition)

        if modified:
            dblib.setsinglevalue(database, 'metadata', 'modifieddata', datalib.gettimestring(), condition)

    return output


"""
Assembly Functions

    Assemblies are essentially identical to BOMs. They have additional status fields: reserved and executed

"""


def makeassemblymetadata(database=sysvars.dirs.dbs.assemblies):
    from iiutilities import dblib

    '''

    This recalculates really basic Assembly metadata. What it does NOT do is recalculate bom entry data. This should be
    called before this function with recalculatepartdata(assemblyname=d['assemblyname']) or similar.

    Current Assembly meta has the format:
    name text, active text, itemcount text, created text, modified text, notes text

    This entry should be created when the Assembly is created, and modified when it is modified
    '''

    allcurrentassemblymeta = dblib.readalldbrows(database, 'metadata')

    assemblytabledata = []
    assemblytablenames = dblib.gettablenames(database)
    for tablename in assemblytablenames:
        if tablename == 'metadata':
            continue

        assemblymeta={}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentassemblymeta in allcurrentassemblymeta:
            if 'name' in currentassemblymeta:
                if currentassemblymeta['name'] == tablename:
                    assemblymeta = currentassemblymeta

        # initialize if not found
        if not assemblymeta:
            assemblymeta = {}
            for item, value in zip(tableitems.assemblymetaitems, tableitems.assemblymetadefaultvalues):
                assemblymeta[item] = value

            # Then insert name to default dictionary
            assemblymeta['name'] = tablename
            print("hey i created this new assemblymeta")
            print(assemblymeta)

        # Get metadata for each table
        itemcount = dblib.gettablesize(database, tablename)
        assemblymeta['itemcount'] = itemcount

        # Calc some other data
        assemblyitems = dblib.readalldbrows(database, tablename)
        cost = 0
        price = 0
        for item in assemblyitems:
            if item['totalcost']:
                cost += float(item['totalcost'])
            if item['totalprice']:
                price += float(item['totalprice'])

        assemblymeta['price'] = price
        assemblymeta['cost'] = cost
        assemblymeta['profit'] = price-cost

        if assemblymeta['executed']:
            assemblymeta['orderstatus'] = 'executed'
        elif assemblymeta['reserved']:
            assemblymeta['orderstatus'] = 'reserved'
        else:
            assemblymeta['orderstatus'] = 'draft'

        assemblytabledata.append(assemblymeta)

    if assemblytabledata:
        dblib.dropcreatetexttablefromdict(database, 'metadata', assemblytabledata)
    else:
        dblib.sqlitedeleteallrecords(database, 'metadata')


# We can feed this either a Assemblyname or a raw Assembly dict array
def calcassemblyprice(d, output={'message':''}, recalc=True):

    from iiutilities import dblib

    # Use the already written recalc routine here
    if recalc and 'assemblyname' in d:
        # This will reload all margin data and do multipliers, so no need to
        # futz with multiplication elsewhere
        recalcpartdata(**{'assemblyname': d['assemblyname']})

    assemblyresults = {'cost':0, 'price': 0}
    if 'assemblydictarray' in d:
        # directly calculate assembly price
        output['message'] == 'assemblydictarray keyword found. '
        pass
    elif 'assemblyname' in d:
        output['message'] += 'assemblyname keyword found. '
        assemblydictarray = dblib.readalldbrows(sysvars.dirs.dbs.assemblys, d['assemblyname'])

    else:
        return None

    calcvalues = {}
    calcdicts = dblib.readalldbrows(sysvars.dirs.dbs.system, 'calcs')
    for calcdict in calcdicts:
        calcvalues[calcdict['item']] = calcdict['value']
        assemblyresults[calcdict['item']] = calcdict['value']

    #dblib.getsinglevalue(sysvars.dirs.dbs.stock, '', )

    totalcost = 0
    totalprice = 0
    for assemblyitem in assemblydictarray:

        # Use existing results to calculate totalprice, totalcost, and
        # Prices for each part category

        # If cost, margin, etc. are not found, retrieve them from stockpartdata. This will allow us to
        # feed a Assembly dict array in and get answers out.

        # qtymultiplier = assemblyitem['qty'] / stockitem['priceqty']
        # itemcost = assemblyitem['totalcost']
        try:
            itemcost = float(assemblyitem['totalcost'])
        except:
            itemcost = 0

        assemblyresults['cost'] += itemcost

        itemtype = assemblyitem['type']

        if itemtype + 'cost' not in assemblyresults:
            assemblyresults[itemtype + 'cost'] = 0

        assemblyresults[itemtype + 'cost'] += itemcost
        totalcost += itemcost

        if itemtype + 'margin' in assemblyresults:
            margin = float(calcvalues[itemtype + 'margin'])
            assemblyresults[itemtype + 'margin'] = margin

        if itemtype + 'price' not in assemblyresults:
            assemblyresults[itemtype + 'price'] = 0

        itemprice = float(assemblyitem['totalprice'])

        assemblyresults[itemtype + 'price'] += itemprice
        assemblyresults[itemtype + 'profit'] = assemblyresults[itemtype + 'price'] - assemblyresults[itemtype + 'cost']

        assemblyresults['price'] += itemprice

        totalprice += itemprice

    assemblyresults['totalcost'] = totalcost
    assemblyresults['totalprice'] = totalprice
    assemblyresults['totalprofit'] = totalprice - totalcost
    assemblyresults['totalmargin'] = totalprice / totalcost - 1
    assemblyresults['totalmarginjustparts'] = totalprice / assemblyresults['partscost'] - 1

    output['data'] = assemblyresults
    return output


def deletepartsfromassembly(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    database = sysvars.dirs.dbs.assemblies

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partids' in d and 'assemblyname' in d:
        if not isinstance(d['partids'],list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or assemblyname found in copy request dictionary. '
        return output

    output['message'] += 'Bomname ' + d['assemblyname']
    output['message'] += 'Partids: '  + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['assemblyname'],"partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Recalc assembly
    recalcpartdata(assemblyname=d['assemblyname'])
    makeassemblymetadata()

    # Update metadata
    condition = "name='"+ d['assemblyname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)


    return output


def deleteassemblies(d, output={'message':''}):

    from iiutilities import dblib

    if 'assemblyname' in d:
        output['message'] += 'Single assemblyname found. '
        assemblynames = [d['assemblyname']]
    elif 'assemblynames' in d:
        output['message'] += 'Bomnames keyword found. '
        if not d['assemblynames']:
            output['message'] += 'Empty assemblynames value. '
            return output
        else:
            assemblynames = d['assemblynames']

    for assemblyname in assemblynames:
        output['message'] += 'Deleting assembly with name' + assemblyname + '. '
        dblib.sqlitedroptable(sysvars.dirs.dbs.assemblies, assemblyname)

    return output


def copyassembly(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    database = sysvars.dirs.dbs.assemblies

    if 'assemblyname' in d:
        pass
    else:
        output['message'] += 'No assemblyname found in copy request dictionary. '
        return output

    assemblynames = dblib.gettablenames(database)
    try:
        assemblynames.index(d['assemblyname'])
    except:
        output['message'] += 'Bomname ' + d['assemblyname'] + ' not found in list of tables. '
        return output
    else:
        if 'newassemblyname' in d:
            newassemblyname = d['newassemblyname']
        else:
            newassemblyname = d['assemblyname'] + '_copy'

        try:
            dblib.sqliteduplicatetable(database, d['assemblyname'], newassemblyname)
        except:
            output['message'] += "Error copying Assembly. "
        else:
            output['message'] += 'Assembly copy appears to have been successful. '

    # Make a new assemblymeta entry so we can edit it
    makeassemblymetadata()

    # Update metadata
    condition = "name='"+ d['assemblyname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modifieddate', datalib.gettimestring(), condition)

    return output


def copybomintoassembly(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    bomsdatabase = sysvars.dirs.dbs.boms
    assembliesdatabase = sysvars.dirs.dbs.assemblies

    if 'assemblyname' in d:
        output['message'] += 'assemblyname ' + d['assemblyname'] + ' found. '
    else:
        output['message'] += 'No bomname found in copy request dictionary. '
        return output

    if 'bomname' in d:
        output['message'] += 'bomname ' + d['bomname'] + ' found. '
    else:
        output['message'] += 'No bomname found in copy request dictionary. '
        return output

    # Get items and then use our generic insert function
    bomitems = dblib.readalldbrows(bomsdatabase, d['bomname'])
    # try:
    print(bomitems)
    for item in bomitems:
        # This needs to be sped up. Simplest way is to make the function below accept a list of parts.
        # Also, too much error-handling in function below makes it very slow.

        output = addeditpartlist({'assemblyname':d['assemblyname'], 'partdata':item }, output)
    # except:
    #     output['message'] += 'Error inserting part data. '
    # else:
    #     output['message'] += 'Query appears to have been successful. '

    # Update metadata
    condition = "name='"+ d['assemblyname'] + "'"
    dblib.setsinglevalue(assembliesdatabase, 'metadata', 'modifieddate', datalib.gettimestring(), condition)

    return output


def addeditassembly(d, output={'message': ''}):

    from iiutilities import dblib, datalib
    database = sysvars.dirs.dbs.assemblies

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'assemblydata' not in d:
        output['message'] == 'No assemblydata found in delivered dict. '
        return output
    else:
        data = d['assemblydata']

    if 'name' not in data:
        output['message'] += 'No assemblyname found in edit request dictionary. '
        return output

    # If we are modifying the partid of an existing part, we will first update the old part to have the new partid.
    # Then we will grab it as if it always had that partid.
    if 'originalname' in data:
        output['message'] += 'Found original assemblyname. '
        if data['originalname'] != '' and data['originalname'] != data['name']:

            output['message'] += 'Found original assemblyname. Moving ' + data['originalname'] + ' to ' + data['name'] + ". "
            dblib.sqlitemovetable(database, data['originalname'], data['name'])

            # Now instead of autocreating the metadata, which would lose the existing fields, we are going to move the
            # metadata entry as well, then edit it and autocreate. All information should be retained.

            output['message'] += 'Updating metadata entry. '
            dblib.setsinglevalue(database, 'metadata', 'name', data['name'], "name='" + data['originalname'] + "'")
        else:
            output['message'] += 'Original assemblyname is same as new assemblyname. '

    # Pull the assembly metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    # First we try to pull it. If it does not exist, we have to create it and then recreate the metadata table
    assemblynames = dblib.gettablenames(database)
    if 'metadata' in assemblynames:
        assemblynames.remove('metadata')
    assemblynames.sort()

    if assemblynames:
        mostrecentassemblyname = assemblynames[-1]

    # print(data['name'])
    # print(assemblynames)
    if data['name'] not in assemblynames:
        output['message'] += 'Assembly does not exist. Creating. '

        # Create table by type
        dblib.sqlitecreateemptytable(database, data['name'], tableitems.assemblypartproperties, tableitems.assemblyparttypes, tableitems.assemblypartoptions)

        # And make a new metadata entry
        makeassemblymetadata(database)

        # Now update with creation data
        condition = "name='"+ data['name'] + "'"
        dblib.setsinglevalue(database, 'metadata', 'creationdata', datalib.gettimestring(), condition)

    else:
        output['message'] += 'assembly appears to exist. Continuing to edit. '

    # Now we revise the existing entry
    allowedkeywords = ['notes', 'status', 'reserved', 'executed']

    for keyword in allowedkeywords:
        # mangledkeyword = 'assemblydata[' + keyword + ']'
        modified = False
        if keyword in data:
            modified = True
            condition = "name='"+ data['name'] + "'"
            output['message'] += 'keyword "' + keyword + '" found with value: "' + data[keyword] + '". Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

        if modified:
            dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


"""
Orders

Orders are quite similar to BOMs. The create function will be the same, essentially.
The metadata \table will be a bit different. It will contain :

<< see t ableitems at top >>

"""


def recalcorder(ordername, database=sysvars.dirs.dbs.orders):
    from iiutilities import dblib
    table = dblib.readalldbrows(database, ordername)
    if not table:
        return

    newitems = []
    for item in table:
        # Items we want to update

        # Update total cost on stock and onorder qty
        try:
            item['totalcost'] = float(item['qty']) * float(item['cost']) / float(item['costqty'])
        except:
            pass

        newitems.append(item)

    dblib.insertstringdicttablelist(database, ordername, newitems, droptable=True)


def makeordermetadata(database=sysvars.dirs.dbs.orders, **kwargs):
    from iiutilities import dblib

    '''
    Current Order meta has the format:
    << see tableitems.ordermetaitems >>

    This entry should be created when the BOM is created, and modified when the BOM is modified
    '''

    allcurrentmeta = dblib.readalldbrows(database, 'metadata')
    defaultmetaitems = tableitems.ordermetaitems
    defaultmetavalues = tableitems.ordermetadefaultvalues

    tabledata = []
    tablenames = dblib.gettablenames(database)
    for tablename in tablenames:
        if tablename == 'metadata':
            continue

        meta={}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentmeta in allcurrentmeta:
            if 'name' in currentmeta:
                if currentmeta['name'] == tablename:
                    meta = currentmeta

        # initialize if not found
        if not meta:
            # Create from default values
            meta = {}
            for key, value in zip(defaultmetaitems, defaultmetavalues):
                meta[key] = value

            # Then insert name to default dictionary
            meta['name'] = tablename

        # Get metadata for each table
        itemcount = dblib.gettablesize(database, tablename)
        meta['itemcount'] = itemcount

        # Calc some other data
        orderitems = dblib.readalldbrows(database, tablename)
        cost = 0

        somethingreceived = False
        somethingnotreceived = False
        for item in orderitems:
            if item['totalcost']:
                cost += float(item['totalcost'])

            if meta['executed']:
                if item['received']:
                    somethingreceived = True
                else:
                    somethingnotreceived = True

                if somethingreceived:
                    if somethingnotreceived:
                        meta['orderstatus'] = 'partial'
                    else:
                        meta['orderstatus'] = 'complete'
                else:
                    meta['orderstatus'] = 'executed'
            else:
                meta['orderstatus'] = 'draft'

            # Need to determine order status. If not executed, is 'draft'.
            # If executed and received, is 'open'
            # If some received, is 'partial'
            # If all received, is 'complete'

        meta['cost'] = cost

        tabledata.append(meta)

    if tabledata:
        dblib.dropcreatetexttablefromdict(database, 'metadata', tabledata)
    else:
        dblib.sqlitedeleteallrecords(database, 'metadata')


def createneworder(d, output={'message':''}):

    from iiutilities import dblib, datalib

    if 'database' in d:
        database = d['database']
    else:
        database = sysvars.dirs.dbs.orders
    existingorders = dblib.gettablenames(database)

    if existingorders:
        try:
            existingorders.remove('metadata')
        except:
            pass
            # metadata was not in there (?!)

    if existingorders:
        existingorders.sort(key=float)
        print(existingorders)
        newordername = int(existingorders[-1])+1
    else:
        newordername=1

    # Create a table with a single entry and then empty it
    emptydict = {}
    for item in tableitems.orderpartproperties:
        emptydict[item] = ''
    dblib.dropcreatetexttablefromdict(database, str(newordername), emptydict)
    dblib.sqlitedeleteallrecords(database, str(newordername))

    if 'partsdictarray' in d:
        dblib.insertstringdicttablelist(database, str(newordername), d['partsdictarray'])

    makeordermetadata(database)

    dblib.setsinglevalue(database, str(newordername), 'created', datalib.gettimestring())

    output['newordername'] = newordername

    return output


def editorder(d, output={'message': ''}):

    from iiutilities import dblib
    database = sysvars.dirs.dbs.orders

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    try:
        data = d['orderdata']
    except:
        output['message'] += 'Error extracting data from message. '
        return output

    if 'name' not in data:
        output['message'] += 'No ordername found in edit request dictionary. '
        return output

    if 'name' not in data:
        output['message'] += 'No order name found in edit request dictionary. '
        return output

    # Orders have a fixed name that is assigned when they are created.
    # Get the list of orders and determine whether or not it exists

    # If it does not exist, we are going to create one. We are not, however, going to create it using the
    # name provided. We will increment name. What this means, practically speaking is that if we sent in anything
    # invalid, a new order would be created. We don't want that, so we'll
    existingorders = dblib.gettablenames(database)

    if data['name'] not in existingorders:
        output['message'] += 'Order does not exist'
        return output

    output['message'] += 'name "' + data['name'] + '" exists in orderdata and order has been found. '
    output['message'] += 'Keys: '
    for key,value in data.iteritems():
        output['message'] += key + ' '

    output['message'] += '. '

    # Pull the metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    allowedkeywords = ['notes', 'status', 'name', 'executed', 'supplier', 'desc']

    for keyword in allowedkeywords:
        if keyword in data:
            condition = "name='"+ data['name'] + "'"
            output['message'] += 'keyword ' + keyword + ' found with value: ' + data[keyword] + '. Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

    return output


def deleteorders(d, output={'message':''}):

    from iiutilities import dblib

    if 'ordername' in d:
        output['message'] += 'Single ordername found. '
        ordernames = [d['ordername']]
    elif 'ordernames' in d:
        output['message'] += 'ordernames keyword found. '
        if not d['ordernames']:
            output['message'] += 'Empty ordernames value. '
            return output
        else:
            ordernames = d['ordernames']

    for ordername in ordernames:
        output['message'] += 'Deleting order with name' + ordername + '. '
        dblib.sqlitedroptable(sysvars.dirs.dbs.orders, ordername)

    return output


def deletepartsfromorder(d, output={'message': ''}):

    from iiutilities import dblib, datalib

    database = sysvars.dirs.dbs.orders

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partids' in d and 'ordername' in d:
        if not isinstance(d['partids'],list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or ordername found in copy request dictionary. '
        return output

    output['message'] += 'ordername ' + d['ordername']
    output['message'] += 'Partids: '  + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['ordername'],"partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)


    # Update metadata
    condition = "name='"+ d['ordername'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output
