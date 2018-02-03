#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


"""

Database tools

"""


class sqliteDatabase(object):

    def __init__(self, path, **kwargs):

        settings = {
            'log_errors':False,
            'quiet':False
                    }
        settings.update(kwargs)

        # we do this so we can pass these settings as kwargs.
        # We pass them into the functions that exist outside of this class, which cannot
        # pull things like 'quiet' from self.

        self.settings = settings

        for item in settings:
            # This will catch all logging options, so when we execute a query,
            # they will be attributes already set.

            setattr(self, item, settings[item])

        # Verify database exists
        self.path = path
        self.queued_queries = []
        # print('INITIALIZED with QUIET: {}'.format(settings['quiet']))

    def get_table_names(self):
        self.tablenames = gettablenames(self.path, **self.settings)
        return self.tablenames

    def create_table(self, name, schema, queue=False, dropexisting=True, migrate=False):
        if schema.valid:
            if migrate:
                query = self.migrate_table(name, schema, queue=queue)
            else:
                if dropexisting:
                    self.drop_table(name, queue=queue)

                query = sqlite_create_table_query_from_schema(name, schema)

            # We will get an empty query if no data items yet exist
            if query:
                if queue:
                    self.queue_queries([query])
                else:
                    self.query(query)
        else:
            print('schema is invalid')

    def touch(self):
        import os
        with open(self.path, 'a'):
            os.utime(self.path, None)

    def drop_table(self, name, queue=False, **kwargs):

        self.settings.update(kwargs)
        if queue:
            self.queue_queries(["drop table '" + name + "'"])
        else:
            sqlitedroptable(self.path, name, **self.settings)

    def drop_all_tables(self, queue=False, quiet=False):
        tables = self.get_table_names()
        for table_name in tables:
            self.drop_table(table_name, queue=True, quiet=quiet)
        if not queue:
            self.execute_queue()

    def drop_empty_tables(self):
        tablenames = self.get_table_names()
        for tablename in tablenames:
            if self.get_table_size(tablename) == 0:
                self.drop_table(tablename, queue=True, **self.settings)
        if self.queued_queries:
            self.execute_queue()

    def move_table(self, oldname, newname, **kwargs):
        sqlitemovetable(self.path, oldname, newname, **kwargs)

    def migrate_table(self, tablename, schema, data_loss_ok=False, queue=False, **kwargs):
        self.settings.update(kwargs)
        current_table = []
        if tablename in self.get_table_names():
            try:
                current_table = self.read_table(tablename, **self.settings)
            except:
                print('table ' + tablename + ' rebuild error) ')
                current_table = []
        else:
            print('Table does not exist. Continuing')


        schema_columns = schema.columns()
        if current_table:
            all_exist = all(key in schema_columns for key in current_table[0])

            if not all_exist and not data_loss_ok:
                print('NOT ALL KEYS EXIST IN SCHEMA AS IN TABLE YOU ARE MIGRATING FROM. OVERRIDE WITH data_loss_ok=True '
                      'kwarg or figure out why this is happening')
                print('Existing keys: ' + str([key for key in current_table[0]]))
                print('Schema keys: ' + str(schema_columns))

                for this_key in [key for key in current_table[0]]:
                    if this_key not in schema_columns:
                        print('Not in schema: {}'.format(this_key))
                return
            elif all_exist and data_loss_ok:
                print('NOT ALL KEYS EXIST, BUT YOU SAID SO. SO I DO IT.')
        else:
            print('no table or tabledata exists :  ' + tablename)

        self.create_table(tablename, schema, queue=True)

        # Check here to make sure we will not incur dataloss
        if current_table:
            for row in current_table:
                self.insert(tablename, row, queue=True)

        # have we created some queries internally?
        if not queue and self.queued_queries:
            print('Migrate queries: ')
            print(self.queued_queries)

            self.execute_queue()

        return current_table

    def get_table_size(self, tablename, **kwargs):
        self.settings.update(kwargs)
        return gettablesize(self.path, tablename, **self.settings)

    def read_tables(self, tablenames, **kwargs):
        all_queries = []
        for tablename in tablenames:
            all_queries.extend(makegetallrowswithpragmaquery(tablename))

        results = self.queries(all_queries)
        result_data = results['data']

        return_data = {}
        for index, tablename in enumerate(tablenames):
            the_data = result_data[index*2]
            pragma = process_pragma(result_data[index*2 + 1])

            is_primary = False
            primary_key = pragma[0]['name']
            pragma_names = []
            for pragma_item in pragma:
                # print(pragma_item)
                if pragma_item['primary']:
                    primary_key = pragma_item['name']
                    is_primary = True
                pragma_names.append(pragma_item['name'])

            dictarray = []
            keyed_dict = {}
            for row in the_data:
                dict = {}
                for datum, pragma_name in zip(row, pragma_names):
                    dict[pragma_name] = datum
                dictarray.append(dict)
                keyed_dict[dict[primary_key]] = dict

            return_data[tablename] = dictarray

        return return_data

    def read_table(self, tablename, **kwargs):
        # Need to delete condition if not passed every time. We want to keep it in settings, but it has a habit
        # of hanging around when it's not wanted.
        # TODO : Think about this.
        settings = {
            'timing':False
        }
        settings.update(kwargs)

        if 'condition' not in kwargs and 'condition' in self.settings:
            del self.settings['condition']

        self.settings.update(kwargs)

        if settings['timing']:
            from datetime import datetime
            start_time = datetime.now()

        db_result = readalldbrows(self.path, tablename, **self.settings)

        if settings['timing']:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print('Elapsed Time: {}'.format(elapsed_time))

        if 'all_results' in kwargs and kwargs['all_results']:
            return db_result
        elif 'keyed_dict' in kwargs and kwargs['keyed_dict']:
            return db_result['keyed_dict']
        else:
            return db_result['dict_array']

    def read_database(self, **kwargs):
        settings = {
            'method': 'bundle',
            'timing': True
        }
        self.settings.update(kwargs)
        settings.update(kwargs)

        if settings['timing']:
            from datetime import datetime
            start_time = datetime.now()

        if settings['method'] == 'std':
            print('standard')
            all_data = {}
            for tablename in self.get_table_names():
                all_data[tablename] = self.read_table(tablename, **self.settings)
        elif settings['method'] == 'bundle':
            print('bundle')
            all_data = self.read_tables(self.get_table_names())

        if settings['timing']:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print('Elapsed DB read time: {}'.format(elapsed_time))

        return all_data

    def read_table_smart(self, tablename, condition=None):
        queries = ['pragma busy_timeout=2000', "pragma table_info ('" + tablename + "')",]
        queries.append("select * from '" + tablename + "'")
        results = self.queries(queries)
        pragma_dict_list = process_pragma(results['data'][1])
        pragmanames = [item['name'] for item in pragma_dict_list]

        dictarray = []
        for row in results['data'][2]:
            dict = {}
            for index, (datum, pragmaname) in enumerate(zip(row, pragmanames)):
                dict[pragmanames[index]] = datum
            dictarray.append(dict)
        return dictarray

    def read_table_row(self, tablename, **kwargs):
        self.settings.update(kwargs)
        dbrow = readonedbrow(self.path, tablename, **self.settings)
        return dbrow

    def read_table_rows(self, tablename,**kwargs):
        self.settings['start'] = 0
        self.settings.update(kwargs)
        dbrows = readsomedbrows(self.path, tablename, **self.settings)
        return dbrows

    def get_last_time_row(self, tablename, timecolumn='time'):
        row = getlasttimerows(self.path, tablename, timecolname=timecolumn, **self.settings)[0]
        return row

    def get_last_time_rows(self, tablename, rows=1, timecolumn='time'):
        rows = getlasttimerows(self.path, tablename, timecolname=timecolumn, numrows=rows, **self.settings)
        return rows

    def get_first_time_row(self, tablename, timecolumn='time'):
        row_reply = getfirsttimerows(self.path, tablename, timecolname=timecolumn, **self.settings)
        if not row_reply:
            return []
        else:
            return row_reply[0]

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

    def get_pragma_names(self, tablename):
        return getpragmanames(self.path, tablename, **self.settings)

    def get_schema(self, tablename):
        schema = sqliteTableSchema(getpragma(self.path, tablename))
        # maybe do some massaging
        return schema

    # Single table operations
    def set_single_value(self, tablename, valuename, value, **kwargs):
        settings = {
            'condition':None,
            'queue': False
        }
        settings.update(kwargs)
        query = makesinglevaluequery(tablename, valuename, value, settings['condition'])
        if settings['queue']:
            self.queue_queries([query])
        else:
            result = self.query(query)
            return result

    def get_single_value(self, tablename, valuename, **kwargs):
        settings = {
            'condition': None,
            'queue': False
        }
        settings.update(kwargs)
        query = makegetsinglevaluequery(tablename, valuename, condition=settings['condition'])
        value = sqlitedatumquery(self.path, query, **self.settings)
        return value

    def get_values(self, tablename, valuenames, condition=None):
        query = 'select '
        for valuename in valuenames:
            query += '"' + valuename + '",'

        query=query[:-1]
        query += ' from {} '.format(tablename)

        if condition:
            query += 'where ' + condition

        result = self.query(query)

        return_dict = {}
        try:
            for valuename, value in zip(valuenames, result['data'][0]):
                return_dict[valuename] = value
        except:
            pass

        return return_dict

    def set_wal_mode(self, wal=True):
        if wal:
            query = 'pragma journal_mode=wal'
        else:
            query = 'pragma journal_mode=delete'
        self.query(query)

    def get_wal_mode(self):
        query = 'pragma journal_mode'
        reply = self.query(query)
        return reply

    def insert(self, tablename, insert, **kwargs):
        settings = {
            'replace':True,
            'queue':False
        }
        settings.update(kwargs)

        if 'quiet' in kwargs:
            self.settings['quiet']=settings['quiet']

        # Insert can be single insert or list (or falsy to insert defaults)
        if not insert:
            queries = ["insert into '" + tablename + "'default values"]
        else:
            if not (isinstance(insert, list)):
                insert_list = [insert]
            else:
                insert_list = insert

            queries = []
            for insert in insert_list:
                query = make_insert_from_dict(tablename, insert)
                queries.append(query)

        if settings['queue']:
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

    def size_table(self, tablename, **size_options):
        # We have to split this up so that we can use our db options to enforce quiet, etc.
        # Well, that did not totally work as we have to query against the database to get size in the size
        # function. For now, we'll just merge options, but need to be aware that option names cannot collide.
        size_options.update(self.settings)
        size_options['dry_run'] = True
        size_query = size_sqlite_table(self.path, tablename, **size_options)['query']
        if size_query:
            self.query(size_query, **self.settings)

    def empty_table(self, tablename, queue=False):
        query = makedeletesinglevaluequery(tablename, condition=None)
        if queue:
            self.queue_queries([query])
        else:
            self.query(query)

    def clean_log(self, tablename, **kwargs):
        self.query("delete from '" + tablename + "' where time =''", **kwargs)

    def execute_queue(self, clear_queue=True, **kwargs):
        self.settings.update(kwargs)
        if self.queued_queries:
            self.queries(self.queued_queries)
        if clear_queue:
            self.clear_queue()

    def clear_queue(self):
        self.queued_queries = []

    def queue_query(self, query):
        self.queued_queries.append(query)

    def queue_queries(self, queries):
        self.queued_queries.extend(queries)

    def query(self, query, **kwargs):
        self.settings.update(kwargs)
        result = sqlitequery(self.path, query, **self.settings)
        return result

    def queries(self, queries):
        result = sqlitemultquery(self.path, queries, **self.settings)
        return result


