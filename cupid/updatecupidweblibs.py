#!/usr/bin/python

from git import *
repo = Repo("/var/www")
origin=repo.remotes.origin
origin.pull('master')
print('Update Complete')
