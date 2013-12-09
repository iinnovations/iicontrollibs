#!/usr/bin/env python

from git import *
repo = Repo("/usr/lib/iicontrollibs")
origin=repo.remotes.origin
origin.pull('master')
print('Update Complete')
