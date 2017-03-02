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
from iiutilities import dblib

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

sysvars.dirs.webroot = '/var/www/html/inventory/'
sysvars.dirs.datadir = sysvars.dirs.webroot + 'data/'

sysvars.dirs.defaultdataroot = sysvars.dirs.datadir + 'iiinventory/'

sysvars.dirs.dataroot = sysvars.dirs.defaultdataroot

sysvars.dirs.download = sysvars.dirs.dataroot + 'download/'

sysvars.dirs.dbs.system = sysvars.dirs.dataroot + 'system.db'
sysvars.dirs.dbs.stock = sysvars.dirs.dataroot + 'stock.db'
sysvars.dirs.dbs.boms = sysvars.dirs.dataroot + 'boms.db'
sysvars.dirs.dbs.inventories = sysvars.dirs.dataroot + 'inventories.db'
sysvars.dirs.dbs.orders = sysvars.dirs.dataroot + 'orders.db'
sysvars.dirs.dbs.quotes = sysvars.dirs.dataroot + 'quotes.db'
sysvars.dirs.dbs.assemblies = sysvars.dirs.dataroot + 'assemblies.db'

tableitems = utility.Bunch()

tableitems.stockpart_schema = dblib.sqliteTableSchema([
    {'name':'partid', 'primary':True},
    {'name':'description'},
    {'name':'qtystock', 'type':'real'},
    {'name':'qtyonorder', 'type':'real'},
    {'name':'qtyreserved', 'type':'real'},
    {'name':'qtyavailable', 'type':'real'},
    {'name':'cost','type':'real'},
    {'name':'costqty','type':'real'},
    {'name':'costqtyunit','type':'real'},
    {'name':'supplier'},
    {'name':'supplierpart'},
    {'name':'manufacturer'},
    {'name':'manufacturerpart'},
    {'name':'notes'},
    {'name':'partdata'},
    {'name':'datasheet'},
    {'name':'inuse'},
    {'name':'datecreated'},
    {'name':'createdby'},
    {'name':'type'},
    {'name':'minqty', 'type':'real'},
    {'name':'inventory'}
])
tableitems.bompart_schema = dblib.sqliteTableSchema([
    {'name':'partid', 'primary':True},
    {'name':'description'},
    {'name':'qty', 'type':'real'},
    {'name':'qtyunit'},
    {'name':'cost','type':'real'},
    {'name':'price', 'type':'real'},
    {'name':'totalcost', 'type':'real'},
    {'name':'totalprice', 'type':'real'},
    {'name':'costqty', 'type':'real'},
    {'name':'costqtyunit'},
    {'name':'supplier'},
    {'name':'supplierpart'},
    {'name':'manufacturer'},
    {'name':'manufacturerpart'},
    {'name':'notes'},
    {'name':'partdata'},
    {'name':'datasheet'},
    {'name':'type'},
    {'name':'marginmethod'},
    {'name':'margin','type':'real'},
    {'name':'inventory'}
])

tableitems.orderpart_schema = dblib.sqliteTableSchema([
    {'name':'partid', 'primary':True},
    {'name':'description'},
    {'name':'qty', 'type':'real'},
    {'name':'qtyunit'},
    {'name':'cost','type':'real'},
    {'name':'price', 'type':'real'},
    {'name':'totalcost', 'type':'real'},
    {'name':'totalprice', 'type':'real'},
    {'name':'costqty', 'type':'real'},
    {'name':'costqtyunit'},
    {'name':'supplier'},
    {'name':'supplierpart'},
    {'name':'manufacturer'},
    {'name':'manufacturerpart'},
    {'name':'notes'},
    {'name':'partdata'},
    {'name':'datasheet'},
    {'name':'type'},
    {'name':'marginmethod'},
    {'name':'margin','type':'real'},
    {'name':'inventory'},
    {'name':'received'}
])
tableitems.inventorypart_schema = dblib.sqliteTableSchema([
    {'name':'partid', 'primary':True},
    {'name':'qtystock','type':'real'}
])
tableitems.assemblypart_schema = dblib.sqliteTableSchema([
    {'name':'partid', 'primary':True},
    {'name':'description'},
    {'name':'qty', 'type':'real'},
    {'name':'qtyunit'},
    {'name':'cost','type':'real'},
    {'name':'price', 'type':'real'},
    {'name':'totalcost', 'type':'real'},
    {'name':'totalprice', 'type':'real'},
    {'name':'costqty', 'type':'real'},
    {'name':'costqtyunit'},
    {'name':'supplier'},
    {'name':'supplierpart'},
    {'name':'manufacturer'},
    {'name':'manufacturerpart'},
    {'name':'notes'},
    {'name':'partdata'},
    {'name':'datasheet'},
    {'name':'type'},
    {'name':'marginmethod'},
    {'name':'margin','type':'real'},
    {'name':'inventory'}
])

tableitems.bommetaitems_schema = dblib.sqliteTableSchema([
    {'name': 'status', 'default':'active'},
    {'name': 'name', 'primary':True},
    {'name': 'cost', 'type':'real'},
    {'name': 'price', 'type':'real'},
    {'name': 'profit', 'type':'real'},
    {'name': 'modified'},
    {'name': 'created'},
    {'name': 'used'},
    {'name': 'notes'},
])

tableitems.ordermetaitems_schema = dblib.sqliteTableSchema([
    {'name': 'status', 'default':'active'},
    {'name': 'orderstatus', 'default':'draft'},
    {'name': 'executed'},
    {'name': 'name', 'primary':True},
    {'name': 'supplier'},
    {'name': 'desc'},
    {'name': 'cost'},
    {'name': 'price'},
    {'name': 'modified'},
    {'name': 'created'},
    {'name': 'used', 'type':'boolean','default':1},
    {'name': 'notes'},
])

tableitems.inventorymetaitems_schema = dblib.sqliteTableSchema([
    {'name': 'status', 'default':'active'},
    {'name': 'executed'},
    {'name': 'reserved'},
    {'name': 'name', 'primary':True},
    {'name': 'desc'},
    {'name': 'modified'},
    {'name': 'created'},
    {'name': 'used'},
    {'name': 'notes'},
    {'name': 'itemcount', 'type':'integer'},
])

tableitems.assemblymetaitems_schema = dblib.sqliteTableSchema([
    {'name':'status', 'default': 'active'},
    {'name':'executed'},
    {'name':'reserved'},
    {'name':'name', 'primary':True},
    {'name':'cost'},
    {'name':'price'},
    {'name':'modified'},
    {'name':'created'},
    {'name':'used'},
    {'name':'notes'},
])


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
        message += 'Pathalias keyword ' + kwargs['pathalias'] + ' found. '
        relpath = dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'pathaliases', 'path',
                                       "alias='" + kwargs['pathalias'] + "'")
        message += 'relpath ' + relpath + ' retrieved. '
        sysvars.dirs.dataroot = '/var/www/html/inventory/data/' + relpath + '/'
        reload = True

    elif 'user' in kwargs:
        # Set path to default for user
        message += 'user: ' + kwargs['user'] + '. '
        usermeta = datalib.parseoptions(
            dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'data', "user='" + kwargs['user'] + "'"))
        message += 'database' + usermeta['database'] + '. '
        relpath = dblib.getsinglevalue(
            dblib.getsinglevalue(sysvars.dirs.dbs.safe, 'pathaliases', 'path', "alias='" + usermeta['database']))
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
                                                                     sysvars.defaultdbalias) + "'" + '. '
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
    # This should be replaced by something OO and more elegant so we edit all dbs in one place.
    friendlynames = ['stockdb', 'bomsdb', 'inventoriesdb', 'ordersdb', 'assembliesdb', 'quotesdb']
    paths = [sysvars.dirs.dbs.stock, sysvars.dirs.dbs.boms, sysvars.dirs.dbs.inventories, sysvars.dirs.dbs.orders,
             sysvars.dirs.dbs.assemblies, sysvars.dirs.dbs.quotes]
    path = None
    if friendlyname in friendlynames:
        path = paths[friendlynames.index(friendlyname)]
    return path


def check_action_auths(action, level):
    action_auths_dict = {
        # 'gettabledata':1, -- Leaving this out means anyone can do it
        'addeditpart':3, 'copypart':3,'deleteparts':3, 'gettrackedpartdata':1,'generateorders':3,
        'editinventory':3,'addinventory':3,'deleteinventories':3,'addeditinventorypart':3,'deletepartsfrominventory':3,

        'editorder':3,'addorder':3,'deleteorders':3,'addeditorderpart':3,'addeditorderparts':3,'deletepartsfromorder':3,

        'copybom':3,'addeditbom':3,'addeditbomparts':3,'getbomcalcs':1,'getquotecalcs':1,'deletepartsfrombom':3,
        'deleteboms':3,

        'copyassembly':3,'copybomintoassembly':3,'addeditassembly':3,'addeditassemblypart':3,'getassemblycalcs':1,
        'deletepartsfromassembly':3,'deleteassemblys':3,

        'deletequotes':3,'copyquotetoboms':3,

        'exportbomtopdf':1,'exportassemblytopdf':1
    }
    # Currently setup to blacklist only. This allows panelbuilder to work
    if action in action_auths_dict:
        level_required = action_auths_dict[action]
    else:
        level_required = 0
    try:
        if int(level) >= level_required:
            authorized = True
        else:
            authorized = False
    except:
        authorized = False

    print('Action ' + action + ', ' + str(level) + ' provided, ' + str(level_required) + ' required : ' + str(authorized))

    return authorized


