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


"""

Database tools

"""


class sqliteDatabase(object):

    def __init__(self, path):
        # Verify database exists
        self.path = path
        self.queued_queries = []

    def get_table_names(self):
        self.tablenames = gettablenames(self.path)
        return self.tablenames

    def create_table(self, name, schema, queue=False, dropexisting=True):
        if schema.valid:
            if dropexisting:
<<<<<<< HEAD
                self.drop_table(name, queue=queue, quiet=True)
=======
                self.drop_table(name, queue=queue)
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

            query = sqlite_create_table_query_from_schema(name, schema)
            if queue:
                self.queue_queries([query])
            else:
                self.query(query)
        else:
            print('schema is invalid')

<<<<<<< HEAD
    def drop_table(self, name, queue=False, quiet=False):
        if queue:
            self.queue_queries(["drop table '" + name + "'"])
        else:
            sqlitedroptable(self.path, name, quiet)

    def drop_empty_tables(self):
        tablenames = self.get_table_names()
        for tablename in tablenames:
            if self.get_table_size(tablename) == 0:
                self.drop_table(tablename, queue=True)
        if self.queued_queries:
            self.execute_queue()
=======
    def drop_table(self, name, queue=False):
        if queue:
            self.queue_queries(["drop table '" + name + "'"])
        else:
            sqlitedroptable(self.path,name)
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

    def move_table(self, oldname, newname):
        sqlitemovetable(self.path, oldname, newname)

    def migrate_table(self, tablename, schema, data_loss_ok=False, queue=False):
        try:
            current_table = self.read_table(tablename)
        except:
            print('table ' + tablename + ' does not currently exist (or there was another error) ')
            current_table = []

        self.create_table(tablename, schema, queue=True)
        # Check here to make sure we will not incur dataloss

        schema_columns = schema.columns()
        if current_table:
            all_exist = all(key in schema_columns for key,value in current_table[0].iteritems())

            if not all_exist and not data_loss_ok:
                print('NOT ALL KEYS EXIST IN SCHEMA AS IN TABLE YOU ARE MIGRATING FROM. OVERRIDE WITH data_loss_ok=True '
                      'kwarg or figure out why this is happening')
                print('Existing keys: ' + str([key for key,value in current_table[0].iteritems()]))
                print('Schema keys: ' + str(self.columns()))
                return
            elif all_exist and data_loss_ok:
                print('NOT ALL KEYS EXIST, BUT YOU SAID SO. SO I DO IT.')
        else:
            print('no table or tabledata exists :  ' + tablename)

        for row in current_table:
            self.insert(tablename, row, queue=True)
        if not queue:
            self.execute_queue()
        return current_table

<<<<<<< HEAD
    def get_table_size(self, tablename):
        return gettablesize(self.path, tablename)

    def read_table(self, tablename, **kwargs):
        dbrows = readalldbrows(self.path, tablename, **kwargs)
        return dbrows

    def read_table_row(self, tablename, row=0, **kwargs):
        dbrow = readonedbrow(self.path, tablename, row, **kwargs)
        return dbrow

    def read_table_rows(self, tablename, row=0, length=1, **kwargs):
        dbrows = readsomedbrows(self.path, tablename, row, length, **kwargs)
        return dbrows

    def get_last_time_row(self, tablename, timecolumn='time'):
        row = getlasttimerows(self.path, tablename, timecolumn)[0]
        return row

    def get_first_time_row(self, tablename, timecolumn='time'):
        row = getfirsttimerows(self.path, tablename, timecolumn)[0]
        return row

    def get_tuples(self, tablename, valuenames, condition=None):
        query = 'select '
        for valuename in valuenames:
            query += '"' + valuename + '",'
        query = query[:-1]
        query += " from '" + tablename + "'"
        if condition:
            query += ' where ' + condition
        data = self.query(query)['data']
        return data

=======
    def read_table(self, name, **kwargs):
        dbrows = readalldbrows(self.path, name, **kwargs)
        return dbrows

    def read_table_row(self, name, row=0, **kwargs):
        dbrow = readonedbrow(self.path, name, row, **kwargs)
        return dbrow

    def read_table_rows(self, name, row=0, length=1, **kwargs):
        dbrows = readsomedbrows(self.path, name, row, length, **kwargs)
        return dbrows

>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
    def get_pragma_names(self, tablename):
        return getpragmanames(self.path, tablename)

    def get_schema(self, tablename):
