#!/usr/bin/python

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

netstats_dbpath = '/var/www/html/netstats/data/netstats.db'
access_dbpath = '/var/www/html/netstats/data/access.db'
salt = 'somesaltystuff'

from iiutilities import dblib

netspeed_schema = dblib.sqliteTableSchema([
    {'name':'time', 'primary':True},
    {'name':'download', 'type':'real'},
    {'name':'upload', 'type':'real'},
    {'name':'ping', 'type':'real'}
])

def init_netstats_database(path=netstats_dbpath):
    from iiutilities import dblib

    the_database = dblib.sqliteDatabase(path)
    the_database.create_table('wired',netspeed_schema)
    the_database.create_table('wireless',netspeed_schema)


def init_access_database(path=access_dbpath):
    from iiutilities import dblib

    the_database = dblib.sqliteDatabase(path)
    schema = dblib.sqliteTableSchema([
        {'name':'time', 'primary':True},
        {'name':'full'},
        {'name':'remote_address'},
        {'name':'user'},
        {'name':'request_time'},
        {'name':'full_request'},
        {'name':'request'},
        {'name':'status'},
        {'name':'body_bytes'},
        {'name':'origin_url'},
        {'name':'host'},
        {'name':'referer'},
        {'name':'http_fwd'},
        {'name':'user_agent'}
    ])
    the_database.create_table('access_log',schema)


def get_and_log_netstats(path=netstats_dbpath, **kwargs):
    import speedtest
    from iiutilities import dblib
    from iiutilities.datalib import gettimestring

    results = speedtest.call_tester(**kwargs)

    the_database = dblib.sqliteDatabase(path)
    download=round(results.download/1000000, 2)
    upload=round(results.upload/1000000, 2)

    if 'wired' not in the_database.get_table_names():
        the_database.create_table('wired', netspeed_schema)
    the_database.insert('wired', {'time':gettimestring(), 'download':download,
                                  'upload':upload, 'ping':round(results.ping, 2)})
    # print(download,upload)


def parse_and_table_nginx_access_log(logpath='/var/log/nginx/access.log'):
    requests = parse_nginx_log(logpath)
    from iiutilities import dblib

    access_db = dblib.sqliteDatabase(access_dbpath)
    for request in requests:
        access_db.insert('access_log',request, queue=True)

    # print(len(access_db.queued_queries))
    # print(access_db.queued_queries)
    access_db.execute_queue()


def parse_nginx_log(logpath='/var/log/nginx/access.log'):
    log_file = open(logpath, 'r')
    log_lines = log_file.readlines()

    requests = []
    for line in log_lines:
        # parsed_return = parse_log_entry(line)
        parsed_return = parse_json_log_entry(line)
        if parsed_return['status']:
            print('ERROR')
            print(parsed_return['message'])

        else:
            requests.append(parsed_return['entry'])

    # requests = [parse_log_entry(line) for line in log_lines]
    return requests


def month_word_to_number(word):

    if word in ['jan', 'Jan']:
        number = '01'
    elif word in ['feb', 'Feb']:
        number = '02'
    elif word in ['mar', 'Mar']:
        number = '03'
    elif word in ['apr', 'Apr']:
        number = '04'
    elif word in ['may', 'May']:
        number = '05'
    elif word in ['jun', 'Jun']:
        number = '06'
    elif word in ['jul', 'Jul']:
        number = '07'
    elif word in ['aug', 'Aug']:
        number = '08'
    elif word in ['sep', 'Sep']:
        number = '09'
    elif word in ['oct', 'Oct']:
        number = '10'
    elif word in ['nov', 'Nov']:
        number = '11'
    elif word in ['dec', 'Dec']:
        number = '12'
    else:
        number = '00'
    return number


def parse_nginx_time(nginx_time):
    """
    IN: 22/Jan/2017:06:43:40 -0800
    OUT: 2017-01-25 16:56:45
    """
    date = nginx_time.split('/')[0]
    word_month = nginx_time.split('/')[1]
    month = month_word_to_number(word_month)
    year = nginx_time.split('/')[2][0:4]
    hour = nginx_time.split(':')[1]
    minute = nginx_time.split(':')[2]
    second = nginx_time.split(':')[3][0:2]

    return '-'.join([year,month,date]) + ' ' + ':'.join([hour,minute,second])


