#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


def updateiodata(database):

    import pilib, owfslib

    busdevices = owfslib.owfsgetbusdevices(pilib.onewiredir)
    print('done getting devices, took ' + str(time.time() - starttime))
    print('updating owfs table')
    starttime = time.time()
    owfslib.updateowfstable(pilib.controldatabase, 'owfs', busdevices)
    print('done updating owfstable, took ' + str(time.time() - starttime))
    print('updating entries')
    starttime = time.time()
    owfslib.updateowfsentries(pilib.controldatabase, 'inputs', busdevices)
    print('done reading devices, took ' + str(time.time() - starttime))
    print('your devices: ')
    for device in busdevices:
        print(device.id)

if __name__ == "__main__":
    from pilib import controldatabase
    updateiodata(controldatabase)