<<<<<<< HEAD
        schema = sqliteTableSchema(getpragma(self.path, tablename))
=======
        schema = getpragma(self.path, tablename)
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
        # maybe do some massaging
        return schema

    def get_table_size(self, tablename):
        return gettablesize(self.path, tablename)

    # Single table operations
<<<<<<< HEAD
    def set_single_value(self, tablename, valuename, value, condition=None, queue=False):
        query = makesinglevaluequery(tablename, valuename, value, condition)
        if queue:
            self.queue_queries([query])
        else:
            self.query(query)
=======
    def set_single_value(self, tablename, valuename, value, condition=None):
        setsinglevalue(self.path, tablename, valuename, value, condition)
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

    def get_single_value(self, tablename, valuename, condition=None):
        value = getsinglevalue(self.path, tablename, valuename, condition)
        return value

    def insert(self, tablename, insert, replace=True, queue=False):
        # Insert can be single insert or list

        if not (isinstance(insert, list)):
            insert_list = [insert]
        else:
            insert_list = insert

        queries = []
        for insert in insert_list:
            query = make_insert_from_dict(tablename, insert)
            queries.append(query)

        if queue:
            self.queue_queries(queries)
        else:
            self.queries(queries)

        return queries

    def insert_defaults(self, tablename, queue=False):
        query = "insert into " + tablename + "  default values"
        if queue:
            self.queue_queries([query])
        else:
            self.query(query)

    def delete(self, tablename, condition, queue=False):
        query = makedeletesinglevaluequery(tablename,condition)
        if queue:
            self.queue_queries([query])
        else:
            self.query(query)

    def empty_table(self, tablename, queue=False):
        query = makedeletesinglevaluequery(tablename, condition=None)
        if queue:
            self.queue_queries([query])
        else:
            self.query(query)

    def execute_queue(self, clear_queue=True):
        if self.queued_queries:
            self.queries(self.queued_queries)
        if clear_queue:
            self.clear_queue()

    def clear_queue(self):
        self.queued_queries = []

<<<<<<< HEAD
    def queue_query(self, query):
        self.queued_queries.append(query)

=======
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
    def queue_queries(self, queries):
        self.queued_queries.extend(queries)

    def query(self, query):
        result = sqlitequery(self.path, query)
        return result

    def queries(self, queries):
        result = sqlitemultquery(self.path, queries)
        return result

<<<<<<< HEAD
=======
    def table_names(self):
        return gettablenames(self.path)

>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

class tableSchema(object):

    def __init__(self, **kwargs):
        self.requiredproperties = ['properties']
        if not all(requiredproperty in kwargs for requiredproperty in self.requiredproperties):
            print('not all required properties required supplied : ')
            print(self.requiredproperties)
        else:
            for key, value in kwargs.iteritems():
                setattr(self, key, value)


# This one is instantiated with a list of schema items
class sqliteTableSchema(object):

    def __init__(self, items):
        # check over items list to ensure that there are not conflicts
        primary = 0
        self.valid_item_types = ['integer','boolean','text','real']
        self.required_schema_items = ['name']   # Default to text

        self.valid = True

        read_items = []
        for item in items:
            if item['name'] in read_items:
                print('DUPLICATE KEY IS PRESENT')
                return None
            else:
                read_items.append(item['name'])

            if not all(key in item for key in self.required_schema_items):
                print('item incomplete: ')
                print(item)
                print('required items: ')
                print(self.required_schema_items)
                self.valid = False
                break
            if 'type' in item:
                if item['type'] not in self.valid_item_types:
                    print('item type ' + item['type'] + ' invalid. Defaulting to text')
                    print(item)
                    self.valid = False
                    break
            else:   # default to text
                item['type'] = 'text'

            if item['type'] == 'text' and 'default' not in item:
                item['default'] = ''
            elif item['type'] == 'boolean' and 'default' not in item:
                item['default'] = 0
            elif 'default' not in item:
                item['default'] = 'null'

            if 'primary' in item and item['primary']:
                primary += 1
            else:
                item['options'] = ''

        if primary == 0:
            print('warning: no primary key provided for schema.')
        elif primary > 1:
            print('invalid schema: multiple primary keys found')
            for item in items:
                if 'primary' in item and item['primary']:
                    print(item['name'])
            self.valid = False

        self.items = items

    def columns(self):
        return [item['name'] for item in self.items]

    def defaults(self):
        return [item['default'] for item in self.items]

    def names(self):
        return [item['name'] for item in self.items]

    def types(self):
        return [item['type'] for item in self.items]

    def options(self):
        return [item['options'] for item in self.items]