def parse_json_entry(entry):
    import json
    obj = json.loads('{' + entry + '}')
    # print(obj)

    return obj


def parse_json_log_entry(logentry):

    try:
        entry_dict = parse_json_entry(logentry)
        entry_dict['time'] = parse_nginx_time(entry_dict['time'])
    except:
        import traceback

        message = 'ERROR WITH ENTRY: \n'
        message += logentry + '\n'
        message += traceback.format_exc()
        return_dict = {'entry':{}, 'message':message, 'status':1}

    else:
        return_dict = {'entry':entry_dict, 'message':'seems to have worked ok', 'status':0}

    return return_dict


def parse_log_entry(logentry):
    # print(logentry)
    entry_dict = {'full':logentry}
    try:
        entry_dict['address'] = logentry.split('-')[0].strip()
        entry_dict['user'] = logentry.split('-')[1].strip()

        remaining_entry = '-'.join(logentry.split('-')[2:])

        # Need to convert this
        entry_dict['time'] = parse_nginx_time(remaining_entry.split(']')[0].strip()[1:])

        remaining_entry = ']'.join(remaining_entry.split(']')[1:]).strip()
        entry_dict['request'] = remaining_entry.split('"')[1].strip()

        remaining_entry = '"'.join(remaining_entry.split('"')[2:]).strip()
        entry_dict['status'] = remaining_entry.split(' ')[0].strip()
        entry_dict['bytes'] = remaining_entry.split(' ')[1].strip()

        remaining_entry = ' '.join(remaining_entry.split(' ')[2:])

        entry_dict['origin_url'] = remaining_entry.split('"')[-4]
        entry_dict['user_agent'] = remaining_entry.split('"')[-2]
    except:
        import traceback

        message = 'ERROR WITH ENTRY: \n'
        message += logentry + '\n'
        message += traceback.format_exc()
        return_dict = {'entry':{}, 'message':message, 'status':1}

    else:
        return_dict = {'entry':entry_dict, 'message':'seems to have worked ok', 'status':0}

    return return_dict


def analyze_access_entry(entry):

    if entry['remote_address'].find('192.168.1') >= 0:
        entry['local'] = True
    else:
        entry['local'] = False

    # Parse address into TLD
    entry['domain'] = entry['host']
    if entry['domain'].find('/') >= 0:
        entry['domain'] = entry['domain'].split('/')[0]

    if entry['domain'].find('www.') >=0:
        entry['domain'] = entry['domain'].split('www.')[1]