class tableSchema(object):

    def __init__(self, **kwargs):
        self.requiredproperties = ['properties']
        if not all(requiredproperty in kwargs for requiredproperty in self.requiredproperties):
            print('not all required properties required supplied : ')
            print(self.requiredproperties)
        else:
            for key in kwargs:
                setattr(self, key, kwargs[key])


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
            pass
            # print('warning: no primary key provided for schema.')
        elif primary > 1:
            print('invalid schema: multiple primary keys found')
            for item in items:
                if 'primary' in item and item['primary']:
                    print(item['name'])
            self.valid = False

        self.items = items

    def __repr__(self):
        string_rep = ''
        for item in self.items:
            string_rep += '{}\n'.format(item)
        return string_rep

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


def make_insert_from_dict(tablename, insert_dict, replace=True, db_type='sqlite'):
    values = []
    valuenames = []
    for key in insert_dict:
        values.append(insert_dict[key])
        valuenames.append(key)
    if db_type == 'sqlite':
        column_quotes = True
        tablename_quotes = True
    elif db_type == 'mysql':
        column_quotes = False
        tablename_quotes = False

    insert_query = makesqliteinsert(tablename, values, valuenames=valuenames, replace=replace, column_quotes=column_quotes, tablename_quotes=tablename_quotes)

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