def make_insert_from_dict(tablename, insert_dict, replace=True):
    values = []
    valuenames = []
    for key, value in insert_dict.iteritems():
        values.append(value)
        valuenames.append(key)
    insert_query = makesqliteinsert(tablename, values, valuenames=valuenames, replace=replace)

    return insert_query


def switchtablerows(database, table, rowid1, rowid2, uniqueindex):
    unique1 = sqlitedatumquery(database,
                               'select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid1))
    unique2 = sqlitedatumquery(database,
                               'select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid2))
    # print('select \'' + uniqueindex + '\'' + ' from \'' + table + '\' where rowid=' + str(rowid1))
    # print(unique1 + ' ' +  unique2)
    queryarray = []
    index = 'rowid'
    # Assumes there is no rowid=9999
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        9999) + ' where \'' + uniqueindex + '\'=\'' + unique2 + '\'')
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        rowid2) + ' where \'' + uniqueindex + '\'=\'' + unique1 + '\'')
    queryarray.append('update \'' + table + '\' set \'' + index + '\'=' + str(
        rowid1) + ' where \'' + uniqueindex + '\'=\'' + unique2 + '\'')

    # print(queryarray)
    sqlitemultquery(database, queryarray)


def removeandreorder(database, table, rowid, indicestoorder=None, uniqueindex=None):
    sqlitequery(database, ' from \'' + table + '\' where rowid=' + rowid)
    if indicestoorder and uniqueindex:
        ordertableindices(database, table, indicestoorder, uniqueindex)


def ordertableindices(databasename, tablename, indicestoorder, uniqueindex):
    table = readalldbrows(databasename, tablename)
    uniquearray = []
    for row in table:
        uniquearray.append(row[uniqueindex])
    queryarray = []
    for i, uniquevalue in enumerate(uniquearray):
        for indextoorder in indicestoorder:
            queryarray.append('update \'' + tablename + '\' set "' + indextoorder + '"=\'' + str(
                i + 1) + '\'  where "' + uniqueindex + '"=\'' + str(uniquevalue) + '\'')

    # print(queryarray)
    # print(queryarray)
    sqlitemultquery(databasename, queryarray)


def logtimevaluedata(database, tablename, timeinseconds, value, logsize=5000, logfrequency=0):
    from iiutilities.datalib import gettimestring, isvalidtimestring, timestringtoseconds
    timestring= gettimestring(timeinseconds)
    if isvalidtimestring(timestring):

        # Get last polltime to determine if we should log again yet.
        # lastpolltimestring = getlasttimerow(database, tablename)['time']
        try:
            lastpolltimestring = getlasttimevalue(database, tablename)
        except:
            lastpolltimestring = ''
        else:
            # print lastpolltimestring
            pass
        if timeinseconds- timestringtoseconds(lastpolltimestring) > logfrequency:

            # Create table if it doesn't exist

            query = 'create table if not exists \'' + tablename + '\' ( value real, time text primary key)'
            sqlitequery(database, query)

            # Enter row
            sqliteinsertsingle(database, tablename, valuelist=[value, timestring],
                                     valuenames=['value', 'time'])

            # Clean log
            cleanlog(database, tablename)

            # Size log based on specified size

            sizesqlitetable(database, tablename, logsize)
        else:
            # print('not time yet')
            pass
    else:
        # print('not enabled')
        pass


def gettablenames(database):
    result = sqlitequery(database, 'select name from sqlite_master where type=\'table\'')['data']
    tables = []
    for element in result:
        tables.append(element[0])
    return tables


def getdatameta(database):
    tablenames = gettablenames(database)
    queryarray = []
    for tablename in tablenames:
        queryarray.append("select count(*) from '" + tablename + "'")
    results = sqlitemultquery(database, queryarray)['data']
    meta = []
    for result, tablename in zip(results, tablenames):
        meta.append({'tablename':tablename, 'numpoints':result[0][0]})
    return meta


def getandsetmetadata(database):
    meta = getdatameta(database)
    queryarray = []
    queryarray.append('drop table if exists metadata')
    queryarray.append('create table metadata ( name text, numpoints int)')
    for metaitem in meta:
        queryarray.append("insert into metadata values ('" + str(metaitem['tablename']) + "','" + str(metaitem['numpoints']) + "')")
        #print(queryarray)
    sqlitemultquery(database, queryarray)