def analyze_and_histo_access_db(dbpath=access_dbpath):
    from iiutilities import dblib
    from iiutilities import datalib

    tablename = 'access_log'
    access_db = dblib.sqliteDatabase(dbpath)
    access_db_tablenames = access_db.get_table_names()
    access_records = access_db.read_table(tablename)

    access_meta = {'total_hits':{}, 'remote_hits':{}, 'hourly_hits':{}, 'not_found':[], 'dbpath':dbpath, 'tablename':tablename}
    for record in access_records:
        analyze_access_entry(record)
        if not record['domain']:
            pass
            # print('no domain for entry')
            # print(record)
        if record['domain'] in access_meta['total_hits']:
            access_meta['total_hits'][record['domain']]['times'].append(record['time'])
        else:
            access_meta['total_hits'][record['domain']] = {'times':[record['time']]}

        if not record['local']:
            if record['domain'] in access_meta['remote_hits']:
                access_meta['remote_hits'][record['domain']]['times'].append(record['time'])
            else:
                access_meta['remote_hits'][record['domain']] = {'times':[record['time']]}

        if record['status'] == '404':
            access_meta['not_found'].append({'url':record['full_request'], 'time':record['time']})


    # NOw process time resolved data into tables
    # this should be better iterate (DRY) but this works
    for domain_name, domain_data in access_meta['total_hits'].items():

        domain_data['times'].sort()

        # Find first time
        first_time = datalib.timestringtoseconds(domain_data['times'][0])

        # Go back to last incremental hour
        first_hour_time_seconds = first_time - first_time % 3600

        # Find last hour (this actually just means that all are within the hour following this)
        last_time = datalib.timestringtoseconds(domain_data['times'][-1])

        last_hour_time_seconds = last_time - last_time % 3600

        bin_times = []
        bin_values = []
        num_bins = int(last_hour_time_seconds - first_hour_time_seconds) / 3600 + 1
        for i in range(num_bins):
            bin_times.append(first_hour_time_seconds + i * 3600)
            bin_values.append(0)

        for time in domain_data['times']:
            time_seconds = datalib.timestringtoseconds(time)
            for index, bin_time in enumerate(bin_times):
                if index == num_bins - 1 or time_seconds < bin_times[index+1]:
                    bin_values[index] += 1
                    break

        domain_data['histo_data']={}

        for bin_time, bin_value in zip(bin_times, bin_values):
            # Put time in middle of hour
            domain_data['histo_data'][datalib.gettimestring(bin_time + 1800)] = bin_value

    for domain_name, domain_data in access_meta['remote_hits'].items():

        domain_data['times'].sort()

        # Find first time
        first_time = datalib.timestringtoseconds(domain_data['times'][0])

        # Go back to last incremental hour
        first_hour_time_seconds = first_time - first_time % 3600

        # Find last hour (this actually just means that all are within the hour following this)
        last_time = datalib.timestringtoseconds(domain_data['times'][-1])

        last_hour_time_seconds = last_time - last_time % 3600

        bin_times = []
        bin_values = []
        num_bins = int(last_hour_time_seconds - first_hour_time_seconds) / 3600 + 1
        for i in range(num_bins):
            bin_times.append(first_hour_time_seconds + i * 3600)
            bin_values.append(0)

        for time in domain_data['times']:
            time_seconds = datalib.timestringtoseconds(time)
            for index, bin_time in enumerate(bin_times):
                if index == num_bins - 1 or time_seconds < bin_times[index+1]:
                    bin_values[index] += 1
                    break

        domain_data['histo_data']={}

        for bin_time, bin_value in zip(bin_times, bin_values):
            # Put time in middle of hour
            domain_data['histo_data'][datalib.gettimestring(bin_time + 1800)] = bin_value

    if access_db.queued_queries:
        access_db.execute_queue()

    return access_meta


def table_access_histo_data(access_meta):
    from iiutilities import dblib
    access_db = dblib.sqliteDatabase(access_meta['dbpath'])
    access_db_tablenames = access_db.get_table_names()

    not_found_schema = dblib.sqliteTableSchema([
        {'name': 'time', 'primary': True},
        {'name': 'url'}
    ])
    access_db.create_table('404s', not_found_schema)
    for nf in access_meta['not_found']:
        access_db.insert('404s', nf)
    access_db.execute_queue()

    histo_schema = dblib.sqliteTableSchema([
        {'name': 'time', 'primary': True},
        {'name': 'count', 'type': 'integer'}
    ])

    for domain_name, domain_data in access_meta['remote_hits'].items():
        tablename = domain_name + '_remotehisto'
        if tablename not in access_db_tablenames:
            access_db.create_table(tablename, histo_schema, queue=True)
        for histo_time, histo_count in domain_data['histo_data'].items():
            access_db.insert(tablename, {'time': histo_time, 'count': histo_count}, queue=True)

    for domain_name, domain_data in access_meta['total_hits'].items():
        tablename = domain_name + '_totalhisto'
        if tablename not in access_db_tablenames:
            access_db.create_table(tablename, histo_schema, queue=True)
        for histo_time, histo_count in domain_data['histo_data'].items():
            access_db.insert(tablename, {'time': histo_time, 'count': histo_count}, queue=True)

    if access_db.queued_queries:
        access_db.execute_queue()


