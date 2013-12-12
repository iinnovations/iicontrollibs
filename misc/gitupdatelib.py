#!/usr/bin/python

# do this stuff to access the pilib for sqlite
import os,sys,inspect

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0,top_folder)

from cupid.pilib import * 
from git import *

defaultrepo = "/usr/lib/iicontrollibs"
versiondb = "/var/www/data/systemdata.db"
versiontablename="versions"
librarydict={'/usr/lib/iicontrollibs':'iicontrollibs','/var/www':'cupidweblibs'}

def getrepoinfo(repodirectory):
    repoinfo={}
    repo = Repo(repodirectory)
    repoinfo['headcommit']=repo.head.commit
    repoinfo['origin']=repo.remotes.origin
    repoinfo['headcommithexsha']=repo.head.commit.hexsha
    repoinfo['headcommitdate']=repo.head.commit.committed_date
    repoinfo['headcommitmsg']=repo.head.commit.message
    repoinfo['name']=librarydict[repodirectory]
    return repoinfo

def updateversion(repodirectory):
    repoinfo=getrepoinfo(repodirectory)
    addversionentry(versiondb,versiontablename,repoinfo)

def pullrepo(repodirectory,originname):
    repo = Repo(repodirectory)
    origin=repo.remotes.origin
    gitresponse=origin.pull(originname)
    return gitresponse

def addversionentry(database,table,entrydict):
    sqliteinsertsingle(database,table,[entrydict['name'],entrydict['headcommithexsha'],gettimestring(entrydict['headcommitdate']),gettimestring()])

def updateiicontrollibs():
    repo='/usr/lib/iicontrollibs'
    originname='master'
    pullrepo(repo,originname)
    updateversion(repo)
    print('update complete')

def updatecupidweblibs():
    repo='/var/www'
    originname='master'
    pullrepo(repo,originname)
    updateversion(repo)
    print('update complete')
    
if __name__=="__main__":
    #pullrepo(defaultrepo)
    repoinfo=getrepoinfo(defaultrepo) 
    #print(repoinfo)
    print('blurg')
    