def getpragma(database, table):
    pragma = sqlitequery(database, 'pragma table_info ( \'' + table + '\')')['data']
    pragmadictlist = []
    for item in pragma:
        pragmadictlist.append({
            'name':item[1],
            'type':item[2],
            'default':item[4],
            'primary':bool(item[5])
        })
    return pragmadictlist


def getpragmanames(database, table):
    pragma = getpragma(database, table)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item['name'])
    return pragmanames


def getpragmatypes(database, table):
    pragma = getpragma(database, table)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item['type'])
    return pragmanames


def getpragmanametypedict(database, table):
    pragma = getpragma(database, table)
    pragmadict = {}
    for item in pragma:
        pragmadict[item['name']] = item['type']
    return pragmadict


def datarowtodict(database, table, datarow):
    pragmanames = getpragmanames(database, table)

    dict = {}
    index = 0
    for datum in datarow:
        dict[pragmanames[index]] = datum
        index += 1
    return dict


def insertstringdicttablelist(database, tablename, datadictarray, droptable=False):
    querylist = []
    if droptable:
        querylist.append('drop table if exists "' + tablename + '"')

        addquery = 'create table "' + tablename + '" ('
        for key in datadictarray[0]:
            addquery += "'" + key + "' text,"

        addquery = addquery[:-1]
        addquery += ')'
        querylist.append(addquery)

    for datadict in datadictarray:
        valuelist=[]
        valuenames=[]
        for key in datadict:
            valuelist.append(datadict[key])
            valuenames.append(key)
        insertquery = makesqliteinsert(tablename, valuelist, valuenames)
        # print(insertquery)
        querylist.append(insertquery)

    result = {'query': querylist}

    # try:
    # print(querylist)
    sqlitemultquery(database, querylist)
    # except:
    #     import sys, traceback
    #     result['tb'] = traceback.format_exc()
    #     result['status'] = 1
    # else:
    #     result['status'] = 0

    return result


def sqlite_create_table_query_from_schema(tablename, schema, **kwargs):
<<<<<<< HEAD
=======

    settings = {'removequotes':True, 'removeslashes':True}
    settings.update(kwargs)
    constructor = ''
    for item in schema.items:
        # Items are 'name', 'type', 'options'
        valuename = item['name']
        try:
            if settings['removequotes']:
                valuename = valuename.replace("'", '').replace('"', '')
            if settings['removeslashes']:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + item['type']

        # options.
        if 'primary' in item and item['primary']:
            constructor += ' primary key '
        elif 'unique' in item and item['unique']:
            constructor += ' unique '
        if 'default' in item:
            if item['type'] == 'text':
                constructor += " default '" + str(item['default']) + "'"
            else:
                constructor += " default " + str(item['default'])

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    return constructorquery


def sqlitecreateemptytablequery(tablename, valuenames, valuetypes, valueoptions=None, dropexisting=True,
                           removequotes=True, removeslashes=True):
    constructor = ''
    for index, valuename in enumerate(valuenames):
        try:
            if removequotes:
                valuename = valuename.replace("'", '').replace('"', '')
            if removeslashes:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + valuetypes[index]

        if valueoptions and valueoptions[index]:
            # limited. multiple options in the future.
            if 'primary' == valueoptions[index]:
                constructor += ' primary key'
            elif 'unique' == valueoptions[index]:
                constructor += ' unique'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"

    return constructorquery


def sqlitecreateemptytable(database, tablename, valuenames, valuetypes, valueoptions=None, dropexisting=True,
                           removequotes=True, removeslashes=True, execute=True):
    if len(valuenames) != len(valuetypes):
        print('Names and types are not of same length. Cannot continue. ')
        return None
    else:
        if valueoptions:
            if len(valuenames) != len(valueoptions):
                print('Valueoptions were delivered but do not appear to be the correct length. Cannot continue. ')
                return None
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

    settings = {'removequotes':True, 'removeslashes':True}
    settings.update(kwargs)
    constructor = ''
    for item in schema.items:
        # Items are 'name', 'type', 'options'
        valuename = item['name']
        try:
            if settings['removequotes']:
                valuename = valuename.replace("'", '').replace('"', '')
            if settings['removeslashes']:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + item['type']

        # options.
        if 'primary' in item and item['primary']:
            constructor += ' primary key '
        elif 'unique' in item and item['unique']:
            constructor += ' unique '
        if 'default' in item:
            if item['type'] == 'text':
                constructor += " default '" + str(item['default']) + "'"
            else:
                constructor += " default " + str(item['default'])

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    return constructorquery