def add_inventory_user(username, password, **kwargs):
    from iiutilities.utility import insertuser
    from iiutilities import dblib
    insertuser(sysvars.dirs.dbs.safe, username, password, sysvars.salt, **kwargs)

    # grab the first access keyword (if there is one) and create a meta entry
    if 'accesskeywords' in kwargs:
        if kwargs['accesskeywords'].find(',') >= 0:
            accesskeywords = kwargs['accesskeywords'].split(',')
        else:
            accesskeywords = [kwargs['accesskeywords'].strip()]
        default_keyword =accesskeywords[0]
    else:
        default_keyword = ''

    # insert metaentry for user with default pathalias.
    safedb=dblib.sqliteDatabase(sysvars.dirs.dbs.safe)
    safedb.insert('usermeta',{'user':username,'data':'pathalias:' + default_keyword})


def respace_date(datetimein):
    try:
        date = datetimein.split(' ')[0]
        time = datetimein.split(' ')[1]
    except:
        print('error in initial datetime split')
        return datetimein

    split = date.split('-')
    if not len(split) == 3:
        print('malformed date input')
        return datetimein

    # make sure dates are of correct length
    # e.g. fix 1-17-2017 to 01-17-2017
    if len(split[1]) == 1:
        split[1] = '0' + split[1]
    if len(split[2]) == 1:
        split[2] = '0' + split[2]
    dateout = '-'.join(split)
    datetimeout = dateout + ' ' + time

    return datetimeout


def inventory_daemon(stockdatabasepath=sysvars.dirs.dbs.stock, tablename='stock', email_recipient='inventory_manager@interfaceinnovations.org'):

    stockresults = generateordersfromstock(stockdatabasepath, tablename=tablename)

    from iiutilities.utility import gmail
    from iiutilities.datalib import gettimestring
    mail_sender = gmail()
    mail_sender.recipient=email_recipient
    mail_sender.subject = 'Inventory daemon'

    if stockresults['orderitems']:
        mail_sender.subject += ' :: Order of ' + str(len(stockresults['orderitems'])) + ' items required.'
        mail_sender.message = 'Order daemon run at ' + gettimestring() + ': \n\r'
        for orderitem in stockresults['orderitems']:
            mail_sender.message += 'PartID: ' + orderitem['partid'] + ':' + orderitem['description'] + ', Qty: ' + str(orderitem['toorder'])
            mail_sender.message += ', Supplier: ' + orderitem['supplier'] + ' \n\r'
    else:
        mail_sender.subject += ' :: nothing to order'
        mail_sender.message += 'It appears there is nothing needing to be ordered. '

    mail_sender.send()

def bomdatatolist(bomdatadictlist, fields, **kwargs):
    # sort
    if 'sortby' in kwargs:
        if kwargs['sortby'] in bomdatadictlist[0]:
            # print('** sorting by '  + kwargs['sortby'])
            bomdatadictlist = sorted(bomdatadictlist, key=lambda k: k[kwargs['sortby']])
        else:
            print('Cannot sort by key that does not exist in dictionary. Key selected: ' + kwargs['sortby'])
    datalist = []
    for datadict in bomdatadictlist:
        datum=[]
        for field in fields:
            fieldvalue = str(datadict[field])
            if 'charlimit' in kwargs:
                try:
                    charlimit = int(kwargs['charlimit'])
                except:
                    print('invalid charlimit passed to bomdatatolist')
                else:
                    if len(fieldvalue) > charlimit:
                        fieldvalue=fieldvalue[0:kwargs['charlimit'] - 3] + '...'
            datum.append(fieldvalue)
        datalist.append(datum)
    return datalist


def writepanelbomtopdf(**kwargs):

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import ParagraphStyle

    settings = {
            'format':'normal',
            'items':['partid','qty','totalcost','totalprice','description'],
            'sortby':'partid',
            'widths': [0.75*inch, 0.3*inch, 0.5*inch, 0.5*inch, 3*inch],
            'heights': {'header':0.4*inch, 'row':0.25*inch},
            'title':'BOM Autoproduced by panelbuilder. ',
            'bomdata': [
                {'partid':'K001', 'qty':2, 'totalcost':123.12, 'totalprice':123.34, 'description': 'A long description .....'},
                {'partid':'K001', 'qty':2, 'totalcost':123.12, 'totalprice':123.34, 'description':'A long description .....'},
                {'partid':'K001', 'qty':2, 'totalcost':123.12, 'totalprice':123.34, 'description':'A long description .....'},
                {'partid':'K001', 'qty':2, 'totalcost':123.12, 'totalprice':123.34, 'description':'A long description .....'}
            ],
        'outputfile':'/var/www/html/panelbuilder/data/downloads/bomoutput.pdf'
        }

    settings.update(kwargs)

    # container for the 'Flowable' objects
    elements = []

    imageheader=True
    if imageheader:
        from reportlab.platypus import SimpleDocTemplate, Image
        headerimage = Image('/var/www/html/panelbuilder/images/ColorLogo.png', width=125, height=61, hAlign='RIGHT')
        elements.append(headerimage)

    doc = SimpleDocTemplate(settings['outputfile'], pagesize=letter)
    # doc = SimpleDocTemplate(kwargs['outputfile'])


    styNormal = ParagraphStyle('normal')
    styTitle = ParagraphStyle('normal', fontSize=14, spaceBefore=20, spaceAfter=20)
    stySubTitle = ParagraphStyle('normal', fontSize=14, spaceBefore=10, spaceAfter=7)

    styIndent1 = ParagraphStyle('normal', leftIndent=10)

    # Convert the data from a bom to a list
    if settings['format'] == 'picklist':
        widths = [1.2 * inch, 0.3 * inch, 2.5 * inch, 0.6 * inch, 0.6 * inch]
        settings['items'] = ['partid','qty','description','manufacturer','manufacturerpart']
        settings['labels'] = ['partid','qty','desc.','mfr','mfrpart']
        settings['charlimit']=40
    else:
        # default
        widths = [1.25 * inch, 0.4 * inch, 0.6 * inch, 0.6 * inch, 3 * inch]
        settings['items']= ['partid', 'qty', 'totalcost', 'totalprice', 'description']
        settings['labels']= ['partid', 'qty', 'totalcost', 'totalprice', 'description']
        settings['charlimit'] = 50
    bomdatalist = [settings['labels']]

    bomdatalist.extend(bomdatatolist(settings['bomdata'], settings['items'], charlimit=settings['charlimit'], sortby=settings['sortby']))

    elements.append(Paragraph(settings['title'], styTitle))
    if 'totalprice' in settings:
        elements.append(Paragraph('Total BOM Price: ' + str(settings['totalprice']), stySubTitle))


    # example for how to style. Drop this in the Table creation definition
    style = TableStyle(
            [
                ('ALIGN', (1, 1), (2, 2), 'RIGHT'),
                ('VALIGN', (-1, 0), (-1, 0), 'MIDDLE'),
                ('VALIGN', (0, 0), (1, 0), 'TOP'),
            ])
    t = Table(bomdatalist , widths, [0.5*inch].extend((len(bomdatalist)-1)*[0.25*inch]),
            hAlign='LEFT'
            )
    elements.append(t)
    # write the document to disk
    doc.build(elements)