def create_access_histo_metadata(access_meta):

    # Should have an option here to pull this from the database. Currently it directly follows analysis

    from iiutilities import datalib
    # So here what we are doing is creating metadata on what has occurred in previous hours, etc.
    current_time = datalib.timestring_to_struct()

    metadata_remote = {}
    # print(access_meta['remote_hits'])
    for domain_name, domain_data in access_meta['remote_hits'].items():
        metadata_remote[domain_name] = {'this_day':0, 'prev_day':0, 'this_hour':0, 'prev_hour':0}
        for histo_time, histo_count in domain_data['histo_data'].items():
            histo_time_struct = datalib.timestring_to_struct(histo_time)

            # Technicaly only one correct hourly atm, but in future we could further divide
            if histo_time_struct.tm_mday == current_time.tm_mday:
                metadata_remote[domain_name]['this_day'] += histo_count
                if histo_time_struct.tm_hour == current_time.tm_hour:
                    metadata_remote[domain_name]['this_hour'] += histo_count

                elif histo_time_struct.tm_hour == current_time.tm_hour - 1:
                    metadata_remote[domain_name]['prev_hour'] += histo_count

            elif histo_time_struct.tm_mday == current_time.tm_mday - 1:
                metadata_remote[domain_name]['prev_day'] += histo_count

    return {'metadata_remote':metadata_remote}


def table_access_histo_metadata(metadata, dbpath=access_dbpath):
    from iiutilities import dblib
    metadata_schema = dblib.sqliteTableSchema([
        {'name':'domain', 'primary':True},
        {'name':'this_hour'},
        {'name':'prev_hour'},
        {'name':'this_day'},
        {'name':'prev_day'}
    ])
    access_db = dblib.sqliteDatabase(dbpath)
    access_db_tablenames = access_db.get_table_names()

    """
    metadata = {
        'metadata_remote': {
            'somedomain.com': {
                'prev_day':integer,
                'prev_hou':integer,
                'this_day':integer,
                'this_hour':integer
            }
            'someotherdomain.com': {
                'prev_day':integer,
                'prev_hou':integer,
                'this_day':integer,
                'this_hour':integer
            }
        }
        'metadata_total': {
            'somedomain.com': {
                'prev_day':integer,
                'prev_hou':integer,
                'this_day':integer,
                'this_hour':integer
            }
            'someotherdomain.com': {
                'prev_day':integer,
                'prev_hou':integer,
                'this_day':integer,
                'this_hour':integer
            }
        }
    }

    """
    for metadata_type, metadata_data in metadata.items():
        tablename = metadata_type
        if tablename not in access_db_tablenames:
            access_db.create_table(tablename, metadata_schema, queue=True)

        for domain_name, domain_data in metadata_data.items():
            domain_data['domain'] = domain_name
            access_db.insert(tablename, domain_data, queue=True)

    if access_db.queued_queries:
        # print('THERE ARE QUERIES')
        access_db.execute_queue()
    else:
        # print('there are no queries?')
        pass


def analyze_histo_and_table_access_db(dbpath=access_dbpath):

    access_meta = analyze_and_histo_access_db(dbpath)
    table_access_histo_data(access_meta)
    metadata = create_access_histo_metadata(access_meta)
    table_access_histo_metadata(metadata)
    print('*** metadata')
    print(metadata)


if __name__ == "__main__":
    print('Testing netstats ...')
    get_and_log_netstats(netstats_dbpath)
    print('Netstats complete')
    print('Trimming/sorting entries ...')

    from iiutilities.utility import split_and_trim_db_by_date
    rotate_result = split_and_trim_db_by_date(netstats_dbpath)

    # Could run a meta on netstats here, using modified results and current results.

    print('NETSTATS', rotate_result)

    print('parsing nginx access logs ...')
    parse_and_table_nginx_access_log()
    print('done parsing logs')

    print('Trimming and sorting entries')
    rotate_result = split_and_trim_db_by_date(access_dbpath)
    print('ACCESS', rotate_result)

    print('Trimming complete.')
    print('Deleting empty tables ...')

    access_db = dblib.sqliteDatabase(access_dbpath)
    access_db.drop_empty_tables()

    modified_dbs = rotate_result['modified_dbs']
    modified_dbs.append(access_dbpath)

    for db in modified_dbs:

        print(db)
        access_meta = analyze_and_histo_access_db(db)
        table_access_histo_data(access_meta)
        metadata = create_access_histo_metadata(access_meta)
        table_access_histo_metadata(metadata, dbpath=db)