<<<<<<< HEAD

def sqlitecreateemptytablequery(tablename, valuenames, valuetypes, valueoptions=None, dropexisting=True,
                           removequotes=True, removeslashes=True):
    constructor = ''
    for index, valuename in enumerate(valuenames):
        try:
            if removequotes:
                valuename = valuename.replace("'", '').replace('"', '')
            if removeslashes:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + valuetypes[index]

        if valueoptions and valueoptions[index]:
            # limited. multiple options in the future.
            if 'primary' == valueoptions[index]:
                constructor += ' primary key'
            elif 'unique' == valueoptions[index]:
                constructor += ' unique'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"

    return constructorquery


def sqlitecreateemptytable(database, tablename, valuenames, valuetypes, valueoptions=None, dropexisting=True,
                           removequotes=True, removeslashes=True, execute=True):
    if len(valuenames) != len(valuetypes):
        print('Names and types are not of same length. Cannot continue. ')
        return None
    else:
        if valueoptions:
            if len(valuenames) != len(valueoptions):
                print('Valueoptions were delivered but do not appear to be the correct length. Cannot continue. ')
                return None

    existingtablenames = gettablenames(database)
    if tablename in existingtablenames:
        if dropexisting:
            sqlitedroptable(database, tablename)
        else:
            # Check to see if this will work out? Match fields, etc.
            pass

    constructorquery = sqlitecreateemptytablequery(tablename, valuenames, valuetypes, valueoptions, dropexisting,
                                                   removequotes, removeslashes)
    if 'execute':
        sqlitequery(database, constructorquery)
    return constructorquery
=======
    constructorquery = sqlitecreateemptytablequery(tablename, valuenames, valuetypes, valueoptions, dropexisting,
                                                   removequotes, removeslashes)
    if 'execute':
        sqlitequery(database, constructorquery)
    return constructorquery

>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4


def dropcreatetexttablefromdict(databasename, tablename, dictordictarray, removequotes=True, removeslashes=True, primarykey=None):
    querylist = []
    constructor = ''
    querylist.append('drop table if exists "' + tablename + '"')

    # just make it an array if not so we can handle the array
    if isinstance(dictordictarray, dict):
        dictarray = [dictordictarray]
    else:
        dictarray = dictordictarray

    for key, value in dictarray[0].items():
        try:
            if removequotes:
                key = key.replace("'", '').replace('"', '')
            if removeslashes:
                key = key.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(key))

        constructor = constructor + "'" + key + "' text"
        if primarykey:
            if key == primarykey:
                constructor += ' primary key'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    # print(constructorquery)
    querylist.append(constructorquery)

    for singledict in dictarray:
        valuelist = ''
        for key, value in singledict.items():
            if removequotes:
                value = str(value).replace("'", '').replace('"', '')
            if removeslashes:
                value = str(value).replace("\\", '').replace("/", "")

            valuelist = valuelist + '\"' + value + '\",'
        querylist.append('insert or replace into \"' + tablename + '\" values (' + valuelist[:-1] + ')')

    # print(querylist)
    sqlitemultquery(databasename, querylist)


def makesqliteinsert(table, valuelist, valuenames=None, replace=True):
    if replace:
        query = 'insert or replace into '
    else:
        query = 'insert into '
    query += "'" + table + "'"

    if valuenames:
        query += ' ('
        for valuename in valuenames:
            query += "'" + str(valuename) + "',"
        query = query[:-1] + ')'

    query += ' values ('

    for value in valuelist:
        strvalue = str(value).replace("'","''")
        query += "'" + strvalue + "',"
    query = query[:-1] + ')'
    return query


def sqliteinsertsingle(database, table, valuelist, valuenames=None, replace=True):
    import sqlite3 as lite

    query = makesqliteinsert(table, valuelist, valuenames, replace)
    result = sqlitequery(database, query)

    return result



def sqlitemultquery(database, querylist, **kwargs):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    settings = {'break_on_error':False}
    settings.update(kwargs)
    with con:
        cur = con.cursor()
        data = []
        message = ''
        status = 0
        for query in querylist:
            try:
                cur.execute(query)
            except:
                import traceback
                dataitem = ''
                trace_msg = 'Error with query: "' + query + '"\n\t' + traceback.format_exc()
                message += trace_msg
                status = 1
                if not 'quiet' in kwargs:
                    print(trace_msg)
                if settings['break_on_error']:
                    break
            else:
                dataitem = cur.fetchall()

            data.append(dataitem)
        con.commit()
