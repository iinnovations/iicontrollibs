#!/usr/bin/python

from git import *
import os
#os.system("echo 'stuff' > /home/pi/Desktop/output.txt")
repo = Repo("/usr/lib/iicontrollibs")
origin=repo.remotes.origin
origin.pull('master')
print('Update Complete')
os.system("echo 'stuff' > /home/pi/Desktop/output.txt")