def removeandreorder(database, table, rowid, indicestoorder=None, uniqueindex=None, **kwargs):
    sqlitequery(database, ' from \'' + table + '\' where rowid=' + rowid)
    if indicestoorder and uniqueindex:
        ordertableindices(database, table, indicestoorder, uniqueindex)


def ordertableindices(databasename, tablename, indicestoorder, uniqueindex, **kwargs):
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


def logtimevaluedata(database, tablename, timeinseconds, value, logsize=5000, logfrequency=0, **kwargs):
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

            size_sqlite_table(database, tablename, logsize)
        else:
            # print('not time yet')
            pass
    else:
        # print('not enabled')
        pass


def gettablenames(database, **kwargs):
    result = sqlitequery(database, 'select name from sqlite_master where type=\'table\'', **kwargs)['data']
    tables = []
    for element in result:
        tables.append(element[0])
    return tables


def gettimespan(database, tablename, time_col='time'):
    from iiutilities.datalib import timestringtoseconds
    first_query = "select \"{}\" from '{}' order by \"{}\" asc limit 1".format(time_col, tablename, time_col)
    last_query = "select \"{}\" from '{}' order by \"{}\" desc limit 1".format(time_col, tablename, time_col)
    result = sqlitemultquery(database, [first_query, last_query])
    first_time_string = result['data'][0][0][0]
    last_time_string = result['data'][1][0][0]
    timespan_float = timestringtoseconds(last_time_string) - timestringtoseconds(first_time_string)
    return {'days':timespan_float / 3600 / 24, 'hours':timespan_float/3600, 'minutes':timespan_float/60, 'seconds':timespan_float}


def process_pragma(pragma):
    pragmadictlist = []
    for item in pragma:
        pragmadictlist.append({
            'name': item[1],
            'type': item[2],
            'default': item[4],
            'primary': bool(item[5])
        })
    return pragmadictlist


def getpragma(database_path, table, **kwargs):
    pragma = sqlitequery(database_path, 'pragma table_info ( \'' + table + '\')', **kwargs)['data']
    pragmadictlist = process_pragma(pragma)
    return pragmadictlist


def getpragmanames(database, table, **kwargs):
    pragma = getpragma(database, table, **kwargs)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item['name'])
    return pragmanames


