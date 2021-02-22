#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def runboot():
    import subprocess
    from time import sleep

    import pilib
    import spilights
    from iiutilities import utility, dblib, datalib

    try:
        pilib.set_all_wal(False)
    except:
        print('error setting wal mode')

    interfaces = pilib.dbs.control.read_table('interfaces')

    # Clear out status bits, if for no other reason to see the LEDs come on
    for statusvalue in ['systemstatusstatus', 'hamachistatus', 'picontrolstatus', 'updateiostatus', 'serialhandlerstatus' ]:
        dblib.setsinglevalue(pilib.dirs.dbs.system, 'systemstatus', statusvalue, 0)

    systemstatus = dblib.readonedbrow(pilib.dirs.dbs.system, 'systemstatus')[0]


    # Queue a message indicating we are rebooting
    # TODO: Make this an actions option, or put it somewhere.
    # try:
    import socket
    hostname = socket.gethostname()

    message = 'CuPID is booting:\r\n\r\n'
    notifications_email = 'cupid_status@interfaceinnovations.org'
    subject = 'CuPID : ' + hostname + ' : booting'
    notification_database = pilib.cupidDatabase(pilib.dirs.dbs.notifications)
    system_database = pilib.cupidDatabase(pilib.dirs.dbs.system)

    currenttime = datalib.gettimestring()
    notification_database.insert('queued',
                                 {'type': 'email', 'message': message,
                                  'options': 'email:' + notifications_email + ',subject:' + subject,
                                  'queuedtime': currenttime})
    system_database.set_single_value('notifications', 'lastnotification', currenttime, condition="item='boot'")

    # except Exception as e:
    #     error_message = 'EXCEPTION in notification: {}'.format(e.message)
    #     print (error_message)
    #     utility.log(pilib.dirs.logs.system, error_message)
    # else:
    #     utility.log(pilib.dirs.logs.system, 'Boot notificaiton complete. ')


    # Start pigpiod

    subprocess.call(['killall','pigpiod'])
    sleep(1)
    utility.log(pilib.dirs.logs.system, 'boot: starting pigpio daemon', 3, pilib.loglevels.system)
    subprocess.call(['/usr/local/bin/pigpiod'])

    # Start webserver

    subprocess.call(['killall','nginx'])
    subprocess.call(['killall','uwsgi'])
    subprocess.call(['killall','apache2'])

    if systemstatus['webserver'] == 'apache':
        utility.log(pilib.dirs.logs.system, 'boot: starting apache', 3, pilib.loglevels.system)
        subprocess.call(['service', 'apache2', 'start'])
    elif systemstatus['webserver'] == 'nginx':
        utility.log(pilib.dirs.logs.system, 'boot: starting nginx', 3, pilib.loglevels.system)
        subprocess.call(['service', 'nginx', 'start'])

    # Run uwsgi daemon if nginx is running

    try:
        result = subprocess.check_output(['service', 'nginx', 'status']).decode('utf-8')
    except subprocess.CalledProcessError as e:
        result = ''
        # print('I AM FAILING')
        # print e.output

    if result:
        utility.log(pilib.dirs.logs.system, 'boot: starting uwsgi based on nginx call', 0)
        subprocess.call(['uwsgi', '--emperor', '/usr/lib/iicontrollibs/wsgi/', '--daemonize', '/var/log/cupid/uwsgi.log'])
    else:
        # print(' I KNOW NGINX IS NOT RUNNING')
        pass
    # Mount 1wire master

    subprocess.call(['killall','owfs'])
    subprocess.call(['killall','owserver'])
    subprocess.call(['killall','owhttpd'])

    runi2cowfs = True
    runusbowfs = False

    temp_unit = 'C'
    for interface in interfaces:
        if interface['enabled']:
            from iiutilities.datalib import parseoptions
            options_dict = parseoptions(interface['options'])
            if 'tempunit' in options_dict:
                if options_dict['tempunit'] in ['F','f','Fahrenheit','fahrenheit']:
                    temp_unit = 'F'

            if interface['interface'] == 'I2C' and interface['type'] == 'DS2483':
                runi2cowfs = True
            if interface['interface'] == 'USB' and interface['type'] == 'DS9490':
                runusbowfs = True

            if interface['interface'] == 'SPI1' and type == 'CuPIDlights':
                spilights.updatelightsfromdb(pilib.dirs.dbs.control, 'indicators', 1)
            if interface['interface'] == 'SPI0' and type == 'CuPIDlights':
                spilights.updatelightsfromdb(pilib.dirs.dbs.control, 'indicators', 0)

    if runi2cowfs or runusbowfs:
        if runi2cowfs:
            utility.log(pilib.dirs.logs.system, 'boot: Running i2c owserver', 3, pilib.loglevels.system)
            try:
                if temp_unit == 'F':
                    subprocess.call(['/opt/owfs/bin/owserver', '-F', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
                else:
                    subprocess.call(['/opt/owfs/bin/owserver', '--i2c=/dev/i2c-1:ALL', '-p', '4304'])
            except:
                utility.log(pilib.dirs.logs.system, 'boot: error running i2c owserver', 1, pilib.loglevels.system)
        if runusbowfs:
            utility.log(pilib.dirs.logs.system, 'boot: Running usb owserver', 3, pilib.loglevels.system)
            try:
                if temp_unit == 'F':
                    subprocess.call(['/opt/owfs/bin/owserver', '-F', '-u', '-p', '4304'])
                else:
                    subprocess.call(['/opt/owfs/bin/owserver', '-u', '-p', '4304'])
            except:
                utility.log(pilib.dirs.logs.system, 'error running usb owserver', 1, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'boot: Running owfs/owserver mount', 3, pilib.loglevels.system)
        try:
            if temp_unit == 'F':
                subprocess.call(['/opt/owfs/bin/owfs', '-F', '-s', '4304', '/var/1wire/'])
            else:
                subprocess.call(['/opt/owfs/bin/owfs', '-s', '4304', '/var/1wire/'])
        except:
            utility.log(pilib.dirs.logs.system, 'boot: error running owfs', 1, pilib.loglevels.system)

        utility.log(pilib.dirs.logs.system, 'boot: Running owhttpd/owserver mount', 3, pilib.loglevels.system)
        try:
            if temp_unit == 'F':
                subprocess.call(['/opt/owfs/bin/owhttpd', '-F', '-s', '4304', '-p', '4305'])
            else:
                subprocess.call(['/opt/owfs/bin/owhttpd', '-s', '4304', '-p', '4305'])
        except:
            utility.log(pilib.dirs.logs.system, 'boot: error running owhttpd', 1, pilib.loglevels.system)

    else:
        utility.log(pilib.dirs.logs.system, 'boot: not running owfs', 3, pilib.loglevels.system)

    # Run netstart script if enabled
    if systemstatus['netconfigenabled']:
        from netconfig import runconfig
        utility.log(pilib.dirs.logs.system, 'boot: running boot netconfig', 2, pilib.loglevels.system)
        runconfig(onboot=True)

    # THIS IS NOW IN cupid_daemon.service
    # Run daemon
    # from cupiddaemon import rundaemon

    # rundaemon()

    # Update hardware version in table
    # from systemstatus import readhardwarefileintoversions
    #
    # readhardwarefileintoversions()

if __name__=="__main__":
    runboot()