<<<<<<< HEAD

    return {'data':data, 'message':message, 'status':status}
=======
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4

    return {'data':data, 'message':message, 'status':status}

<<<<<<< HEAD
=======

>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
def sqlitequery(database, query, **kwargs):
    import sqlite3 as lite

    con = lite.connect(database)
    con.text_factory = str

    try:
        with con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
    except:
        import traceback
        data = ''
        message = traceback.format_exc()
        status = 1
<<<<<<< HEAD
        print('error with query: "' + query + '"')
=======
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
        if not 'quiet' in kwargs:
            print(message)
    else:
        status = 0
        message = 'all seems ok'

    return {'data':data, 'status':status, 'message':message}


def sqlitedatumquery(database, query):
    datarow = sqlitequery(database, query)['data']
    if datarow:
        datum = datarow[0][0]
    else:
        datum = ''
    return datum


def getsinglevalue(database, table, valuename, condition=None):
    query = makegetsinglevaluequery(table, valuename, condition)
    # print(query)
    response = sqlitedatumquery(database, query)
    return response


def makegetsinglevaluequery(table, valuename, condition=None):
    query = 'select \"' + valuename + '\" from \'' + table + '\''
    if isinstance(condition, dict):
        try:
            conditionnames = condition['conditionnames']
            conditionvalues = condition['conditionvalues']
        except:
            # print('oops')
            pass
        else:
            query += ' where '
            numconditions = len(conditionnames)
            for index, (name, value) in enumerate(zip(conditionnames, conditionvalues)):
                query += "\"" + name + "\"='" + value + "'"
                if index < numconditions-1:
                    query += ' and '
            # print(query)
    elif isinstance(condition, basestring):
        query += ' where ' + condition
    return query


def sqlitedeleteitem(database, table, condition=None):
    query = makedeletesinglevaluequery(table, condition)
    sqlitequery(database, query)


def makedeletesinglevaluequery(table, condition=None):
    query = "delete from '" + table + "'"
    if isinstance(condition, dict):
        try:
            conditionnames = condition['conditionnames']
            conditionvalues = condition['conditionvalues']
        except:
            print('oops')
        else:
            query += ' where '
            numconditions = len(conditionnames)
            for index, (name, value) in enumerate(zip(conditionnames, conditionvalues)):
                query += '"' + name + '"' + "='" + value + "'"
                if index < numconditions-1:
                    query += ' and '
    elif isinstance(condition, basestring):
        query += ' where ' + condition
    return query


def readalldbrows(database, table, condition=None, includerowids=True):

    query = "select * from '" + table + "'"
    if condition:
        query += ' where ' + condition

    data = sqlitequery(database, query)['data']

    pragmanames = getpragmanames(database, table)

    dictarray = []
    for row in data:
        dict = {}
        index = 0
        for datum in row:
            dict[pragmanames[index]] = datum
            index += 1
        dictarray.append(dict)

    return dictarray


def makegetallrowsquery(tablename):
    query = "select * from '" + tablename + "'"
    return query


def getentiredatabase(databasename, method='nometa'):
    # Get names of all tables in database
    tablenames = gettablenames(databasename)
    databasequery = []

    # Construct a query for each table
    for tablename in tablenames:
        databasequery.append(makegetallrowsquery(tablename))

    # Execute multiple query to return data
    alldatabasedata = sqlitemultquery(databasename, databasequery)['data']
    reconstructeddatabase=[]
    tables = []

    # This method blindly produces lists
    if method == 'nometa':
        # reconstruct without tuples

        for index, table in enumerate(alldatabasedata):
            newtable = []
            for row in table:
                newtable.append(list(row))
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data': newtable})

    # This method puts meta from each table into a dictionary entry
    elif method == 'metameta':
        for index, table in enumerate(alldatabasedata):
            newtable = []

            # print(tablenames[index])
            meta = getpragmanames(databasename, tablenames[index])
            for row in table:
                newtable.append(list(row))
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data':newtable, 'meta':meta})

    # This method produces a list of dictionaries so all data is self-described (but big)
    else:

        for index, table in enumerate(alldatabasedata):
            newtable = []

            # print(tablenames[index])
            pragmanames = getpragmanames(databasename, tablenames[index])
            for row in table:
                newrow = {}

                for name, value in zip(pragmanames, row):
                    newrow[name] = value
                newtable.append(newrow)
            reconstructeddatabase.append(newtable)
            tables.append({'tablename': tablenames[index], 'data':newtable})

    return {'data': reconstructeddatabase, 'dictarray': tables, 'tablenames': tablenames}