def getpragmatypes(database, table, **kwargs):
    pragma = getpragma(database, table, **kwargs)
    pragmanames = []
    for item in pragma:
        pragmanames.append(item['type'])
    return pragmanames


def getpragmanametypedict(database, table, **kwargs):
    pragma = getpragma(database, table, **kwargs)
    pragmadict = {}
    for item in pragma:
        pragmadict[item['name']] = item['type']
    return pragmadict


def datarowtodict(database, table, datarow, **kwargs):
    pragmanames = getpragmanames(database, table, **kwargs)

    dict = {}
    index = 0
    for datum in datarow:
        dict[pragmanames[index]] = datum
        index += 1
    return dict


def string_condition_from_lists(conditionnames, conditionvalues):
    numconditions = len(conditionnames)
    condition = ''

    for index, (name, value) in enumerate(zip(conditionnames, conditionvalues)):
        condition += "\"" + name + "\"='" + value + "'"
        if index < numconditions - 1:
            condition += ' and '

    return condition


def insertstringdicttablelist(database, tablename, datadictarray, droptable=False, **kwargs):
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
    sqlitemultquery(database, querylist, **kwargs)
    # except:
    #     import sys, traceback
    #     result['tb'] = traceback.format_exc()
    #     result['status'] = 1
    # else:
    #     result['status'] = 0

    return result


def sqlite_create_table_query_from_schema(tablename, schema, **kwargs):

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

    constructorquery = "create table if not exists '" + tablename + "' (" + constructor[:-1] + ")"
    return constructorquery


def sqlitecreateemptytablequery(tablename, valuenames, valuetypes, **kwargs):
    settings = {
        'valueoptions': None,
        'removequotes': True,
        'removeslashes': True,
        'execute': True
    }
    settings.update(kwargs)

    constructor = ''
    for index, valuename in enumerate(valuenames):
        try:
            if settings['removequotes']:
                valuename = valuename.replace("'", '').replace('"', '')
            if settings['removeslashes']:
                valuename = valuename.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(valuename))

        constructor += "'" + valuename + "' " + valuetypes[index]

        if settings['valueoptions'] and settings['valueoptions'][index]:
            # limited. multiple options in the future.
            if 'primary' == settings['valueoptions'][index]:
                constructor += ' primary key'
            elif 'unique' == settings['valueoptions'][index]:
                constructor += ' unique'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"

    return constructorquery


def sqlitecreateemptytable(database, tablename, valuenames, valuetypes, **kwargs):

    settings = {
        'valueoptions':None,
        'dropexisting': True,
        'removequotes': True,
        'removeslashes': True,
        'execute': True
    }
    settings.update(kwargs)

    if len(valuenames) != len(valuetypes):
        print('Names and types are not of same length. Cannot continue. ')
        return None
    else:
        if settings['valueoptions']:
            if len(valuenames) != len(settings['valueoptions']):
                print('Valueoptions were delivered but do not appear to be the correct length. Cannot continue. ')
                return None

    existingtablenames = gettablenames(database)
    if tablename in existingtablenames:
        if settings['dropexisting']:
            sqlitedroptable(database, tablename)
        else:
            # Check to see if this will work out? Match fields, etc.
            pass

    constructorquery = sqlitecreateemptytablequery(tablename, valuenames, valuetypes, **settings)
    if settings['execute']:
        sqlitequery(database, constructorquery, **kwargs)
    return constructorquery


def dropcreatetexttablefromdict(databasename, tablename, dictordictarray, **kwargs):
    settings = {
        'removequotes': True,
        'removeslashes': True,
        'primarykey': None
    }
    settings.update(kwargs)

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
            if settings['removequotes']:
                key = key.replace("'", '').replace('"', '')
            if settings['removeslashes']:
                key = key.replace("\\", '').replace("/", "")
        except:
            print('error replacing in key ' + str(key))

        constructor = constructor + "'" + key + "' text"
        if settings['primarykey']:
            if key == settings['primarykey']:
                constructor += ' primary key'

        constructor += ","

    constructorquery = "create table '" + tablename + "' (" + constructor[:-1] + ")"
    # print(constructorquery)
    querylist.append(constructorquery)

    for singledict in dictarray:
        valuelist = ''
        for key, value in singledict.items():
            if settings['removequotes']:
                value = str(value).replace("'", '').replace('"', '')
            if settings['removeslashes']:
                value = str(value).replace("\\", '').replace("/", "")

            valuelist = valuelist + '\"' + value + '\",'
        querylist.append('replace into \"' + tablename + '\" values (' + valuelist[:-1] + ')')

    # print(querylist)
    sqlitemultquery(databasename, querylist, **kwargs)


# TODO: REname this and take db type input here inside of at higher level
def makesqliteinsert(table, valuelist, valuenames=None, replace=True, column_quotes=True, tablename_quotes=True):
    if replace:
        query = 'replace into '
    else:
        query = 'insert into '
    if tablename_quotes:
        query += "'" + table + "'"
    else:
        query += table

    if valuenames:
        query += ' ('
        for valuename in valuenames:
            if column_quotes:
                query += "'" + str(valuename) + "',"
            else:
                query += '{},'.format(valuename)

        query = query[:-1] + ')'

    query += ' values ('

    for value in valuelist:
        strvalue = str(value).replace("'","''")
        query += "'" + strvalue + "',"
    query = query[:-1] + ')'
    return query


