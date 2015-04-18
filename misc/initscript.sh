#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "no arguments supplied. Usage: ./install.sh install [full]"
elif [ "$1" = "install" ]
  then
    echo "running install as requested"
    apt-get update
    apt-get -y install lsb-core
    apt-get -y install php5 sqlite3 php5-sqlite
    apt-get -y install python-dev python3 python-setuptools
    apt-get -y install swig libfuse-dev libusb-dev php5-dev

    apt-get -y install python-pip
    pip install rpi.gpio
    pip install gitpython
    apt-get -y install python-serial
    apt-get -y install python-gtk2
    apt-get -y install automake

    apt-get -y install apache2 php5 sqlite3 php5-sqlite libapache2-mod-wsgi libapache2-mod-php5
    a2enmod rewrite
    a2enmod ssl
    # default apache
    # update-rc.d -f apache2 remove

    apt-get -y install nginx
    update-rc.d -f nginx remove

    apt-get -y install uwsgi
    apt-get -y install uwsgi-plugin-python
    apt-get -y install php5-fpm

    apt-get -y install i2c-tools python-smbus
    apt-get -y install hostapd
    apt-get -y install isc-dhcp-server
    update-rc.d -f isc-dhcp-server remove

    echo "installing gpio-admin"
    apt-get install quickwire-gpio-admin

    echo "installing python-api-master"
    apt-get install quick2wire-python-api-master/

    echo "installing spi-dev"
    pip install spidev

    echo "installing bitstring"
    apt-get install python3-pip

    pip install bitstring
    pip-3.3 install bitstring

    echo "configuring hamachi"

  if [ -z $2 ]
  then
    echo "not manipulating users or directories"
  elif [ "$2" = "full" ]
  then

    echo "configuring users"
    addgroup sshers
    usermod -aG sshers pi
    usermod -aG www-data pi

    useradd websync
    usermod -aG sshers websync
    usermod -aG www-data websync
    echo "user configuration complete"

    echo "Configuring directories"
    mkdir /usr/lib/iicontrollibs
    chown -R root:pi /usr/lib/iicontrollibs
    chmod -R 775 /usr/lib/iicontrollibs
    chmod ug+x /usr/lib/iicontrollibs

    mkdir /var/wwwsafe
    chown -R root:pi /var/wwwsafe
    chmod -R 775 /var/wwwsafe
    chmod ug+x /var/wwwsafe

    mkdir /var/www
    chown -R root:www-data /var/www
    chmod -R 775 /var/www
    chmod ug+x /var/www

    mkdir /usr/lib/cgi-bin
    chown -R root:www-data /usr/lib/cgi-bin
    chmod ug+x /usr/lib/cgi-bin

    mkdir /var/log/cupid
    chgrp -R pi /var/log/cupid
    chmod ug+s /var/log/cupid
    chmod -R 775 /var/log/cupid

    mkdir /var/1wire
    echo "directory configuration complete"

    echo "configuring sshd for restricted access"
    echo "Configuring sshd"
    #       Add to sshd_config: AllowGroups sshers
    testresult=$(grep -c 'AllowGroups' /etc/ssh/sshd_config)
    if [ ${testresult} -ne 0 ]
      then
        echo "Groups ssh already configured"
    else
      echo "AllowGroups sshers" >> /etc/ssh/sshd_config
    fi
    echo "sshd configuration complete"

    echo "Initializing web library repo"
    cd /var/www
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/cupidweblib
    chown -R pi:www-data .git
    chmod -R 775 .git
    git reset --hard master
    git pull origin master
    chown -R pi:www-data *
    chmod -R 775 *
    echo "complete"


    echo "Initializing control libraries repo"
    cd /usr/lib/iicontrollibs
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/iicontrollibs
    chown -R pi:www-data .git
    chmod -R 775 .git
    git reset --hard master
    git pull origin master
    chown -R pi:www-data *
    chmod -R 775 *
    echo "complete"

    echo "Creating default databases"
    /usr/lib/iicontrollibs/cupid/rebuilddatabases.py DEFAULTS
    chmod g+s /var/www/data
    chmod -R 775 /var/www/data
    chown -R root:www-data /var/www/data

    echo "Complete"

    echo "Copying boot script"
    cp /usr/lib/iicontrollibs/misc/rc.local /etc/
    echo "complete"

    echo "Updating crontab"
    crontab /usr/lib/iicontrollibs/misc/crontab
    echo "complete"


    #    wget https://secure.logmein.com/labs/logmein-hamachi_2.1.0.139-1_armhf.deb
    dpkg -i /usr/lib/iicontrollibs/resource/logmein-hamachi_2.1.0.139-1_armhf.deb
    hamachi login
    # hamachi do-join XXX-XX-XXXX

    echo "hamachi complete"

    echo "testing for owfs"
    testresult=$(/opt/owfs/bin/owfs -V | grep -c '2.9p5')
    if [ ${testresult} -ne 0 ]
      then
        echo "owfs 2.9p5 already installed"
    else
        echo "installing owfs 2.9p5"
        cd /usr/lib/iicontrollibs/resource
        tar -xvf owfs-2.9p5.tar.gz
        cd /usr/lib/iicontrollibs/resource/owfs-2.9p5
        ./configure
        make install
        cd ..
        rm -R owfs-2.9p5
    fi
    echo "owfs complete"

    # get custom sources