def sqliteemptytable(database, tablename):
    querylist = []
    querylist.append('delete from \'' + tablename + '\'')
    sqlitemultquery(database, querylist)


def emptyandsetdefaults(database, tablename):
    querylist = []
    querylist.append('delete from \'' + tablename + '\'')
    querylist.append('insert into \'' + tablename + '\' default values')
    sqlitemultquery(database, querylist)


# Now we put them together into a dynamically typed function
# that we specify operation based on what arguments we send
# No location argument = entire database
# One location argument = single row
# Two arguments = range of rows


def dynamicsqliteread(database, table, start=None, length=None, condition=None):
    if length is None and start is None:
        dictarray = readalldbrows(database, table, condition)
    elif length is None:
        dictarray = readonedbrow(database, table, start, condition)
    else:
        dictarray = readsomedbrows(database, table, start, length, condition)

    return dictarray


def cleanlog(databasename, logname):
    sqlitequery(databasename, "delete from '" + logname + "' where time =''")


def sqliteduplicatetable(database, oldname, newname):
    # Get pragma to create table
    oldcreatequery = sqlitequery(database, "SELECT sql FROM sqlite_master WHERE type='table' AND name='" + oldname + "'")['data'][0][0]

    # Check to see if it was created with quotes or not
    # Gotta use quotes on new name for safety
    if oldcreatequery.find('"' + oldname + '"') >= 0:
        newcreatequery = oldcreatequery.replace('"' + oldname + '"', "'" + newname + "'")
    elif oldcreatequery.find("'" + oldname + "'") >= 0:
        newcreatequery = oldcreatequery.replace("'" + oldname + "'", "'" + newname + "'")
    else:
        newcreatequery = oldcreatequery.replace(oldname, "'" + newname + "'")

    sqlitequery(database, newcreatequery)

    # Now get all the old data and insert it
    data=readalldbrows(database, oldname)

    # We have to drop all records and insert string without the droptable, just in case it already exists.
    # This way we retain the table structure
    sqlitedeleteallrecords(database, newname)
    insertstringdicttablelist(database, newname, data, droptable=False)


def sqlitemovetable(database, oldname, newname):
    sqliteduplicatetable(database, oldname, newname=newname)
    sqlitedroptable(database, oldname)


def sqlitedeleteallrecords(database, table):
    sqlitequery(database, 'delete from "' + table + '"')


def sqlitedroptable(database, table, quiet=False):
    sqlitequery(database, 'drop table "' + table + '"', quiet=quiet)


def sqlitedropalltables(database):
    # not optimized
    existingtables = gettablenames(database)
    queries = []
    if existingtables:
        for table in existingtables:
            queries.append('drop table "' + table + '"')
        sqlitemultquery(database, queries)


def sqlitedropalltables(database):
    # not optimized
    existingtables = gettablenames(database)
    queries = []
    if existingtables:
        for table in existingtables:
            queries.append('drop table "' + table + '"')
        sqlitemultquery(database, queries)


def gettablesize(databasename, tablename):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')
    return logsize


def sizesqlitetable(databasename, tablename, size):
    logsize = sqlitedatumquery(databasename, 'select count(*) from \'' + tablename + '\'')

    if logsize and (logsize > size):
        logexcess = int(logsize) - int(size)
        sqlitequery(databasename, 'delete from\'' + tablename + '\' order by time limit ' + str(logexcess))
    else:
        logexcess = -1

    return (logexcess)


<<<<<<< HEAD
def getfirsttimerows(database, tablename, timecolname='time', numrows=1):
    query = 'select * from \'' + tablename + "' order by'" + timecolname + "' desc limit " + str(int(numrows))
    data = sqlitequery(database, query)['data']
=======
def getfirsttimerow(database, tablename, timecolname='time'):
    query = 'select * from \'' + tablename + '\' order by \'' + timecolname + '\' limit 1'
    data = sqlitequery(database, query)['data'][0]
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
    try:
        dictarray = []
        for datum in data:
            dict = datarowtodict(database, tablename, datum)
            dictarray.append(dict)
    except:
        # print('no row here')
        dictarray = {}
        pass
    return dictarray