def sqliteinsertsingle(database, table, valuelist, valuenames=None, replace=True, **kwargs):
    query = makesqliteinsert(table, valuelist, valuenames, replace)
    result = sqlitequery(database, query, **kwargs)

    return result


def sqlitemultquery(database, querylist, **kwargs):
    import sqlite3 as lite
    settings = {'break_on_error': False, 'quiet': False, 'timeout': 10}
    settings.update(kwargs)

    # if not settings['quiet']:
    #     print('Quiet: {} on db {}, query {}'.format(settings['quiet'], database, querylist))

        # print(querylist)

    con = lite.connect(database, timeout=settings['timeout'])
    con.text_factory = str

    messages = []
    statuses = []
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
                trace_message = traceback.format_exc()
                error_searched = status_error_from_sqlite_msg(trace_message)
                error_searched['query'] = query

                status = 1
                if not settings['quiet']:
                    print(error_searched)

                if 'log_errors' in kwargs and kwargs['log_errors'] and 'log_path' in kwargs:
                    from iiutilities.utility import log
                    log(kwargs['log_path'], error_searched['message'] + '\n\t Original message: ' + trace_message + ', query: ' + error_searched['query'])

                if settings['break_on_error']:
                    break
            else:
                dataitem = cur.fetchall()

            messages.append(message)
            statuses.append(status)
            data.append(dataitem)
        con.commit()
        # con.close()

    return {'data':data, 'messages':messages,'status':status, 'statuses':statuses}


def sqlitequery(database, query, **kwargs):
    import sqlite3 as lite
    import traceback
    import time

    settings = {'timeout':3, 'quiet':False, 'timeout_retry':0.5}
    settings.update(kwargs)

    # if not settings['quiet']:
    #     print('Quiet: {} on db {}, query {}'.format(settings['quiet'], database, query))



    # So TABLE locks will automatically retry. Database locks will not. This means we have to do our own wrapping.

    number_retries = int(settings['timeout'] / settings['timeout_retry'])
    retry = 0
    complete = False
    message = ''
    while not complete:
        try:
            con = lite.connect(database, timeout=settings['timeout'])
            con.text_factory = str

            with con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
                # cur.close()
            con.close()

        except:
            data = ''
            trace_message = traceback.format_exc()

            error_searched = status_error_from_sqlite_msg(trace_message)
            error_searched['query'] = query

            status = error_searched['status']

            if not settings['quiet']:
                # print('Error searched:')
                print(error_searched)

            if error_searched['type'] == 'lock':
                message += 'Attempt {}/{} : Lock error. '.format(retry, number_retries)

                retry += 1
                # if not settings['quiet']:
                print('Retry {}/{} : Lock Error'.format(retry, number_retries))
                if retry > number_retries:
                    complete = True
                    this_message = '{} retries exceeded. Aborting. '.format(number_retries)
                    print(this_message)
                    message += this_message
                else:
                    time.sleep(settings['timeout_retry'])
            else:
                complete = True
                if 'log_errors' in kwargs and kwargs['log_errors'] and 'log_path' in kwargs:
                    from iiutilities.utility import log
                    log(kwargs['log_path'],
                        error_searched['message'] + '\n\t Original message: ' + trace_message + ', query: ' + error_searched[
                            'query'])

                message += error_searched['message']
        else:
            complete = True
            status = 0
            message += 'Query completed successfully. '
            error_searched = {'status':status, 'message':message, 'type':None}


    return {'data':data, 'status':status, 'message':message, 'error':error_searched}


def status_error_from_sqlite_msg(trace_message):
    status = 1
    message = 'unmatched error type, text: ' + trace_message
    type = 'unknown'
    if trace_message.lower().find('lock') >= 0:
        status = 2
        message = '(2) lock error'
        type = 'lock'
    elif trace_message.lower().find('no such table') >= 0:
        status = 3
        message = '(3) table does not exist: ' + trace_message.split(':')[-1].strip()
        type = 'not_found'

    return {'status':status, 'message':message, 'type':type}


def sqlitedatumquery(database, query, **kwargs):
    datarow = sqlitequery(database, query, **kwargs)['data']
    if datarow:
        datum = datarow[0][0]
    else:
        datum = ''
    return datum


def getsinglevalue(database, table, valuename, **kwargs):
    settings = {'condition':None}
    settings.update(kwargs)
    query = makegetsinglevaluequery(table, valuename, condition=settings['condition'])
    # print(query)
    response = sqlitedatumquery(database, query, **kwargs)
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
            condition = string_condition_from_lists(conditionnames, conditionvalues)
            # print(query)
    if condition:
        query += ' where ' + condition
    return query


def sqlitedeleteitem(database, table, condition=None):
    query = makedeletesinglevaluequery(table, condition)
    sqlitequery(database, query)


