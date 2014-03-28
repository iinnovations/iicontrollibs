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

    import pilib

    print("processing enabled I2C")
    from owfslib import updateowfstable, updateowfsentries
    #updateowfstable(database, 'owfs')
    updateowfsentries(database, 'inputs')

if __name__ == "__main__":
    from pilib import controldatabase
    updateiodata(controldatabase)