<<<<<<< HEAD
def getlasttimerows(database, tablename, timecolname='time', numrows=1):
    query = 'select * from \'' + tablename + "' order by'" + timecolname + "' desc limit " + str(int(numrows))
=======
def getlasttimerows(database, tablename, numrows=1):
    query = 'select * from \'' + tablename + '\' order by time desc limit ' + str(int(numrows))
>>>>>>> 4658da7edce3628e94d01808b4f389c7ceb428d4
    data = sqlitequery(database, query)['data']
    try:
        dictarray = []
        for datum in data:
            dict = datarowtodict(database, tablename, datum)
            dictarray.append(dict)
    except:
        # print('no row here')
        dictarray = {}
        pass
    return dictarray


def getlasttimevalue(database, tablename):
    query = 'select time from \'' + tablename + '\' order by time desc limit 1'
    data = sqlitequery(database, query)['data'][0][0]
    return data


def sqlitedatadump(databasename, tablelist, outputfilename, limit=None):
    import csv

    queryarray = []

    # These are for csv file headers
    allpragmanames = []
    alltablelist = []

    for tablename in tablelist:
        pragmanames = getpragmanames(databasename, tablename)
        for pragmaname in pragmanames:
            alltablelist.append(tablename)
            allpragmanames.append(pragmaname)
            if limit is not None:
                queryarray.append('select ' + pragmaname + ' from \'' + tablename + '\' limit ' + str(limit))
            else:
                queryarray.append('select ' + pragmaname + ' from \'' + tablename + '\'')
    data = sqlitemultquery(databasename, queryarray)['data']
    #print(data)
    newdata = []
    for outerlist in data:
        newinnerlist = []
        for innerlist in outerlist:
            newinnerlist.append(innerlist[0])
        newinnerlist.insert(0, allpragmanames.pop(0))
        newinnerlist.insert(0, alltablelist.pop(0))
        newdata.append(newinnerlist)

    #print(newdata)
    with open(outputfilename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(newdata)


def setsinglevalue(database, table, valuename, value, condition=None):
    query = makesinglevaluequery(table, valuename, value, condition)
    response = sqlitequery(database, query)['data']
    return response


def makesinglevaluequery(table, valuename, value, condition=None):
    query = 'update ' + "'" + table + '\' set "' + valuename + '"=\'' + str(value) + "'"
    if condition:
        query += ' where ' + condition
    return query


def readonedbrow(database, table, rownumber=0, condition=None):
    query = "select * from '" + table + "'"
    if condition:
        query += ' where ' + condition
    data = sqlitequery(database, query)['data']
    try:
        datarow = data[rownumber]

        dict = datarowtodict(database, table, datarow)
        dictarray = [dict]
    except:
        dictarray = []

    return dictarray


def readsomedbrows(database, table, start, length, condition=None):

    # User specifies length of data, and where to start, in terms of row index
    # If a negative number is the start argument, data is retrieved from the end of the data

    if start >= 0:
        query = "select * from '" + table + "' limit " + str(start) + ',' + str(length)
    else:
        query = "select * from '" + table + "' order by rowid desc " + " limit " + str(length)
    # print(query)
    if condition:
        query += ' where ' + condition

    datarows = sqlitequery(database, query)['data']

    # This is the old code. Requires retrieving the entire table

    # Start < 0 retrieves from end of list
    # if start < 0:
    #     datarows = data[len(data)-length:len(data)-1]
    # else:
    #     datarows = data[int(start):int(start + length)]

    pragmanames = getpragmanames(database, table)

    dictarray = []
    for row in datarows:
        dict = {}
        index = 0
        for datum in row:
            dict[pragmanames[index]] = datum
            index += 1
        dictarray.append(dict)

    return dictarray


def dbvntovalue(dbvn, interprettype=False):

    from iiutilities.datalib import parsedbvn, getvartype
    dbvndict = parsedbvn(dbvn)
    print(dbvndict)
    # try:

    value = getsinglevalue(dbvndict['dbpath'], dbvndict['tablename'], dbvndict['valuename'], dbvndict['condition'])
    # except:
    #     print('error getting value')
    #     print(dbvndict)
    #     return None

    if interprettype:
        # get type

        vartype = getvartype(dbvndict['dbpath'], dbvndict['tablename'], dbvndict['valuename'])

        if vartype == 'boolean':
            return bool(value)
        elif vartype == 'float':
            return float(value)
        elif vartype == 'int':
            return int(value)

    return value