def makedeletesinglevaluequery(table, condition=None):
    query = "delete from '" + table + "'"
    if condition:
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
        elif isinstance(condition, type('string')):
            query += ' where ' + condition
    return query


def readalldbrows(database, table, **kwargs):

    settings = {
        'condition':None,
        'includerowids':True,
        'combined_pragma_query':True
    }
    settings.update(kwargs)

    query = "select * from '" + table + "'"

    if 'length' in settings:
        query += ' LIMIT {} '.format(settings['length'])
    if 'start' in settings:
        query += ' OFFSET {} '.format(settings['start'])

    if settings['condition']:
        query += ' where ' + settings['condition']

    # print(query)

    if settings['combined_pragma_query']:
        queries = [query]
        queries.append('pragma table_info ( \'' + table + '\')')
        all_data = sqlitemultquery(database, queries, **settings)['data']
        data = all_data[0]
        if not data:
            return {'dict_array': [], 'keyed_dict': {}, 'indexed_key': None, 'is_primary': False}

        pragma = process_pragma(all_data[1])
    else:

        data = sqlitequery(database, query, **settings)['data']

        # print('data of length {}'.format(len(data)))
        if not data:
            return {'dict_array': [], 'keyed_dict': {}, 'indexed_key': None, 'is_primary': False}

        pragma = getpragma(database, table, **settings)

    is_primary = False
    primary_key = pragma[0]['name']
    pragma_names = []
    for pragma_item in pragma:
        # print(pragma_item)
        if pragma_item['primary']:
            primary_key = pragma_item['name']
            is_primary = True
        pragma_names.append(pragma_item['name'])


    dictarray = []
    keyed_dict = {}
    for row in data:
        dict = {}
        for datum, pragma_name in zip(row, pragma_names):
            dict[pragma_name] = datum
        dictarray.append(dict)
        keyed_dict[dict[primary_key]] = dict

    return {'dict_array':dictarray, 'keyed_dict':keyed_dict, 'indexed_key':primary_key, 'is_primary':is_primary}


def makegetallrowsquery(tablename, **kwargs):
    settings = {
        'condition':None,

    }
    settings.update(kwargs)
    query = "select * from '" + tablename + "'"

    query = "select * from '" + table + "'"

    if 'length' in settings:
        query += ' LIMIT {} '.format(settings['length'])
    if 'start' in settings:
        query += ' OFFSET {} '.format(settings['start'])

    if settings['condition']:
        query += ' where ' + settings['condition']

    return query


def makegetallrowswithpragmaquery(tablename, **kwargs):
    settings = {
        'condition':None,
    }
    settings.update(kwargs)

    table_query = "select * from '{}'".format(tablename)

    if 'length' in settings:
        table_query += ' LIMIT {} '.format(settings['length'])
    if 'start' in settings:
        table_query += ' OFFSET {} '.format(settings['start'])

    if settings['condition']:
        table_query += ' where {}'.format(settings['condition'])

    pragma_query = "pragma table_info ( '{}')".format(tablename)

    return[table_query, pragma_query]


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


def dynamicsqliteread(database_path, table, **kwargs):

    settings = {
        'start':None,
        'length':None,
        'condition':None
    }
    settings.update(kwargs)

    if settings['length'] is None and settings['start'] is None:
        dictarray = readalldbrows(database_path, table, **kwargs)['dict_array']
    elif settings['length'] is None:
        dictarray = readonedbrow(database_path, table, **kwargs)
    else:
        dictarray = readsomedbrows(database_path, table, **kwargs)

    return dictarray


def cleanlog(databasename, logname, **kwargs):
    sqlitequery(databasename, "delete from '" + logname + "' where time =''", **kwargs)


def sqliteduplicatetable(database, oldname, newname):
    # Get pragma to create table
    the_database = sqliteDatabase(database)
    schema = the_database.get_schema(oldname)

    the_data = the_database.read_table(oldname)
    the_database.create_table(newname, schema, queue=True)
    the_database.insert(newname, the_data, queue=True)
    the_database.execute_queue()


def sqlitemovetable(database, oldname, newname, **kwargs):
    sqliteduplicatetable(database, oldname, newname)
    sqlitedroptable(database, oldname)


def sqlitedeleteallrecords(database, table, **kwargs):
    sqlitequery(database, 'delete from "{}"'.format(table))


def sqlitedroptable(database, table, **kwargs):
    if 'quiet' in kwargs:
        quiet = kwargs['quiet']
    sqlitequery(database, 'drop table "{}"'.format(table), **kwargs)


def sqlitedropalltables(database, **kwargs):
    # not optimized
    existingtables = gettablenames(database)
    queries = []
    if existingtables:
        for table in existingtables:
            queries.append('drop table "{}"'.format(table))
        sqlitemultquery(database, queries, **kwargs)


def gettablesize(databasename, tablename, **kwargs):
    logsize = sqlitedatumquery(databasename, "select count(*) from '{}'".format(tablename), **kwargs)
    return logsize


