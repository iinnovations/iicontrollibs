#!/usr/bin/python

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]

if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

if __name__ == '__main__':
    from iiutilities.netfun import restart_uwsgi
    directories = ['/usr/lib/iicontrollibs/inventory/', '/usr/lib/iicontrollibs/netstats/', '/usr/lib/ivlbotlib/wsgi/']
    print('running restart with directories {}'.format(directories))

    # print('running restart with directory ' + directory)
    # restart_uwsgi(directory, quiet=True, killall=True)
    import subprocess 
    try:
       print('doing nothing')
       #result = subprocess.check_output(['/usr/bin/pkill','uwsgi'])
    except:
       print('there appears to be an error')
    else:
       print('uwsgi processes terminated')
    
    for directory in directories:
        restart_uwsgi(directory, quiet=True)

   
    #restart_uwsgi('/usr/lib/iicontrollibs/netstats/', quiet=True)
    #restart_uwsgi('/usr/lib/ivlbotlib/wsgi/', quiet=True)

