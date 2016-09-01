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

from git import *

from cupid.pilib import dirs

iicontrollibsrepodir = '/usr/lib/iicontrollibs'
cupidweblibrepodir = '/var/www'
defaultrepo = iicontrollibsrepodir
versiondb = dirs.dbs.system
versiontablename = "versions"
librarydict = {iicontrollibsrepodir: 'iicontrollibs', cupidweblibrepodir: 'cupidweblibs'}


def getrepoinfo(repodirectory):
    repoinfo = {}
    repo = Repo(repodirectory)
    repoinfo['headcommit'] = repo.head.commit
    repoinfo['origin'] = repo.remotes.origin
    repoinfo['headcommithexsha'] = repo.head.commit.hexsha
    repoinfo['headcommitdate'] = repo.head.commit.committed_date
    repoinfo['headcommitmsg'] = repo.head.commit.message
    repoinfo['name'] = librarydict[repodirectory]
    return repoinfo


def updategitversions():
    updaterepoversion(iicontrollibsrepodir)
    updaterepoversion(cupidweblibrepodir)


def updaterepoversion(repodirectory):
    repoinfo = getrepoinfo(repodirectory)
    addversionentry(versiondb, versiontablename, repoinfo)


def pullrepo(repodirectory, originname):
    repo = Repo(repodirectory)
    origin = repo.remotes.origin
    gitresponse = origin.pull(originname)
    return gitresponse


def stashrepo(repodirectory, originname):
    gitresponse = 'not implemented yet'
    return gitresponse


def addversionentry(database, table, entrydict):
    from iiutilities.dblib import sqliteinsertsingle
    from iiutilities.datalib import gettimestring
    sqliteinsertsingle(database, table,
                       [entrydict['name'], entrydict['headcommithexsha'], gettimestring(entrydict['headcommitdate']),
                        gettimestring()])


def updateiicontrollibs(stash=False):
    repodirectory = iicontrollibsrepodir
    originname = 'master'
    if stash:
        stashrepo(repodirectory, originname)
    pullrepo(repodirectory, originname)
    updaterepoversion(repodirectory)
    print('update complete')


def updatecupidweblib(stash=False):
    repodirectory = cupidweblibrepodir
    originname = 'master'
    if stash:
        stashrepo(repodirectory,originname)
    pullrepo(repodirectory, originname)
    updaterepoversion(repodirectory)
    print('update complete')


if __name__ == "__main__":
    updaterepoversion(iicontrollibsrepodir)
    updaterepoversion(cupidweblibrepodir)
    print('blurg')
    


