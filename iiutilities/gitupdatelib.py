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

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def getrepoinfo(repodirectory):
    from git import Repo
    repoinfo = {}
    repo = Repo(repodirectory)
    repoinfo['headcommit'] = repo.head.commit
    repoinfo['origin'] = repo.remotes.origin
    repoinfo['headcommithexsha'] = repo.head.commit.hexsha
    repoinfo['headcommitdate'] = repo.head.commit.committed_date
    repoinfo['headcommitmsg'] = repo.head.commit.message
    repoinfo['repo'] = repo
    return repoinfo


def updaterepoversion(repodirectory, versiondb, versiontablename='versions'):
    repoinfo = getrepoinfo(repodirectory)
    addversionentry(versiondb, versiontablename, repoinfo)


def pullrepo(repodirectory, originname):
    from git import Repo
    repo = Repo(repodirectory)
    origin = repo.remotes.origin
    gitresponse = origin.pull(originname)
    return gitresponse


def stashrepo(repodirectory, originname):
    gitresponse = 'not implemented yet'
    return gitresponse


def addversionentry(database_path, tablename, entrydict):
    import iiutilities.dblib as dblib
    from iiutilities.datalib import gettimestring
    versions_db = dblib.sqliteDatabase(database_path)
    tablenames = versions_db.get_table_names()
    if not tablename in tablenames:
        versions_schema = dblib.sqliteTableSchema([
            {'name': 'item', 'primary': True},
            {'name': 'version'},
            {'name': 'versiontime'},
            {'name': 'updatetime'}
        ])
        versions_db.create_table(tablename, versions_schema)
    insert = {'item':entrydict['repo'],
              'version':entrydict['headcommithexsha'],
              'versiontime':gettimestring(entrydict['headcommitdate']),
              'updatetime': gettimestring()
              }
    versions_db.insert(tablename, insert)

if __name__ == "__main__":

    print('blurg')
    


