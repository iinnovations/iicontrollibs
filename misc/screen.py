#!/usr/bin/env python


# __author__ = "Colin Reese"
# __copyright__ = "Copyright 2014, Interface Innovations"
# __credits__ = ["Colin Reese"]
# __license__ = "Apache 2.0"
# __version__ = "1.0"
# __maintainer__ = "Colin Reese"
# __email__ = "support@interfaceinnovations.org"
# __status__ = "Development"

def setscreen(mode,debug=False):
    import subprocess
    if mode ==  'compon':
        subprocess.call(['tvservice', '-sdtvon="NTSC 4:3"'])
        subprocess.call(['startx', '&'])
        if debug:
            print('screen enabled')
        return

    elif mode == 'hdmion': 
        subprocess.call(['tvservice', '-o'])
        subprocess.call(['tvservice', '-p'])
        subprocess.call(['startx', '&'])
        if debug:
            print('hdmi enabled')
        return

    elif mode == 'off':
        subprocess.call(['tvservice', '-o'])
        if debug:
            print('screens disabled')
        return
    print("usage: setscreen(mode [,debug]), mode='compon','hdmion','off'")

if __name__=='__main__':
    import sys,getopt
    opt,args = getopt.getopt(sys.argv[1:],'')
    print(args)
    if len(args) > 1:
        if args[1] in ['True','true','T','t']:
            setscreen(args[0],True)
        else:
            setscreen(args[0])
    elif len(args) > 0:
        setscreen(args[0])
    else:
        print("usage: setscreen(mode[,debug]), mode='compon','hdmion','off'")
  
