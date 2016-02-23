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


def runcheck():
    import cupid.netfun as netfun

    pingtime = netfun.runping('25.37.18.7')[0]

    if ( pingtime > 1000 or pingtime == 0 ):
        print('bad things')
        from cupid.pilib import gmail
        message = 'Libation is restarting its Hamachi daemon. '
        subject = 'Keeping Hamachi online!'
        email = 'colin.reese@gmail.com'
        actionmail = gmail(message=message, subject=subject, recipient=email)
        actionmail.send()

        netfun.killhamachi()
        netfun.restarthamachi()
    else:
        print(pingtime)


def generatehamachipage(path=None):
    from cupid.netfun import gethamachidata
    networks, clients = gethamachidata()
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
    for network, clientlist in zip(networks, clients):
        if path:
            htmlstring = ('<ul data-role="listview" data-inset="true">' +
                    '<li data-role="list-divider">' + network['name'] + ' : ' + network['networkid'] + '</li>')

        for client in clientlist:
            # print(client['name'] + ' : ' + client['hamachiip'])
            if path:
                htmlstring += '<li>'
                htmlstring += '<fieldset class="ui-grid-a"><div class="ui-block-a" style="width:50%">'
                #htmlstring += client['name'] + ' : ' + client['hamachiip']
                htmlstring += '<a href="https://' +  client['hamachiip'] +'">' + client['name'] + '</a> : ' + client['hamachiip']

                if client['onlinestatus'] == 'online':
                    htmlstring += '</div><div class="online" style="width:60px; float:right; text-align:center; border-radius:0.4em; border-width:1px; border-style:solid; border-color:#333333">Online</div>'
                else:
                    htmlstring += '</div><div class="offline" style="width:60px; float:right; text-align:center; border-radius:0.4em; border-width:1px; border-style:solid; border-color:#333333">Offline</div>'

                htmlstring += '</fieldset></li>\n'

        if path:
            htmlstring+='</ul>'
            file.write(htmlstring)

    if path:
        htmlstring = '</div></div>\n'
        file.write(htmlstring)
        file.close()
if __name__=="__main__":
        runcheck()

