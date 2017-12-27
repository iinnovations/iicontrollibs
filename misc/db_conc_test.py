#!/usr/bin/python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2016, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'

# This script handles owfs read functions

import os, inspect, sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


from cupid import pilib
from iiutilities import dblib


def test_conc(**kwargs):

    settings = {
        'database':dblib.sqliteDatabase(pilib.dirs.dbs.system),
        'tablename':'logconfig',
        'sessions':5,
        'timeout':0,
        'reads':1000
    }
    # settings.update(kwargs)

    import threading
    from time import sleep

    def read_table(i):

        results = {'name':threading.currentThread().getName(), 'success':0,'fail':0}

        for iteration in range(settings['reads']):
            """thread worker function"""
            thread_name = threading.currentThread().getName()
            print(thread_name + ' reading table ' + settings['tablename'])
            try:
                # print('something . ')
                the_table = settings['database'].read_table_smart(settings['tablename'])
            except:
                print('Worker ' + thread_name + ' FAIL')
                results['fail'] += 1
            else:
                results['success'] += 1

            wait_time = 0.1 + i*0.01
            # print('sleeping ' + str(wait_time))
            sleep(wait_time)

        print(results)
        return

    for i in range(settings['sessions']):
        threading.Thread(target=read_table, args=(i,), name='Worker ' + str(i)).start()


if __name__ == "__main__":
    test_conc()