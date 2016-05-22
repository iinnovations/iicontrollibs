#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# do this stuff to access the pilib for sqlite
import os, sys, inspect
from time import sleep

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def runhamachicheck():
    import cupid.netfun as netfun
    import socket
    hostname = socket.gethostname()

    pingtime = netfun.runping('25.215.49.105')[0]

    if ( pingtime > 1000 or pingtime == 0 ):
        from cupid.utilities import gmail
        message = hostname + ' is restarting its Hamachi daemon. '
        subject = 'Keeping Hamachi online!'
        email = 'colin.reese@gmail.com'
        actionmail = gmail(message=message, subject=subject, recipient=email)
        actionmail.send()

        netfun.killhamachi()
        netfun.restarthamachi()


def generatehamachipage(hamachidata=None, path=None):
    from cupid.netfun import gethamachidata
    from datalib import parseoptions

    if not hamachidata:
        hamachidata = gethamachidata()

    if path:
        file = open(path, 'w')
        htmlstring = (
            '<!DOCTYPE html>' +
            '<html>' +
            '<head>' +
            '<title>Hamachi Remotes Home</title>' +
            '<meta name="viewport" content="width=device-width, initial-scale=1">' +
            '<link rel="stylesheet" href="jqm/themes/base.css" />' +

            '<link rel="stylesheet" href="jqm/themes/jquery.mobile.icons.min.css" />' +
            '<link rel="stylesheet" href="jqm/jquery.mobile.custom.structure.min.css" />' +

            '<!--jQuery Mobile is 1.4.5-->' +
            '<script src="js/jquery-1.11.1.js"></script>' +
            '<script src="jqm/jquery.mobile.custom.js"></script>' +

            '<style>' +
                '.online {' +
                    'background-color:#bbffbb' +
                '}' +
                '.offline {' +
                    'background-color:#ffbbbb' +
                '}' +
            '</style>' +
            '</head>' +

            '<body>' +
            '<div data-role="page" id="demo-page" class="my-page" data-theme="d">' +
                '<div role="main" class="ui-content">')

        file.write(htmlstring)
    for network in hamachidata:
        if path:
            htmlstring = ('<ul data-role="listview" data-inset="true">' +
                    '<li data-role="list-divider">' + network['name'] + ' : ' + network['id'] + '</li>')

        for client in network['clientlist']:
            # print(client['name'] + ' : ' + client['hamachiip'])
            if path:
                htmlstring += '<li>'
                htmlstring += '<fieldset class="ui-grid-a"><div class="ui-block-a" style="width:50%">'
                # htmlstring += client['name'] + ' : ' + client['hamachiip']
                htmlstring += '<a href="http://' +  client['hamachiip'] +'">' + client['name'] + '</a> : ' + client['hamachiip']

                options = parseoptions(client['options'])

                htmlstring+='</div>'

                if client['onlinestatus']:
                    htmlstring += '<div class="online" style="width:60px; float:right; text-align:center; border-radius:0.4em; border-width:1px; border-style:solid; border-color:#333333">Online</div>'
                else:
                    htmlstring += '<div class="offline" style="width:60px; float:right; text-align:center; border-radius:0.4em; border-width:1px; border-style:solid; border-color:#333333">Offline</div>'

                if 'monitor' in options:
                    if options['monitor'] == '1':
                        htmlstring += '<div class="online" style="width:70px; float:right; text-align:center; border-radius:0.4em; border-width:1px; border-style:solid; border-color:#333333; margin-right:10px">Daemon</div>'

                htmlstring += '</fieldset></li>\n'

        if path:
            htmlstring+='</ul>'
            file.write(htmlstring)

    if path:
        htmlstring = '</div></div>\n'
        file.write(htmlstring)
        file.close()


if __name__=="__main__":
        runhamachicheck()