def writepanelquotetopdf(**kwargs):

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from iiutilities.datalib import setprecision

    settings = {
            'widths': [1*inch, 2.5*inch, 0.5*inch, 0.5*inch, 1.5*inch],
            'heights': {'header':0.4*inch, 'row':0.20*inch},
            'title':'Quote auto-generated by panelbuilder. ',
            'price': 123.45999,
            'options': {'option1':
                            {'price':123.34},
                        'option2':
                            {'price':123.34},
                        'option3':
                            {'price':123.34},
                        'option4':
                            {'price':123.34}
                        },
            'description':'Control panel quote generated by panelbuilder.',
            'includes1':'Control web interface (where applicable), commissioning, testing, wiring',
            'includes2':'of included sensors, complete drawings, support',
            'notincludes1':'Travel and expenses for commissioning. Output wiring (available additional).',
            'notincludes2':'See T&C for details',
            'outputfile': '/var/www/html/panelbuilder/data/downloads/bomoutput.pdf',
            'alphabetizeoptions':True
            }

    settings.update(kwargs)

    # container for the 'Flowable' objects
    elements = []

    imageheader=True
    if imageheader:
        from reportlab.platypus import SimpleDocTemplate, Image
        headerimage = Image('/var/www/html/panelbuilder/images/ColorLogo.png', width=125, height=61, hAlign='RIGHT')
        elements.append(headerimage)

    doc = SimpleDocTemplate(settings['outputfile'], pagesize=letter)
    # doc = SimpleDocTemplate(kwargs['outputfile'])


    styNormal = ParagraphStyle('normal')
    styTitle = ParagraphStyle('normal', fontSize=14, spaceBefore=20, spaceAfter=25)

    styIndent1 = ParagraphStyle('normal', leftIndent=10)

    elements.append(Paragraph(settings['title'], styTitle))

    summarytable = [['Description: ', settings['description'], '', '', '']]
    summarytable.append(['Included:', settings['includes1'], '','',''])
    summarytable.append(['', settings['includes2'], '','',''])
    summarytable.append(['Not included:', settings['notincludes1'],'','',''])
    summarytable.append(['', settings['notincludes2'],'','',''])
    summarytable.append(['Price:','','','','$' + str(settings['price'])])
    summarytable.append(['Panel Options:','','','',''])

    # Convert to list for sorting purposes
    optionslist = []
    for optionname, optiondict in settings['options'].iteritems():
        optionslist.append({'name':optionname, 'dict':optiondict})

    if settings['alphabetizeoptions']:
        optionslist = sorted(optionslist, key=lambda k: k['name'])


    for item in optionslist:
        optionname = item['name']
        optiondict = item['dict']
    # for optionname, optiondict in settings['options'].iteritems():
        summarytable.append(['', optionname, '','', ' $' + str(setprecision(optiondict['price'],2))])

    # example for how to style. Drop this in the Table creation definition
    style = TableStyle(
            [
                ('VALIGN', (0, 0), (4, 0), 'TOP'),
                ('ALIGN', (4, 1), (4, len(summarytable)-1), 'RIGHT')
                # ('VALIGN', (0, 0), (1, 0), 'TOP'),
            ])
    # t = Table(bomdatalist ,[1.25*inch, 0.4*inch, 0.6*inch, 0.6*inch, 3*inch], [0.4*inch].extend((len(bomdatalist)-1)*[0.25*inch]),
    #         hAlign='LEFT'
    #         )
    # Set some custom lineheights
    lineheights = len(summarytable)*[0.35*inch]
    lineheights[2] = 0.2*inch
    lineheights[4] = 0.2*inch
    t = Table(summarytable, settings['widths'], lineheights, hAlign='LEFT')
    t.setStyle(style)
    elements.append(t)
    # write the document to disk
    doc.build(elements)


"""
Shared Functions
"""


def recalcitem(item, precision=2):
    from iiutilities.datalib import setprecision
    if all(key in item for key in ['cost', 'totalcost', 'qty', 'costqty']):
        # Fill in blank quantity with zero
        try:
            item['qty'] = float(item['qty'])
        except:
            item['qty'] = 0

        try:
            item['totalcost'] = setprecision(float(item['qty']) * float(item['cost']) / float(item['costqty']), precision)
        except:
            item['totalcost'] = 0
        try:
            item['price'] = setprecision((1 + float(item['margin'])) * float(item['cost']),precision)
        except:
            item['price'] = 0

    if all(key in item for key in ['price', 'totalprice', 'qty', 'costqty']):
        try:
            item['totalprice'] = setprecision((1 + float(item['margin'])) * item['totalcost'],2)
        except:
            item['totalprice'] = 0

    return item


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

    output = {'message': ''}
    if 'output' in kwargs:
        output.update(kwargs['output'])

    from iiutilities import dblib

    if 'stock' in kwargs:
        type = 'stock'
        database = dblib.sqliteDatabase(sysvars.dirs.dbs.stock)
        tableschema = tableitems.stockpart_schema
        tablenames = ['stock']

    elif 'orders' in kwargs or 'ordername' in kwargs:
        database = dblib.sqliteDatabase(sysvars.dirs.dbs.orders)
        tableschema = tableitems.orderpart_schema
        if 'ordername' in kwargs:
            type = 'order'
            tablenames = [str(kwargs['ordername'])]
        elif 'orders' in kwargs:
            type = 'orders'
            if kwargs['orders']:
                # Run array of orders
                tablenames = kwargs['orders']
            else:
                # Run all orders
                tablenames = dblib.gettablenames(database).remove('metadata')

    elif 'bomname' in kwargs or 'boms' in kwargs:
        database = dblib.sqliteDatabase(sysvars.dirs.dbs.boms)
        tableschema = tableitems.bompart_schema
        if 'bomname' in kwargs:
            type = 'bom'
            tablenames = [kwargs['bomname']]
        elif 'boms' in kwargs:
            type = 'boms'
            database = sysvars.dirs.dbs.boms

            if kwargs['boms']:
                # Run array of orders
                tablenames = kwargs['boms']
            else:
                # Run all orders
                # print(database)
                tablenames = database.get_table_names()

                # print(tablenames)
                tablenames.remove('metadata')

    elif 'assemblyname' in kwargs or 'assemblies' in kwargs:
        database = dblib.sqliteDatabase(sysvars.dirs.dbs.assemblies)
        tableschema = tableitems.assemblypart_schema

        if 'assemblyname' in kwargs:
            type = 'assembly'
            tablenames = [kwargs['assemblyname']]

        elif 'assemblies' in kwargs:
            type = 'assemblies'
            if kwargs['assemblies']:
                # Run array of orders
                tablenames = kwargs['assemblies']
            else:
                # Run all orders
                # print(database)
                tablenames = database.get_table_names()
                # print(tablenames)
                tablenames.remove('metadata')

    elif 'partdictarray' in kwargs:

        # NOT YET TESTED OR USED since update to schema
        tableschema = kwargs['schema']

        type = 'partdictarray'

        # Run on partdictarray sent through. Calculates bom cost though, not individual item recalcs
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
                output['message'] += 'bomdictarray keyword received, but no dictarray present. '
                return

        else:
            table = database.read_table(tablename)

        newtable = []
        for item in table:
            # Items we want to update
            # Update number available
            # print(type)

            if type == 'stock':

                try:
                    temp = float(item['qtystock'])
                except:
                    item['qtystock'] = 0

                try:
                    temp = float(item['qtyreserved'])
                except:
                    item['qtyreserved'] = 0

                try:
                    temp = float(item['qtyonorder'])
                except:
                    item['qtyonorder'] = 0

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
                    item['cost'] = 0

                try:
                    temp = float(item['costqty'])
                except:
                    item['costqty'] = 1

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
                    item['marginmethod'] = 'type'

                if item['marginmethod'] == 'type':
                    try:
                        item['margin'] = dblib.getsinglevalue(sysvars.dirs.dbs.system, 'calcs', 'value',
                                                              "item='" + item['type'] + "margin'")
                        try:
                            item['margin'] = float(item['margin'])
                        except:
                            item['margin'] = 0
                    except:
                        item['margin'] = 0
            else:
                item['margin'] = 0
                # print('MARGIN DEFAULT TO ZERO FOR ITEM ', item['partid'])

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

            item = recalcitem(item)

            newtable.append(item)
        # print(len(newtable))
        newtables.append(newtable)

    if type == 'stock':
        # We dont' need to create, do we?
        # database.create_table('stock', tableitems.stockpart_schema, queue=True)
        for item in newtables[0]:
            database.insert('stock', item, queue=True)
        # print(database.queued_queries)
        database.execute_queue()
        # dblib.insertstringdicttablelist(database, 'stock', newtables[0], droptable=False)
    if type in ['order', 'orders', 'bom', 'boms', 'assembly', 'assemblies']:
        for tablename, anewtable in zip(tablenames, newtables):
            # print('TABLENAME')
            # print(tablename)
            # print('TABLE')
            # print(anewtable)
            if len(anewtable) > 0:
                database.create_table(tablename, tableschema, queue=True)
                for tablerow in anewtable:
                    database.insert(tablename, tablerow, queue=True)
                # dblib.insertstringdicttablelist(database, tablename, anewtable, droptable=True)
            else:
                # print('empty table')
                pass

        # print(database.queued_queries)
        # for query in database.queued_queries:
        #     print(query)
            # database.query(query)
        database.execute_queue()
        # print(database.path)

    return {'tables': newtables, 'output': output}