def size_sqlite_table(databasename, tablename, **kwargs):
    settings = {
        'method':'count',
        'unit':'hours',          # If we specify method is time, units are in hours unless otherwise specified
        'size':1000,
        'time_column':'time',
        'delete':'oldest',
        'dry_run':False
    }
    settings.update(kwargs)
    the_log_db = sqliteDatabase(databasename, **kwargs)
    if settings['method'] == 'count':
        logsize = the_log_db.get_table_size(tablename)

        settings['size'] = int(settings['size'])
        if logsize and (logsize > settings['size']):
            log_excess = logsize - settings['size']
        else:
            log_excess = -1

    elif settings['method'] == 'timespan':
        from iiutilities.datalib import timestringtoseconds
        first_time_string = the_log_db.get_first_time_row(tablename)[settings['time_column']]
        first_time = timestringtoseconds(first_time_string)
        log_excess = 0
        time_threshold = settings['size']   # this would be seconds
        if 'unit' == 'hours':
            time_threshold = settings['size'] * 3600
        elif 'unit' == 'minutes':
            time_threshold = settings['size'] * 60
        elif 'unit' == 'days':
            time_threshold = settings['size'] * 3600 * 24

        log_data = the_log_db.read_table(tablename)
        for datum in log_data:
            string_time = datum[settings['time_column']]
            elapsed = timestringtoseconds(string_time) - first_time
            if elapsed > time_threshold:
                log_excess += 1

    query = ''
    if log_excess > 0:
        if settings['delete'] == 'oldest':
            # print('deleting {}'.format(log_excess))
            query = "delete from '{}' order by {} limit {}".format(tablename, settings['time_column'], log_excess)

        if not settings['dry_run'] and query:
            the_log_db.query(query)

    return {'excess':log_excess, 'query':query}


def getfirsttimerows(database, tablename, **kwargs):
    settings = {
        'timecolname':'time',
        'numrows':1
    }
    settings.update(kwargs)

    query = 'select * from \'' + tablename + "' order by '" + settings['timecolname'] + "' asc limit " + str(int(settings['numrows']))
    data = sqlitequery(database, query, **kwargs)['data']
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


def getlasttimerows(database, tablename, **kwargs):
    settings = {
        'timecolname': 'time',
        'numrows': 1
    }
    settings.update(kwargs)

    # print(database,tablename,timecolname,numrows)
    query = "select * from '" + tablename + "' order by \"" + settings['timecolname'] + "\" desc limit " + str(int(settings['numrows']))
    # print(query)
    data = sqlitequery(database, query, **settings)['data']
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


def getlasttimevalue(database, tablename, **kwargs):
    query = 'select time from \'' + tablename + '\' order by time desc limit 1'
    data = sqlitequery(database, query, **kwargs)['data'][0][0]
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


def readonedbrow(database, table, **kwargs):
    settings = {
        'rownumber':0,
        'condition':None
    }
    settings.update(kwargs)
    query = "select * from '" + table + "'"
    if settings['condition']:
        query += ' where ' + settings['condition']

    data = sqlitequery(database, query, **settings)['data']
    try:
        datarow = data[settings['rownumber']]

        dict = datarowtodict(database, table, datarow, **kwargs)
        dictarray = [dict]
    except:
        dictarray = []

    return dictarray


def readsomedbrows(database, table, **kwargs):

    settings = {
        'condition':None,
        'start':0,
        'length':1000,
        'reverse':False
    }
    settings.update(kwargs)

    """
    User specifies length of data, and where to start, in terms of row index

    Select statement has format:
    
    'select * from table limit LENGTH, offset OFFSET'
    
    This is pretty confusing, as if you omit the directive, the syntax is reversed: 
    
    'select * from table limit OFFSET, LENGTH
    
    This used to take a negative start argument, which would sort in descending. This was removed, as -0 is not a 
    thing and thus the last row was not readable with a reverse statement. Instead, now we pss the keyword revers.
    
    """

    if settings['reverse']:
        query = "select * from '{}' DESC LIMIT {} OFFSET {}".format(table, settings['length'], settings['start']) + str(settings['start'])
    else:
        query = "select * from '{}' LIMIT {} OFFSET {}".format(table, settings['length'], abs(settings['start'])) + str(settings['start'])
    # print(query)
    if settings['condition']:
        query += ' where ' + settings['condition']

    datarows = sqlitequery(database, query, **settings)['data']

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


def dbvntovalue(dbvn, interprettype=False, **kwargs):

    from iiutilities.datalib import parsedbvn, getvartype
    dbvndict = parsedbvn(dbvn)
    # print(dbvndict)
    # try:

    value = getsinglevalue(dbvndict['dbpath'], dbvndict['tablename'], dbvndict['valuename'], condition=dbvndict['condition'], **kwargs)
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