#    cp /usr/lib/iicontrollibs
#    apt-get update

    # handled in raspi-config
#    echo "Copying inittab"
#    cp /usr/lib/iicontrollibs/misc/inittab /etc/
#    echo "Complete"

#    echo "Copying cmdline.txt"
#    cp /usr/lib/iicontrollibs/misc/cmdline.txt /boot/
#    echo "Complete"

    echo "Copying nginx site"
    cp /usr/lib/iicontrollibs/misc/nginx/nginxsite /etc/nginx/sites-available/default
    echo "Complete"

    echo "Copying apache site"
    cp /usr/lib/iicontrollibs/misc/apache/apachesslsites /etc/apache/sites-available/default
    echo "Complete"

    echo "Copying nginx config"
    cp /usr/lib/iicontrollibs/misc/nginx/ngin.conf /etc/nginx/nginx.conf
    echo "Complete"

    echo "Creating self-signed ssl cert"
    mkdir /etc/ssl/localcerts
    openssl req -new -x509 -days 365 -nodes -out /etc/ssl/localcerts/mycert.pem -keyout /etc/ssl/localcerts/mycert.key
    echo "Complete"

    echo "setting fpm extensions to allow html files"
    # cp pool.d/www.conf file over ...

    echo "Copying dhcpd.conf"
    cp /usr/lib/iicontrollibs/misc/dhcpd.conf /etc/dhcp/
    echo "Complete"

#    if [ $(ls /usr/sbin/ | grep -c 'hostapd.edimax') -ne 0 ]
#        then
#            echo "hostapd already configured"
#    else
#        echo "copying hostapd"
#        mv /usr/sbin/hostapd /usr/sbin/hostapd.bak
#        cp /usr/lib/iicontrollibs/resource/hostapd.edimax /usr/sbin/hostapd.edimax
#        ln -sf /usr/sbin/hostapd.edimax /usr/sbin/hostapd
#        chown root:root /usr/sbin/hostapd
#        chmod 755 /usr/sbin/hostapd
#        echo "hostapd configuration complete"
#    fi

    echo "copying hostapd.conf"
    cp /usr/lib/iicontrollibs/misc/hostapd.conf /etc/hostapd/

    # These are now handled via raspi-config (I think. In testing)
#    echo "copying blacklist file"
#    cp /usr/lib/iicontrollibs/misc/raspi-blacklist.conf /etc/modprobe.d/

#    echo "setting modprobe"
#    modprobe i2c-bcm2708

#    echo "coping boot config to disable console serial interface and enable serial interfaces"
#    cp /usr/lib/iicontrollibs/misc/config.txt /boot/

    echo "Copying icons to desktop"

    echo "Changing desktop wallpaper"
    sudo -u pi pcmanfm -w /var/www/images/splash/cupid_splash_big.png

    echo "Copying icons"
    cp /usr/lib/iicontrollibs/misc/updatecupidweblibs.desktop /
  else
    echo "Invalid argument received: "
    echo "$2"
    echo "Usage: ./install.sh install [full]"
  fi
else
    echo "Invalid argument received: "
    echo "$1"
    echo "Usage: ./install.sh install [full]"
fi