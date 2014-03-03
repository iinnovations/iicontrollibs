iicontrollibs
=============================================

## Introduction

Interface Innovations libraries for networked control, general and pi-based
This library is designed to be used in conjunction with cupidweblibs, for a web-enabled interface employing wsgi. cupidweblibs are not required, however, and control elements may be used without the web interface. Items required only for web elements and cupidweblibs are noted below. 

## Requirements:

Elements only required for cupidweblibs are marked with **

At least Python 2.7 is required for modules, but all should be python3 compliant

sqlite
    php5
    sqlite3
    libapache2-mod-php5**
    php5-sqlite
    (pdo and sqlite are enabled by default)

i2c
    Comment out spi and i2c in /etc/modprobe.d/raspi-blacklist.conf
    python-smbus
    i2c-tools

owfs/owserver/owhttpd
    owfs 2.9.1 (download, make and install)
    add to rc.local: /usr/lib/iicontrollibs/misc/boot.sh

SPI module
    Python3
    python-pip
    python-virtualenv
    python3-setuptools
    python-gpioadmin
    bitstring
    quick2wire master

wsgi**
    apache2 mod_rewrite**
    alias wsgi scripts in site configuration, e.g.:
        WSGIScriptAlias /wsgisqlitequery /usr/lib/iicontrollibs/wsgi/wsgisqlitequery.wsgi

