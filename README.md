iicontrollibs
=============

Interface Innovations libraries for networked control, general and pi-based

Hello there. Welcome to the II libraries.

Requirements:

Python 2.7 is required for modules, but all should be python3 compliant

sqlite
    php5
    sqlite3
    libapache2-mod-php5
    php5-sqlite
    (pdo and sqlite are enabled by default)
i2c
    Comment out spi and i2c in /etc/modprobe.d/raspi-blacklist.conf
    python-smbus
    i2c-tools
owfs
    owfs 2.9.1 (download, make and install)
    add to rc.local: /opt/owfs/bin/owfs –i2c=/dev/i2c-1:ALL /var/1wire

SPI module:
    Python3
    python-pip
    python-virtualenv
    python3-setuptools
    python-gpioadmin
    bitstring
    quick2wire master
wsgi
    a2enmod rewrite (to enable mod_rewrite)
    alias wsgi scripts in site configuration, e.g.:
        WSGIScriptAlias /wsgisqlitequery /usr/lib/iicontrollibs/wsgi/wsgisqlitequery.wsgi