def addeditpartlist(d, output={'message': ''}):
    from iiutilities import dblib, datalib

    """

    TODO: Optimize query structure

    This operates either on partdata OR partsdata list. Still does not optimize to run queries at once. Runs them
    in series. An obvious place for optimization

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

    # Defaults
    settings = {'addqty':False, 'copystock':None}
    settings.update(d)
    stockdbpath = sysvars.dirs.dbs.stock
    ordersdbpath = sysvars.dirs.dbs.orders
    bomsdbpath = sysvars.dirs.dbs.boms
    inventoriesdbpath = sysvars.dirs.dbs.inventories
    assembliesdbpath = sysvars.dirs.dbs.assemblies

    if 'bomname' in settings:
        output['message'] += 'bomname key present. '
        type = 'bom'
        activedbpath = bomsdbpath
        tablekey = 'bomname'
        listpartproperties = tableitems.bompart_schema.columns()

    elif 'ordername' in settings:
        output['message'] += 'ordername key present. '
        type = 'order'
        activedbpath = ordersdbpath
        tablekey = 'ordername'
        listpartproperties = tableitems.orderpart_schema.columns()

    elif 'assemblyname' in settings:
        output['message'] += 'assemblyname key present. '
        type = 'assembly'
        activedbpath = assembliesdbpath
        tablekey = 'assemblyname'
        listpartproperties = tableitems.assemblypart_schema.columns()

    elif 'inventoryname' in settings:
        output['message'] += 'inventoryname key present. '
        type = 'inventory'
        activedbpath = inventoriesdbpath
        tablekey = 'inventoryname'
        listpartproperties = tableitems.inventorypart_schema.columns()

    else:
        output['message'] += 'No suitable keyword present for command. Terminating. '
        return output

    if 'partdata' not in settings and 'partsdata' not in settings:
        output['message'] += 'No partdata or partsdata present in request. Terminating. '
        return output

    # Always operate on a list of parts to speed things up.
    if 'partdata' in settings:
        settings['partsdata'] = [settings['partdata']]

    if 'message' not in output:
        output['message'] = ''

    tablename = str(d[tablekey])

    activedb = dblib.sqliteDatabase(activedbpath)

    # Determine whether or not the part already exists in the BOM
    listparts = activedb.read_table(tablename)

    # This is just columns
    # Eventually this should be more robust and actually enforce types by pragma

    ordercolumns = activedb.get_pragma_names(tablename)

    for index, partdatum in enumerate(settings['partsdata']):
        print(index)
        if settings['copystock'] in ['all', 'missing']:
            # Get the stock part entry for reference and backfill purposes
            try:
                stockpart = dblib.readonedbrow(stockdbpath, 'stock', condition="partid='" + partdatum['partid'] + "'")[0]
            except:
                stockpart = None
                pass
                # print('error in stockpart result')

            # revert to no copystock if we can't find the part
            if not stockpart:
                settings['copystock'] = None
                stockpart = {}
        else:
            stockpart = {}

        """
        We are going to totally rebuild the database if database format changes.

        TODO: Totally fix and unkludge this using new schema.

        We are only going to do
        this, however, if a sample part that exists in the database does not contain all the fields of the new entry
        We do this because there are concurrency issues with recreating simultaneously with, for example multiple
        asynchronous calls. Insert operations are atomic, however, so if we can run insert whenever possible, we will
        do that.
        """

        # Test: (again, this should eventually test pragma and properly form a database using schema)
        inclusive = True
        if ordercolumns:
            for property in listpartproperties:
                if property not in ordercolumns:
                    inclusive = False
                    break

        newparts = []
        thenewpart = {}

        """
        We iterate over every part in the existing database table.
        We make a new part.
        If the part we are modifying matches, matchpart = True and partexists = True

        TODO: OMG FIX THIS UGLY MESS
        """

        partexists = False
        for orderpart in listparts:

            newpart = {'partid': orderpart['partid']}
            matchpart = False
            print('orderpart, partid')
            print(orderpart)
            print(partdatum)
            if orderpart['partid'] == partdatum['partid']:
                output['message'] += 'Part ' + orderpart['partid'] + ' / ' + partdatum['partid'] + ' was found. '
                matchpart = True
                partexists = True

            # If we have a match, copy all data from previous part and stockpart where appropriate
            # depending on backfill options.

            for property in listpartproperties:
                if matchpart:
                    # add qty if requested. otherwise just paste new value
                    if property == 'qty':
                        # print(partdatum['partid'] + ', ' + str(settings['addqty']))
                        if settings['addqty']:
                            # print('partdatum qty ' + str(partdatum['qty'] + ', orderpart qty ' + str(orderpart['qty'])))
                            newpart['qty'] = float(partdatum['qty']) + float(orderpart['qty'])
                        else:
                            newpart['qty'] = partdatum['qty']
                    elif settings['copystock'] == 'all' and property != 'qty':
                        # get all part data from stock entry
                        # except qty, which is special
                        newpart[property] = stockpart[property]
                    else:
                        if property in partdatum:
                            # print('property ' + property + ' found in partdata')
                            # make sure not empty
                            if partdatum[property]:
                                newpart[property] = partdatum[property]
                                continue

                        # Combined elif via continue
                        # Have to protect against properties that are in order and not stock
                        if settings['copystock'] == 'missing' and property in stockpart:
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
            if 'partid' in partdatum:
                output['message'] += 'key partdata[partid] found in d with value ' + partdatum['partid'] + '. '
                newpart = {'partid': partdatum['partid']}

                for property in listpartproperties:
                    if settings['copystock'] == 'all' and property != 'qty':
                        # get all part data from stock entry
                        # except qty, which is special
                        newpart[property] = stockpart[property]
                    else:
                        if property in partdatum:
                            # print('property ' + property + ' found')

                            # make sure not empty
                            if partdatum[property]:
                                newpart[property] = partdatum[property]
                                continue
                            else:
                                # print('property empty.')
                                pass

                        # Have to protect against properties that are in order and not stock
                        # print('input dictionary' )
                        # print(d)
                        if settings['copystock'] == 'missing':
                            # print('at copystock for property ' + property)
                            pass
                        if settings['copystock'] == 'missing' and property in stockpart:
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
            # if partexists:
            #     activedb.insert
            #
            #     dblib.sqlitedeleteitem(activedb, tablename, "partid='" + thenewpart['partid'] + "'")
            # # print('THE NEW NPART')
            # # print(thenewpart)
            try:
                # assumes uniquekey and auto replace
                activedb.insert(tablename, thenewpart)
                # dblib.insertstringdicttablelist(activedb, tablename, [thenewpart], droptable=False)
            except:
                output['message'] += 'Error in query on "' + activedb + '" + and table "' + tablename + '. '
        else:
            output['message'] += 'Structure was not found to be inclusive. rebuilding. '
            dblib.insertstringdicttablelist(activedb, tablename, newparts, droptable=True)

    # Recalculate quantities. Autotyped based on kwargs
    recalcpartdata(**{tablekey: tablename})

    return output


def refreshpartsfromstock(d, output={'message': ''}):
    from iiutilities import dblib

    notouchkeys = ['qty', 'partid']
    if 'bomname' or 'assemblyname' in d:
        if 'bomname' in d:
            output['message'] += 'bomname found. '
            databasepath = sysvars.dirs.dbs.boms
            tablename = d['bomname']
            schema = tableitems.bompart_schema
        elif 'assemblyname' in d:
            output['message'] += 'assemblyname found. '
            databasepath = sysvars.dirs.dbs.assemblies
            tablename = d['assemblyname']
            schema = tableitems.assemblypart_schema

        database = dblib.sqliteDatabase(databasepath)
        stock_database = dblib.sqliteDatabase(sysvars.dirs.dbs.stock)

        if 'partids' in d:
            output['message'] += 'partids found. '
            for partid in d['partids']:
                output['message'] += 'processing ' + partid + '. '
                condition = "partid='" + partid + "'"
                try:
                    stockpart = stock_database.read_table_row('stock', condition=condition)[0]
                except:
                    output['message'] += 'No stock part found for condition ' + condition + '. '
                    return output

                try:
                    entry = database.read_table_row(tablename, condition=condition)[0]
                except:
                    output['message'] += 'No entry found for condition ' + condition + ' in table "' + tablename + '". '
                    return output

                for property in schema.columns():
                    if property not in notouchkeys and property in stockpart:
                        entry[property] = stockpart[property]

                # This takes advantage of partid being unique key. Will automatically replace without
                # needing to delete

                database.insert(tablename, entry)

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
        allowedkeywords = tableitems.stockpart_schema.columns()

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
                output['message'] += 'Found original partid. Updating ' + d['partdata']['originalpartid'] + ' to ' + \
                                     d['partdata']['partid'] + ". "
                dblib.setsinglevalue(sysvars.dirs.dbs.stock, 'stock', 'partid', d['partdata']['partid'],
                                     "partid='" + d['partdata']['originalpartid'] + "'")
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
        for key in d:
            output['message'] += key + ': ' + str(d[key]) + '. '

    return output


def copystockpart(d={'partdata': {'partid': 'P001', 'description': 'testpart'}}, output={'message': ''}):
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
        if not isinstance(d['partids'], list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids found in copy request dictionary. '
        return output

    output['message'] += 'Partids: ' + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery('stock', "partid='" + id + "'"))

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

    inventory_database = dblib.sqliteDatabase(database)

    allcurrentmeta = inventory_database.read_table('metadata')

    tabledata = []
    tablenames = inventory_database.get_table_names()

    if not tablenames:
        print('no inventory tables')
        return

    inventory_database.create_table('metadata', tableitems.inventorymetaitems_schema, queue=True)
    for tablename in tablenames:
        if tablename == 'metadata':
            continue

        meta = {}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentmeta in allcurrentmeta:
            if 'name' in currentmeta:
                if currentmeta['name'] == tablename:
                    meta = currentmeta

        # initialize if not found
        if not meta:
            meta['name'] = tablename

        # Get metadata for each table
        itemcount = dblib.gettablesize(database, tablename)
        meta['itemcount'] = itemcount
        # print(meta)

        inventory_database.insert('metadata', meta, queue=True)

    inventory_database.execute_queue()


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
            output['message'] += 'keyword ' + keyword + ' found with value: ' + data[
                keyword] + '. Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

        if modified:
            dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


def createnewinventory(d, output={'message': ''}):
    from iiutilities import dblib, datalib

    # Going to leave this as items to make it generic. Inventories and orders are the same thing

    if 'database' in d:
        database_path = d['database']
    else:
        database_path = sysvars.dirs.dbs.inventories

    inventory_db = dblib.sqliteDatabase(database_path)

    existingitems = inventory_db.get_table_names()

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
        newitemnumber = int(existingitems[-1]) + 1
    else:
        newitemnumber = 1

    # Create a table with a single entry and then empty it
    emptydict = {}
    for item in tableitems.inventorypart_schema.columns():
        emptydict[item] = ''

    tablename = str(newitemnumber)
    inventory_db.create_table(tablename, tableitems.inventorypart_schema)

    if 'partsdictarray' in d:
        # sort by partid
        from operator import itemgetter
        partsdictarray = sorted(d['partsdictarray'], key=itemgetter('partid'))

        inventory_db.insert(tablename, partsdictarray)
        # dblib.insertstringdicttablelist(database, str(newitemnumber), partsdictarray)

    makeinventorymetadata(inventory_db.path)

    # Set created date in meta
    inventory_db.set_single_value('metadata', 'created', datalib.gettimestring(), condition="name='" + str(newitemnumber) + "'")
    # dblib.setsinglevalue(database, 'metadata', 'created', datalib.gettimestring(), "name='" + str(newitemnumber) + "'")

    output['newitemnumber'] = newitemnumber

    return output


def deleteinventories(d, output={'message': ''}):
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


def calcstockmeta(stockdatabase=sysvars.dirs.dbs.stock):
    from iiutilities import dblib, datalib

    totalstockvalue = 0
    totalstockcost = 0
    stocktuples = dblib.sqlitequery(stockdatabase, 'select partid, totalprice, totalcost from stock')
    items = []
    for stocktuple in stocktuples:
        try:
            totalprice = float(stocktuple[1])
            totalcost = float(stocktuple[2])
        except:
            print(stocktuple[0] + ': error converting value ' + str(stocktuple[1]) + ' or ' + str(stocktuple[2]))
        else:
            # print(stocktuple[0] + ': ' + str(totalprice) + ',' + str(totalcost))
            items.append({'partid':str(stocktuple[0]), 'totalprice':totalprice, 'totalcost':totalcost})
            totalstockvalue += totalprice
            totalstockcost += totalcost

    sorteditems = sorted(items, key=lambda k: k['totalprice'])
    sorteditems.reverse()
    # print(sorteditems)
    print('Total stock price : ' + str(totalstockvalue))
    print('Total stock cost : ' + str(totalstockcost))


def generateandaddorders(stockdatabase=sysvars.dirs.dbs.stock, ordersdatabase=sysvars.dirs.dbs.orders):
    from iiutilities import dblib

    stockgeneratedorders = generateordersfromstock(stockdatabase)['orders']

    # for now, drop all autogenerated orders. We prevent these orders from being dropped by
    # changing the value of the description field.

    autogenorders = dblib.readalldbrows(ordersdatabase, 'metadata', "desc='autogenerated'")
    # print('** autogenerated orders **')
    # print(autogenorders)
    for autogenorder in autogenorders:
        dblib.sqlitedroptable(ordersdatabase, autogenorder['name'])

    makeordermetadata(ordersdatabase)

    neworderdata = []
    for supplier, orderitems in stockgeneratedorders.iteritems():
        # insert metadata entry with supplier
        # print('** supplier')
        # print(supplier)
        # print('** order items')
        # print(orderitems)
        newordername = createneworder({'partsdictarray':orderitems})['newordername']
        # print(newordername)
        neworderdata.append({'name': newordername, 'supplier': supplier})
        recalcpartdata(**{'ordername': newordername})


    makeordermetadata(ordersdatabase)

    # Now take new order data and tag new orders with supplier
    for neworderdatum in neworderdata:

        dblib.setsinglevalue(ordersdatabase, 'metadata', 'supplier', neworderdatum['supplier'],
                             "name='" + neworderdatum['name'] + "'")
        dblib.setsinglevalue(ordersdatabase, 'metadata', 'desc', 'autogenerated',
                             "name='" + neworderdatum['name'] + "'")


def generateordersfromstock(stockdatabase=sysvars.dirs.dbs.stock, tablename='stock'):
    """
    Iterate over items, finding ones where stock is less than min qty.
    Then consolidate by vendor and those without vendor (soon to be limited to known and 'other'
    """
    from iiutilities import dblib
    allstock = dblib.readalldbrows(stockdatabase, tablename)
    orderentries = []
    for stockitem in allstock:
        try:
            qtyavailable = float(stockitem['qtyavailable'])
        except:
            print('error parsing qtyavailable')
            continue
        try:
            minqty = float(stockitem['minqty'])
        except:
            print('Error parsing minqty for item ' + stockitem['partid'] + '. Setting to 0. ')
            minqty = 0

        if qtyavailable < minqty:
            qtytoorder = minqty - qtyavailable
            # print('We need to order ' + str(qtytoorder) + ' of ' + stockitem['partid'])
            orderentry = stockitem.copy()
            orderentry['toorder'] = qtytoorder
            orderentries.append(orderentry)

    # Now put together order
    suppliers = []
    orders = {}
    othersuppliers = ['other','Other','']

    for orderentry in orderentries:
        if orderentry['supplier'] in othersuppliers:
            orderentry['supplier'] = 'other'

        partorderentry = {}
        for orderpartproperty in tableitems.orderpart_schema.columns():
            if orderpartproperty in orderentry:
                partorderentry[orderpartproperty] = orderentry[orderpartproperty]
            else:
                partorderentry[orderpartproperty] = ''

        partorderentry['qty'] = orderentry['toorder']

        if orderentry['supplier'] in suppliers:
            orders[orderentry['supplier']].append(partorderentry)
        else:
            orders[orderentry['supplier']] = [partorderentry]
            suppliers.append(orderentry['supplier'])

    return {'orderitems':orderentries, 'orders':orders}


def calcstockfromall(inventoriesdatabase=sysvars.dirs.dbs.inventories,
                     stockdatabase=sysvars.dirs.dbs.stock, ordersdatabase=sysvars.dirs.dbs.orders,
                     assembliesdatabase=sysvars.dirs.dbs.assemblies, output=None, **kwargs):

    """
    This does the unholy task of trawling through the inventories, orders, and assemblies to create a current
    inventory.

    Track part. We need a way to track why an inventory item is being incremented/decremented. This is for debug
        and also for visualization. We are going to add a 'trackpart' option to the stock recalc

    """

    if not output:
        output = {'message':''}
    elif 'message' not in output:
        output['message'] = ''

    trackpartenabled = False
    if 'trackpart' in kwargs:
        if kwargs['trackpart']:
            trackpartenabled = True
            print('tracking part ' + kwargs['trackpart'])
            trackedpart = {'partid':kwargs['trackpart'], 'history':[]}


    from iiutilities import dblib, datalib
    inventorytablenames = dblib.gettablenames(inventoriesdatabase)
    orderstablenames = dblib.gettablenames(ordersdatabase)
    assembliestablenames = dblib.gettablenames(assembliesdatabase)

    allitems = []

    """
    Get list of items to handle in inventory. By whitelisting, this means that if an item does not already exist in
    stock and is listed as having a valid inventory type (here, 'std'), it will be ignored
    """

    # We need a generic function for this.

    stock_database = dblib.sqliteDatabase(stockdatabase)

    partinventorytuples = stock_database.get_tuples('stock',['partid','inventory'])
    # dblib.sqlitequery(stockdatabase, 'select partid,inventory from stock')['data']

    inventoryparts = []
    for tuple in partinventorytuples:
        if tuple[1] in ['std']:
            inventoryparts.append(tuple[0])


    """
    Iterate over inventories. Take our list of tablenames, ignore metadata, grab meta, and determine which are executed
    and should be included.

    We create a list of summary items with type of 'inventory' to indicate they reflect an absolute value. We include
    the date to appropriately sort later.

    We tag with origin to make tracking easy later.
    """
    inventorytablenames.sort()
    for inventorytablename in inventorytablenames:

        # Date is in metadata table
        if inventorytablename == 'metadata':
            continue

        # print(inventorytable)

        try:
            metaentry = dblib.readonedbrow(inventoriesdatabase, 'metadata', condition="name='" + inventorytablename + "'")[
                0]
        except:
            # print('NO METAENTRY. OOPS')
            pass
        else:
            # inventory has been executed and should be reviewed
            if metaentry['executed']:
                # print('executed')
                inventoryitems = dblib.readalldbrows(inventoriesdatabase, inventorytablename)

                for inventoryitem in inventoryitems:
                    # print('received: ' + inventoryitem['partid'])
                    summaryitem = {'date': respace_date(metaentry['executed']), 'partid': inventoryitem['partid'],
                                   'qtystock': inventoryitem['qtystock'], 'mode': 'inventory', 'origin':inventorytablename,
                                    'type':'inventory'}
                    allitems.append(summaryitem)

    """
    Orders.

    Same as above with inventories, but this time our summary item has a mode of 'change' instead of 'inventory'.
    """

    print('** Orders')
    orderstablenames.sort()
    for orderstablename in orderstablenames:
        # Date is in metadata table
        if orderstablename == 'metadata':
            continue

        # print(orderstable)

        try:
            metaentry = dblib.readonedbrow(ordersdatabase, 'metadata', condition="name='" + orderstablename + "'")[0]
        except:
            pass
            # print('NO METAENTRY. OOPS')
        else:
            # order has been executed and should be reviewed
            if metaentry['executed']:
                # print('executed')
                # print(metaentry['executed'])
                orderitems = dblib.readalldbrows(ordersdatabase, orderstablename)

                for orderitem in orderitems:
                    if orderitem['received']:
                        # Denote as received into stock
                        # print('received: ' + orderitem['partid'])
                        summaryitem = {'date': respace_date(orderitem['received']), 'partid': orderitem['partid'],
                                       'qtystock': orderitem['qty'], 'mode': 'change', 'type':'order'}
                    else:
                        # Need to grab meta entry executed date
                        # print('on order: ' + orderitem['partid'])
                        summaryitem = {'date': respace_date(metaentry['executed']), 'partid': orderitem['partid'],
                                       'qtyonorder': orderitem['qty'], 'mode': 'change', 'type':'order'}

                    summaryitem['origin'] = orderstablename
                    allitems.append(summaryitem)

    """
    Assemblies

    Same as above with orders, but we take the things away.
    """

    # print('** Assemblies')
    assembliestablenames.sort()
    for assembliestablename in assembliestablenames:
        # Date is in metadata table
        if assembliestablename == 'metadata':
            continue

        try:
            metaentry = dblib.readonedbrow(assembliesdatabase, 'metadata', condition="name='" + assembliestablename + "'")[
                0]
        except:
            pass
            # print('NO METAENTRY. OOPS')
        else:
            # order has been executed and should be reviewed
            if metaentry['executed']:
                # print('executed')
                orderitems = dblib.readalldbrows(assembliesdatabase, assembliestablename)

                for orderitem in orderitems:
                    # Denote as taking out of stock
                    # print('executed: ' + orderitem['partid'])
                    summaryitem = {'date': respace_date(metaentry['executed']), 'partid': orderitem['partid'],
                                   'qtystock': -1 * float(orderitem['qty']), 'mode': 'change',
                                   'origin':assembliestablename, 'type':'assembly'}
                    allitems.append(summaryitem)
            elif metaentry['reserved']:
                # print('reserved')
                orderitems = dblib.readalldbrows(assembliesdatabase, assembliestablename)

                for orderitem in orderitems:
                    # Denote as taking out of stock
                    # print('reserved: ' + orderitem['partid'])
                    summaryitem = {'date': respace_date(metaentry['reserved']), 'partid': orderitem['partid'],
                                   'qtyreserved': orderitem['qty'], 'mode': 'change',
                                   'origin':assembliestablename, 'type':'assembly'}
                    allitems.append(summaryitem)

    # print(allitems)
    """
    Now iterate over all items to create a comprehensive stock
    First sort by date
    """
    from operator import itemgetter

    # need to add a fixer for date, since they are ot getting spaced right 100% of the time

    orderedlist = sorted(allitems, key=itemgetter('date'))

    # print(orderedlist)

    newstockparts = []

    # keep an index handy
    newstockpartids = []
    elementtypes = ['qtystock', 'qtyreserved', 'qtyonorder']
    for element in orderedlist:
        if element['partid'] in inventoryparts:
            for elementtype in elementtypes:
                if elementtype in element:
                    if trackpartenabled:
                        if element['partid'] == trackedpart['partid']:
                            trackedpart['history'].append(element)
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
                        newstockparts.append({'partid': element['partid'], elementtype: element[elementtype]})
                        newstockpartids.append(element['partid'])

                    else:
                        if valueexists:
                            if element['mode'] == 'change':
                                # print('changing existing value for part ' + element['partid'])
                                # print('old value: ' + str(newstockparts[existingindex][elementtype]))
                                newstockparts[existingindex][elementtype] = float(
                                    newstockparts[existingindex][elementtype]) + float(element[elementtype])
                                # print('new value: ' + str(newstockparts[existingindex][elementtype]))

                            elif element['mode'] == 'inventory':
                                newstockparts[existingindex][elementtype] = float(element[elementtype])

                        else:
                            # print('value does not exist for part ' + element['partid'])
                            # This will be for adding a new vaue to an existing part, e.g. onorder to a qtystock item
                            # print('part exists but value does not. Setting new value. ')
                            newstockparts[existingindex][elementtype] = element[elementtype]
        else:
            # print(element['partid'] + ' is a non-inventory item.')
            pass

    starttime = datalib.gettimestring()

    # set zero queries. This assumes the part already exists, which could prove problematic.
    stock_database.queue_queries(['update stock set qtyreserved=0'])
    stock_database.queue_queries(['update stock set qtystock=0'])
    stock_database.queue_queries(['update stock set qtyonorder=0'])

    for part in newstockparts:
        if part['partid'] == 'K080':
            print('**')
            print(part)
            print('** ')
        for elementtype in elementtypes:
            if elementtype in part:
                stock_database.set_single_value('stock', elementtype, str(part[elementtype]),
                                                condition="partid='" + part['partid'] + "'", queue=True)

    output['queries'] = stock_database.queued_queries
    stock_database.execute_queue()

    elapsedtime = datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(starttime)
    # print('Elapsed time: ' + str(elapsedtime))
    recalcpartdata(**{'stock': ''})

    if trackpartenabled:
        output['trackedpart'] = trackedpart

    return output


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
        if not isinstance(d['partids'], list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or inventoryname found in copy request dictionary. '
        return output

    output['message'] += 'inventoryname ' + d['inventoryname']
    output['message'] += 'Partids: ' + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['inventoryname'], "partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Update metadata
    condition = "name='" + d['inventoryname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


def importstockfromcsv(filename, database=sysvars.dirs.dbs.stock):
    from iiutilities import datalib, dblib
    if not filename:
        # print('no file selected')
        return None

    # Read csv datamap file
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1,
                                                          keystolowercase=True)

    requiredkeys = ['partid', 'description']
    # iterate over header to make sure key quantities are found
    foundkeys = []
    for itemname in datamapdictarray[0]:
        if itemname in tableitems.stockpart_schema.columns():
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

    # print(str(len(insertarray)) + ' items prepared for insertion from ' + str(len(datamapdictarray)))

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
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1,
                                                          keystolowercase=True)

    if 'partid' in datamapdictarray[0] and 'manufacturerpart' in datamapdictarray[0]:
        print('fields found')
    else:
        return None

    subarray = []
    for dict in datamapdictarray:
        if dict['partid'] and dict['manufacturerpart']:
            subarray.append({'partid': dict['partid'], 'manufacturerpart': dict['manufacturerpart']})

    print(subarray)
    print(database)

    querylist = []
    for sub in subarray:
        condition = "partid='" + sub['partid'] + "'"
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
        condition = "partid='" + sub['partid'] + "'"
        print(condition)
        print(sub['manufacturerpart'])
        query = dblib.makesinglevaluequery('stock', 'supplierpart', sub['manufacturerpart'], condition=condition)
        try:
            dblib.sqlitequery(database, query)
            print(query)
        except:
            print('Error with query:')
            print(query)

    # print('*** BOMS')
    bomnames = dblib.gettablenames(sysvars.dirs.dbs.boms)
    for bomname in bomnames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] + "'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(bomname, 'manufacturerpart', sub['manufacturerpart'],
                                               condition=condition)
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

    # print('*** ASSEMBLIES')
    assemblynames = dblib.gettablenames(sysvars.dirs.dbs.assemblies)
    for assemblyname in assemblynames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] + "'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(assemblyname, 'manufacturerpart', sub['manufacturerpart'],
                                               condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.assemblies, query)
                print(query)
            except:
                print('Error with query:')
                print(query)
            query = dblib.makesinglevaluequery(assemblyname, 'supplierpart', sub['manufacturerpart'],
                                               condition=condition)
            try:
                dblib.sqlitequery(sysvars.dirs.dbs.assemblies, query)
                print(query)
            except:
                print('Error with query:')
                print(query)

    # print('*** ORDERS')
    ordernames = dblib.gettablenames(sysvars.dirs.dbs.orders)
    for ordername in ordernames:
        for sub in subarray:
            condition = "partid='" + sub['partid'] + "'"
            print(condition)
            print(sub['manufacturerpart'])
            query = dblib.makesinglevaluequery(ordername, 'manufacturerpart', sub['manufacturerpart'],
                                               condition=condition)
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
    datamapdictarray = datalib.datawithheaderstodictarray(datalib.delimitedfiletoarray(filename), 1,
                                                          keystolowercase=True)

    requiredkeys = ['partid', 'qtystock']
    # iterate over header to make sure key quantities are found
    foundkeys = []
    for itemname in datamapdictarray[0]:
        if itemname in tableitems.inventorypart_schema.columns():
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

    createnewinventory({'partsdictarray': insertarray})

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

        bommeta = {}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentbommeta in allcurrentbommeta:
            if 'name' in currentbommeta:
                if currentbommeta['name'] == tablename:
                    bommeta = currentbommeta

        # initialize if not found
        if not bommeta:
            bommeta = {}
            for item, value in zip(tableitems.bommetaitems_schema.columns(), tableitems.bommetaitems_schema.defaults()):
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
        if bomitems:
            for item in bomitems:
                if item['totalcost']:
                    # Pick up errors for problems converting float
                    try:
                        cost += float(item['totalcost'])
                    except:
                        pass
                if item['totalprice']:
                    try:
                        price += float(item['totalprice'])
                    except:
                        pass

        bommeta['price'] = price
        bommeta['cost'] = cost
        bommeta['profit'] = price - cost

        bomtabledata.append(bommeta)

    if bomtabledata:
        dblib.dropcreatetexttablefromdict(database, 'metadata', bomtabledata)
    else:
        dblib.sqlitedeleteallrecords(database, 'metadata')


def backfillbomfromstock(bomitems, recalc=True):
    from iiutilities import dblib
    newbomitems = []
    for bomitem in bomitems:
        stockdbresult = dblib.readonedbrow(sysvars.dirs.dbs.stock, 'stock', condition="partid='" + bomitem['partid'] + "'")
        if stockdbresult:
            stockitem = stockdbresult[0]
        else:
            print(' ITEM "' + bomitem['partid'] + '" NOT FOUND ')
            stockitem = {}

        # Backfill all properties that do not exist
        for property in tableitems.bompart_schema.columns():
            if property in stockitem and property not in bomitem:
                bomitem[property] = stockitem[property]

        if recalc:
            recalcitem(bomitem)

        newbomitems.append(bomitem)
    return newbomitems


# We can feed this either a BOMname or a raw BOM dict array
def calcbomprice(d, output={'message': ''}, recalc=True, precision=2):
    from iiutilities import dblib
    from iiutilities.datalib import setprecision

    # Use the already written recalc routine here
    if recalc and 'bomname' in d:
        # This will reload all margin data and do multipliers, so no need to
        # futz with multiplication elsewhere
        recalcpartdata(**{'bomname': d['bomname']})

    bomresults = {'cost': 0, 'price': 0}
    if 'bomdictarray' in d:
        # directly calculate bom price
        output['message'] == 'bomdictarray keyword found. '
        bomdictarray = d['bomdictarray']
        # This will not do any recalc. Below, we will use what we find if we find it, and retrieve what we do not

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


    totalcost = 0
    totalprice = 0
    for bomitem in bomdictarray:

        # Use existing results to calculate totalprice, totalcost, and
        # Prices for each part category

        # If cost, margin, etc. are not found, retrieve them from stockpartdata. This will allow us to
        # feed a BOM dict array in and get answers out even without

        if 'totalcost' not in bomitem:
            # Now we have to recalc

            bomitem = backfillbomfromstock([bomitem])[0]

        try:
            itemcost = float(bomitem['totalcost'])
        except:
            itemcost = 0

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
    try:
        bomresults['totalmargin'] = totalprice / totalcost - 1
    except:
        bomresults['totalmargin'] = 0
    try:
        bomresults['totalmarginjustparts'] = totalprice / bomresults['partscost'] - 1
    except:
        bomresults['totalmargin'] = 0

    for name, value in bomresults.iteritems():
        # print(name,value)
        bomresults[name] = setprecision(value, precision)

    output['data'] = bomresults
    return output


def deletepartsfrombom(d, output={'message': ''}):
    from iiutilities import dblib, datalib

    database = sysvars.dirs.dbs.boms

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'partids' in d and 'bomname' in d:
        if not isinstance(d['partids'], list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or bomname found in copy request dictionary. '
        return output

    output['message'] += 'Bomname ' + d['bomname']
    output['message'] += 'Partids: ' + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['bomname'], "partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Recalc bom
    recalcpartdata(bomname=d['bomname'])
    makebommetadata()

    # Update metadata
    condition = "name='" + d['bomname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


def deleteboms(d, output={'message': ''}):
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
    condition = "name='" + d['bomname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modifieddata', datalib.gettimestring(), condition)

    return output


def addeditbom(d, output={'message': ''}):
    from iiutilities import dblib, datalib
    settings = {'database':sysvars.dirs.dbs.boms}
    settings.update(d)

    boms_database = dblib.sqliteDatabase(settings['database'])

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'name' not in settings['bomdata']:
        output['message'] += 'No bomname found in edit request dictionary. '
        return output

    # If we are modifying the partid of an existing part, we will first update the old part to have the new partid.
    # Then we will grab it as if it always had that partid.
    if 'originalname' in settings['bomdata']:
        output['message'] += 'Found original bomname. '
        if settings['bomdata']['originalname'] != '' and settings['bomdata']['originalname'] != settings['bomdata']['name']:

            output['message'] += 'Found original bomname. Moving ' + settings['bomdata']['originalname'] + ' to ' + \
                                 settings['bomdata']['name'] + ". "

            boms_database.move_table(settings['bomdata']['originalname'], settings['bomdata']['name'])

            # Now instead of autocreating the metadata, which would lose the existing fields, we are going to move the
            # metadata entry as well, then edit it and autocreate. All information should be retained.

            output['message'] += 'Updating metadata entry. '
            dblib.setsinglevalue(settings['database'], 'metadata', 'name', settings['bomdata']['name'],
                                 "name='" + settings['bomdata']['originalname'] + "'")
        else:
            output['message'] += 'Original bomname is same as new bomname. '

    # Pull the bom metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    # First we try to pull it. If it does not exist, we have to create it and then recreate the metadata table
    # TODO: queue all entries where possible to speed up

    bomnames = dblib.gettablenames(settings['database'])
    if 'metadata' in bomnames:
        bomnames.remove('metadata')
    bomnames.sort()
    # mostrecentbomname = bomnames[-1]

    # print(settings['bomdata']['name'])
    # print(bomnames)
    if settings['bomdata']['name'] not in bomnames:
        output['message'] += 'BOM does not exist. Creating. '

        boms_database.create_table(settings['bomdata']['name'], tableitems.bompart_schema)

        # And make a new metadata entry
        print(boms_database.path)
        makebommetadata(boms_database.path)

        # Now update with creation data
        condition = "name='" + settings['bomdata']['name'] + "'"
        boms_database.set_single_value('metadata','creationdate', datalib.gettimestring(), condition)

    else:
        output['message'] += 'Bom appears to exist. Continuing to edit. '

    # Now we revise the existing entry
    allowedkeywords = ['notes', 'status']

    for keyword in allowedkeywords:
        # mangledkeyword = 'bomdata[' + keyword + ']'
        modified = False
        if keyword in settings['bomdata']:
            modified = True
            condition = "name='" + settings['bomdata']['name'] + "'"
            output['message'] += 'keyword ' + keyword + ' found with value: ' + settings['bomdata'][
                keyword] + '. Updating metadata entry with condition:' + condition + '. '
            boms_database.set_single_value('metadata', keyword, settings['bomdata'][keyword], condition)

        if modified:
            boms_database.set_single_value('metadata', 'modifieddata', datalib.gettimestring(), condition)

    return output


"""
Quotes
"""


def deletequotes(d, output={'message': ''}):
    from iiutilities import dblib

    names = []
    if 'name' in d:
        output['message'] += 'Single name found. '
        names = [d['bomname']]
    elif 'names' in d:
        output['message'] += 'names keyword found. '
        if not d['names']:
            output['message'] += 'Empty names value. '
            return output
        else:
            names = d['names']

    for name in names:
        database = sysvars.dirs.dbs.quotes
        output['message'] += 'Deleting quote with name "' + name + '" from db "' + database + '" . '
        dblib.sqlitedroptable(database, name)

    return output


def copyquotetoboms(d, output={'message': ''}):
    from iiutilities import dblib, datalib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    quotesdatabase = sysvars.dirs.dbs.quotes
    bomsdatabase = sysvars.dirs.dbs.boms

    if 'name' in d:
        output['message'] += 'name ' + d['name'] + ' found. '
    else:
        output['message'] += 'No name found in copy request dictionary. '
        return output

    # Get items and then use our generic insert function
    quoteitems = dblib.readalldbrows(quotesdatabase, d['name'])
    # print('** QTY : ' + str(len(quoteitems)))

    # Backfill and create BOM. Drop a table with the same name if it exists
    backfillbomfromstock(quoteitems, recalc=True)

    addeditbom({'bomdata':{'name':d['name']}}, output)

    # for quoteitem in quoteitems:
    addeditpartlist({'bomname':d['name'], 'partsdata':quoteitems, 'copystock':'all'}, output)

    condition = "name='" + d['name'] + "'"
    dblib.setsinglevalue(bomsdatabase, 'metadata', 'modifieddate', datalib.gettimestring(), condition)

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

        assemblymeta = {}
        # Check to see if metadata already exist. We need to maintain activity status and notes
        for currentassemblymeta in allcurrentassemblymeta:
            if 'name' in currentassemblymeta:
                if currentassemblymeta['name'] == tablename:
                    assemblymeta = currentassemblymeta

        # initialize if not found
        if not assemblymeta:
            assemblymeta = {}
            for item, value in zip(tableitems.assemblymetaitems_schema.columns(), tableitems.assemblymetaitems_schema.defaults()):
                assemblymeta[item] = value

            # Then insert name to default dictionary
            assemblymeta['name'] = tablename
            # print("hey i created this new assemblymeta")
            # print(assemblymeta)

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
        assemblymeta['profit'] = price - cost

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
def calcassemblyprice(d, output={'message': ''}, recalc=True):
    from iiutilities import dblib

    # Use the already written recalc routine here
    if recalc and 'assemblyname' in d:
        # This will reload all margin data and do multipliers, so no need to
        # futz with multiplication elsewhere
        recalcpartdata(**{'assemblyname': d['assemblyname']})

    assemblyresults = {'cost': 0, 'price': 0}
    if 'assemblydictarray' in d:
        # directly calculate assembly price
        output['message'] += 'assemblydictarray keyword found. '
        pass
    elif 'assemblyname' in d:
        output['message'] += 'assemblyname keyword found. '
        assemblydictarray = dblib.readalldbrows(sysvars.dirs.dbs.assemblies, d['assemblyname'])

    else:
        return None

    calcvalues = {}
    calcdicts = dblib.readalldbrows(sysvars.dirs.dbs.system, 'calcs')
    for calcdict in calcdicts:
        calcvalues[calcdict['item']] = calcdict['value']
        assemblyresults[calcdict['item']] = calcdict['value']

    # dblib.getsinglevalue(sysvars.dirs.dbs.stock, '', )

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
        if not isinstance(d['partids'], list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or assemblyname found in copy request dictionary. '
        return output

    output['message'] += 'Bomname ' + d['assemblyname']
    output['message'] += 'Partids: ' + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['assemblyname'], "partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Recalc assembly
    recalcpartdata(assemblyname=d['assemblyname'])
    makeassemblymetadata()

    # Update metadata
    condition = "name='" + d['assemblyname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output


def deleteassemblies(d, output={'message': ''}):
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
    condition = "name='" + d['assemblyname'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modifieddate', datalib.gettimestring(), condition)

    return output


def copybomintoassembly(d, output={'message': ''}):
    from iiutilities import dblib, datalib

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    boms_database = dblib.sqliteDatabase(sysvars.dirs.dbs.boms)
    assemblies_database = dblib.sqliteDatabase(sysvars.dirs.dbs.assemblies)
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
    # Except -- we are going to make this additive for multiple units and combinations.

    bomitems = boms_database.read_table(d['bomname'])

    # print(bomitems)
    # Should pass whole dict, but I can't be arsed to error check all of that just yet.
    output = addeditpartlist({'assemblyname': d['assemblyname'], 'addqty':d['addqty'], 'partsdata': bomitems}, output)

    # Update metadata
    condition = "name='" + d['assemblyname'] + "'"
    assemblies_database.set_single_value('metadata', 'modifieddate', datalib.gettimestring(), condition)
    # dblib.setsinglevalue(assembliesdatabase, 'metadata', 'modifieddate', datalib.gettimestring(), condition)

    return output


def addeditassembly(d, output={'message': ''}):
    from iiutilities import dblib, datalib
    assembly_database = dblib.sqliteDatabase(sysvars.dirs.dbs.assemblies)

    # In here we should test to see if the request is valid. First, let us make sure we have all the required
    # fields we need:
    # partid, description, manufacturer, manufacturerpart

    if 'assemblydata' not in d:
        output['message'] = 'No assemblydata found in delivered dict. '
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

            output['message'] += 'Found original assemblyname. Moving ' + data['originalname'] + ' to ' + data[
                'name'] + ". "
            assembly_database.move_table(data['originalname'], data['name'])

            # Now instead of autocreating the metadata, which would lose the existing fields, we are going to move the
            # metadata entry as well, then edit it and autocreate. All information should be retained.

            output['message'] += 'Updating metadata entry. '
            assembly_database.set_single_value('metadata', 'name', data['name'], "name='" + data['originalname'] + "'")
            # dblib.setsinglevalue(database, 'metadata', 'name', data['name'], "name='" + data['originalname'] + "'")
        else:
            output['message'] += 'Original assemblyname is same as new assemblyname. '

    # Pull the assembly metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    # First we try to pull it. If it does not exist, we have to create it and then recreate the metadata table
    assemblynames = assembly_database.get_table_names()
    if 'metadata' in assemblynames:
        assemblynames.remove('metadata')
    assemblynames.sort()

    # print(data['name'])
    # print(assemblynames)
    if data['name'] not in assemblynames:
        output['message'] += 'Assembly does not exist. Creating. '

        # Create table by type
        assembly_database.create_table(data['name'], tableitems.assemblypart_schema)
        # dblib.sqlitecreateemptytable(database, data['name'], tableitems.assemblypart_schema.columns(),
        #                              tableitems.assemblypart.types, tableitems.assemblypart.options)

        # And make a new metadata entry
        makeassemblymetadata(assembly_database.path)

        # Now update with creation data
        condition = "name='" + data['name'] + "'"
        assembly_database.set_single_value('metadata', 'creatiodate', datalib.gettimestring(), condition)
        # dblib.setsinglevalue(database, 'metadata', 'creationdata', datalib.gettimestring(), condition)

    else:
        output['message'] += 'assembly appears to exist. Continuing to edit. '

    # Now we revise the existing entry
    allowedkeywords = ['notes', 'status', 'reserved', 'executed']

    for keyword in allowedkeywords:
        # mangledkeyword = 'assemblydata[' + keyword + ']'
        modified = False
        if keyword in data:
            modified = True
            condition = "name='" + data['name'] + "'"
            output['message'] += 'keyword "' + keyword + '" found with value: "' + data[
                keyword] + '". Updating metadata entry with condition:' + condition + '. '
            assembly_database.set_single_value('metadata', keyword, data[keyword], condition)
            # dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

        if modified:
            assembly_database.set_single_value('metadata', 'modified', datalib.gettimestring(), condition)
            # dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

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
    defaultmetaitems = tableitems.ordermetaitems_schema.columns()
    defaultmetavalues = tableitems.ordermetaitems_schema.defaults()

    tabledata = []
    tablenames = dblib.gettablenames(database)
    for tablename in tablenames:
        if tablename == 'metadata':
            continue

        meta = {}
        # Check to see if metadata already exist. We need to maintain activity status and notes, other things
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


def createneworder(d, output={'message': ''}):
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
        # print(existingorders)
        newordername = int(existingorders[-1]) + 1
    else:
        newordername = 1

    # Create a table with a single entry and then empty it
    emptydict = {}
    for item in tableitems.orderpart_schema.columns():
        emptydict[item] = ''
    dblib.dropcreatetexttablefromdict(database, str(newordername), emptydict)
    dblib.sqlitedeleteallrecords(database, str(newordername))

    if 'partsdictarray' in d:
        dblib.insertstringdicttablelist(database, str(newordername), d['partsdictarray'])

    makeordermetadata(database)

    dblib.setsinglevalue(database, str(newordername), 'created', datalib.gettimestring())

    output['newordername'] = str(newordername)

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
    for key, value in data.iteritems():
        output['message'] += key + ' '

    output['message'] += '. '

    # Pull the metadata entry and begin to update it. We're only updating name (done above) and other editable fields.
    # For the moment this is only the notes and status fields. Everything else is dynamic

    allowedkeywords = ['notes', 'status', 'name', 'executed', 'supplier', 'desc']

    for keyword in allowedkeywords:
        if keyword in data:
            condition = "name='" + data['name'] + "'"
            output['message'] += 'keyword ' + keyword + ' found with value: ' + data[
                keyword] + '. Updating metadata entry with condition:' + condition + '. '
            dblib.setsinglevalue(database, 'metadata', keyword, data[keyword], condition)

    return output


def deleteorders(d, output={'message': ''}):
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
    # print(d['ordernames'])
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
        if not isinstance(d['partids'], list):
            d['partids'] = [d['partids']]
    else:
        output['message'] += 'No partids and/or ordername found in copy request dictionary. '
        return output

    output['message'] += 'ordername ' + d['ordername']
    output['message'] += 'Partids: ' + str(d['partids']) + '. '

    querylist = []
    for id in d['partids']:
        output['message'] += 'Deleting part ' + id + '. '
        querylist.append(dblib.makedeletesinglevaluequery(d['ordername'], "partid='" + id + "'"))

    dblib.sqlitemultquery(database, querylist)

    # Update metadata
    condition = "name='" + d['ordername'] + "'"
    dblib.setsinglevalue(database, 'metadata', 'modified', datalib.gettimestring(), condition)

    return output