def test_db_read(**kwargs):

    settings = {
        'iterations':10,
        'mode':'pragma',
        'database_path':'/var/www/data/control.db',
        'tablename':'inputs'
    }
    settings.update(kwargs)

    database = sqliteDatabase(settings['database_path'])

    if settings['mode'] == 'pragma':
        import datetime

        modes = ['standard', 'combined']

        results = {}
        results['times'] = {}
        results['fails'] = {}
        results['average_times'] = {}

        for mode in modes:
            results['times'][mode] = []
            results['fails'][mode] = 0
            results['average_times'][mode] = 0

        for mode,combined_query in zip(modes, [False, True]):
            for i in range(settings['iterations']):
                start_time = datetime.datetime.now()
                try:
                    query_result = database.read_table(settings['tablename'], combined_pragma_query=combined_query)
                except:
                    print("FAIL")
                    results['fails'][mode] += 1

                elapsed_time = (datetime.datetime.now()-start_time).total_seconds()
                results['times'][mode].append(elapsed_time)

            results['average_times'][mode] = sum(results['times'][mode]) / float(len(results['times'][mode]))



        return results


"""
Mariadb implementation (experimental), designed for python3
"""

class mysqlDB(object):

    # TODO : Integrate queue functions as with sqlite.
    def __init__(self, **kwargs):

        settings = {
            'type':'mysql',
            'debug':True
        }
        settings.update(kwargs)
        self.settings = settings

        #mysql, sqlite
        setattr(self, 'db_type', settings['type'])

        required_arguments = ['user', 'password', 'database']
        for argument in required_arguments:
            if not argument in kwargs:
                print('Required argument {} was not provided'.format(argument))
                return None
            else:
                setattr(self, argument, kwargs[argument])

    def query(self, query):

        """
        TODO : Incorporate database settings into self.settings

        :param query:
        :return:
        """

        import pymysql
        import pymysql.cursors
        mariadb_connection = pymysql.connect(host='localhost', user=self.user, password=self.password, database=self.database,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        cursor = mariadb_connection.cursor()

        if self.settings['debug']:
            print(query)
        cursor.execute(query)

        data = []
        for row in cursor:
            data.append(row)

        # try:
        # cursor.execute("INSERT INTO employees (first_name,last_name) VALUES (%s,%s)", ('Maria', 'DB'))
        # except mariadb.Error as error:
        #     print("Error: {}".format(error))
        #     return_dict = {'status':1, 'error':format(error), 'data':None}
        #
        # else:
        return_dict = {'status':0, 'error':None, 'data':data}
        mariadb_connection.commit()
        mariadb_connection.close()
        return return_dict

    def get_table_names(self):
        results = self.query('SHOW TABLES')['data']
        tablenames = []
        for result in results:
            for key in result:
                tablenames.append(result[key])
        return tablenames

    def read_table(self, tablename, **kwargs):

        """
        TODO: Work on self.settings and condition here. Should be same in both sqlite and mysql for compatibility

        :param tablename:
        :param kwargs:
        :return:
        """
        if 'condition' not in kwargs and 'condition' in self.settings:
            del self.settings['condition']
        self.settings.update(kwargs)

        query = 'select * from {}'.format(tablename)
        if 'condition' in kwargs:
            query += ' where ' + kwargs['condition']

        result = self.query(query)['data']
        return result

    def insert(self, tablename, insert, **kwargs):
        settings = {
            'replace':True,
            'queue':False
        }
        settings.update(kwargs)

        if 'quiet' in kwargs:
            self.settings['quiet']=settings['quiet']

        # Insert can be single insert or list (or falsy to insert defaults)
        if not insert:
            queries = ["insert into '" + tablename + "'default values"]
        else:
            if not (isinstance(insert, list)):
                insert_list = [insert]
            else:
                insert_list = insert

            queries = []
            for insert in insert_list:
                query = make_insert_from_dict(tablename, insert, db_type=self.db_type)
                queries.append(query)

        if settings['queue']:
            self.queue_queries(queries)
        else:
            self.queries(queries)

        return queries

    # TODO: Make this an actual mult query
    def queries(self, queries):
        results = []
        for query in queries:
            print(query)
            result = self.query(query)
            results.append(result)
        return results

    def create_table(self, tablename, table_schema):
        query = "create table {} ( ".format(tablename)
        for index, item in enumerate(table_schema):
            query += '{} {}'.format(item['name'], item['type'])
            if index < len(table_schema) - 1:
                query += ', '

        for index, item in enumerate(table_schema):
            if 'primary' in item and item['primary']:
                query += ', primary key ({})'.format(item['name'])

        query += ')'

        self.query(query)

    def drop_table(self, name, queue=False, **kwargs):

        self.settings.update(kwargs)
        drop_query = "drop table '{}'".format(name)
        if queue:
            self.queue_queries([drop_query])
        else:
            self.query(drop_query)

    def execute_queue(self, clear_queue=True, **kwargs):
        self.settings.update(kwargs)
        if self.queued_queries:
            self.queries(self.queued_queries)
        if clear_queue:
            self.clear_queue()

    def clear_queue(self):
        self.queued_queries = []

    def queue_query(self, query):
        self.queued_queries.append(query)

    def queue_queries(self, queries):
        self.queued_queries.extend(queries)

    # def query(self, query, **kwargs):
    #     self.settings.update(kwargs)
    #     result = sqlitequery(self.path, query, **self.settings)
    #     return result
    #
    # def queries(self, queries):
    #     result = sqlitemultquery(self.path, queries, **self.settings)
    #     return result