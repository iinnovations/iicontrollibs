#!/bin/bash

RED='\033[0;31m'
WHT='\033[1;37m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]
  then
    echo "no arguments supplied. Usage: ./install.sh install [full]"
elif [ "$1" = "install" ]
  then
    echo -e "${WHT}************************************${NC}"
    echo -e "${WHT}*****      RUNNING INSTALL     *****${NC}"
    echo -e "${WHT}************************************${NC}"

    # reconfig keys?

    # rm -r /etc/ssh/ssh*key
    # dpkg-reconfigure openssh-server

    # Enable uart
    # This is done with raspi-config now, but this won't hurt
    # /bin/sed -ie 's/enable_uart=0/enable_uart=1/g' /boot/config.txt

    apt-get -y update
    apt-get -y upgrade
    apt-get -y install git
    apt-get -y remove --purge wolfram-engine
    apt-get -y autoremove

     # This is what should work (and WILL work once they update the repos)
    apt-get -y install lsb-core

    # remove, but leave requirements
    apt-get -y remove lsb-core

    echo "configuring hamachi"
    # So we have a compatibility issue with the lsb-core in raspbian jessie. We should ideally:
    # 1. Test for OS version (probably revert to previous raspbian here)
    # 2. If using jessie, do the following
    # wget http://ftp.de.debian.org/debian/pool/main/l/lsb/lsb-core_4.1+Debian8+deb7u1_armhf.deb
    # dpkg -i lsb-core_4.1+Debian8+deb7u1_armhf.deb

    # THIS HAS BEEN FIXED ^^ as of STRETCH

    # wget https://secure.logmein.com/labs/logmein-hamachi_2.1.0.139-1_armhf.deb
    wget https://www.vpn.net/installers/logmein-hamachi_2.1.0.174-1_armhf.deb
    dpkg -i logmein-hamachi_2.1.0.174-1_armhf.deb
    rm logmein-hamachi_2.1.0.174-1_armhf.deb
    # dpkg -i /usr/lib/iicontrollibs/resource/logmein-hamachi_2.1.0.139-1_armhf.deb
    hamachi login
    # hamachi do-join 283-153-722
    #
    echo "hamachi complete"

    apt-get -y install php sqlite3 php7.0-sqlite
    apt-get -y install python-dev python3-dev python3 python-setuptools
    apt-get -y install swig libfuse-dev libusb-dev php-dev
    apt-get -y ifupdown

    apt-get -y install python-pip
    pip3 install rpi.gpio
    pip3 install gitpython
    pip3 install requests
    pip3 install pyownet
    pip3 install pymodbus

    apt-get -y install python-serial
    apt-get -y install python-gtk2
    apt-get -y install automake
    apt-get -y install fping
    # pip install lal

    apt-get -y install apache2 libapache2-mod-wsgi libapache2-mod-php
    a2enmod rewrite
    a2enmod ssl
    update-rc.d -f apache2 remove
    service apache2 stop

    apt-get -y install nginx
    update-rc.d -f nginx remove
    update-rc.d -f dhcpd remove
    apt-get -y install uwsgi
    apt-get -y install uwsgi-plugin-python
    apt-get -y install uwsgi-plugin-python3

    apt-get -y install php-fpm
    apt-get -y install i2c-tools python-smbus
    apt-get -y install hostapd isc-dhcp-server
    update-rc.d -f isc-dhcp-server remove

    # This appears to cause problems with hamachi and is by default installed on Stretch
    # We may be able to avoid this by moving from network/interfaces. Unknown.
    update-rc.d -f dhcpcd remove

    echo "installing pigpio"
    wget abyz.co.uk/rpi/pigpio/pigpio.zip
    unzip pigpio.zip
    cd PIGPIO
    make
    make install
    cd ..
    rm -Rf PIGPIO

    echo "installing asteval"
    pip3 install asteval

    echo -e "${WHT}************************************${NC}"
    echo -e "${WHT}*****   STD  INSTALL  COMPLETE *****${NC}"
    echo -e "${WHT}************************************${NC}"


elif [ "$1" = "maxtc" ]
  then
    echo "installing MAX31855 library"
    cd /usr/lib/iicontrollibs/resource/Adafruit_Python_MAX31855-master
    python setup.py install

elif [ "$1" = "update" ]
  then
    echo "updating"
    pip3 install rpi.gpio
    pip3 install gitpython
    apt-get -y install uwsgi-plugin-python3
    pip3 install asteval
    pip3 install pyownet
    pip3 install pymodbus
    cd /usr/lib/iicontrollibs/resource
    tar xvf netifaces-0.10.6.tar.gz
    cd netifaces-0.10.6
    python setup.py install
    python3 setup.py install
    cd ..
    rm -rf netifaces-0.10.6
    cd /usr/lib/iicontrollibs/iiutilities
    python3 -c 'import data_agent; data_agent.rebuild_data_agent_db()'

elif [ "$1" = "spi" ]
  then
    echo "installing spi-dev"
    wget https://github.com/Gadgetoid/py-spidev/archive/master.zip
    unzip master.zip
    rm master.zip
    cd py-spidev-master
    sudo python setup.py install
    cd ..
    rm -R py-spidev-master

elif [ "$1" = "camera" ]
  then
    apt-get update
    apt-get install python-picamera

elif [ "$1" = "labjack" ]
  then
    apt-get update
    apt-get -y install libusb-1.0
    cd ../resource/labjack/LabJackPython-5-26-2015/
    python setup.py install
    cd labjack-exodriver-815464f
    ./install.sh
fi

if [ "$2" = "full" -o "$1" = "full" ]
  then
    echo -e "${WHT}************************************${NC}"
    echo -e "${WHT}*******  RUNNING ADDITIONAL  *******${NC}"
    echo -e "${WHT}*******  INSTALL CONPONENTS  *******${NC}"
    echo -e "${WHT}************************************${NC}"

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
    chown -R root:www-data /var/wwwsafe
    chmod -R 775 /var/wwwsafe
    chmod ug+x /var/wwwsafe

    mkdir /var/www
    rm -Rf /var/www/*
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

    echo "Disabling iface names"
    testresult=$(grep -c 'net.ifnames=0' /boot/cmdline.txt)
    if [ ${testresult} -ne 0 ]
      then
        echo "ifacenames already disabled"
    else
       cp /boot/cmdline.txt /boot/cmdline.txt.bak
       echo -n 'net.ifnames=0 ' | cat - /boot/cmdline.txt.bak > /boot/cmdline.txt
    fi
    echo "sshd configuration complete"

    echo "Initializing web library repo"
    cd /var/www
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/cupidweblib

    git reset --hard master
    git pull origin master
    chown -R pi:www-data *
    chmod -R 775 *
    chown -R pi:www-data .git
    chmod -R 775 .git
    echo "complete"


    echo "Initializing control libraries repo"
    cd /usr/lib/iicontrollibs
    rm -R *
    git init .
    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"
    git remote add origin https://github.com/iinnovations/iicontrollibs

    git reset --hard master
    git pull origin master
    chown -R pi:www-data .git
    chmod -R 775 .git
    chown -R pi:www-data *
    chmod -R 775 *
    echo "complete"

    echo "Creating default databases"
    /usr/lib/iicontrollibs/cupid/rebuilddatabases.py DEFAULTS
    cd /usr/lib/iicontrollibs/iiutilities
    python3 -c 'import data_agent; data_agent.rebuild_data_agent_db()'
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


    cd /usr/lib/iicontrollibs/resource
    tar -xvf netifaces-0.10.6.tar.gz
    cd netifaces-0.10.6
    python setup.py install
    python3 setup.py install
    cd ..
    rm -rf netifaces-0.10.6

#    echo "testing for owfs"
#    testresult=$(/opt/owfs/bin/owfs -V | grep -c '2.9p5')
#    if [ ${testresult} -ne 0 ]
#      then
#        echo "owfs 2.9p5 already installed"
#    else
#        echo "installing owfs 2.9p5"
#        cd /usr/lib/iicontrollibs/resource
#        tar -xvf owfs-2.9p5.tar.gz
#        cd /usr/lib/iicontrollibs/resource/owfs-2.9p5
#        ./configure
#        make
#        make install
#        cd ..
#        rm -R owfs-2.9p5
#    fi
#    echo "owfs complete"

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
    cp /usr/lib/iicontrollibs/misc/apache/apachesslsites /etc/apache2/sites-available/default
    echo "Complete"

    echo "Copying nginx certificates"
    cp /usr/lib/iicontrollibs/misc/nginx/nginx.ssl.conf /etc/nginx/nginx.conf

    # fix security limit extensions
    cp /usr/lib/iicontrollibs/misc/nginx/www.conf /etc/php/7.0/fpm/pool.d/www.conf
    echo "Complete"

    echo "Creating self-signed ssl cert"
    mkdir /etc/ssl/localcerts
    openssl req -new -x509 -sha256 -days 365 -nodes \
       -subj "/C=US/ST=OR/L=Portland/O=Interface Innovations/OU=CuPID Controls/CN=interfaceinnovations.org" \
        -out /etc/ssl/localcerts/mycert.pem \
        -keyout /etc/ssl/localcerts/mycert.key

    echo "Complete"

#    This is now done at configure time, with dedicated dhcpd files
#    echo "Copying dhcpd.conf"
#    cp /usr/lib/iicontrollibs/misc/dhcpd.conf /etc/dhcp/
#    echo "Complete"

#    if [ $(ls /usr/sbin/ | grep -c 'hostapd.edimax') -ne 0 ]
#        then
#            echo "hostapd already configured"
#    else
#        echo "copying hostapd"

        # This stuff is now deprecated with new hostapd on built-in Pi 3 ap hardware.
#        mv /usr/sbin/hostapd /usr/sbin/hostapd.bak
#        cp /usr/lib/iicontrollibs/resource/hostapd.edimax /usr/sbin/hostapd.edimax
#        ln -sf /usr/sbin/hostapd.edimax /usr/sbin/hostapd
#        chown root:root /usr/sbin/hostapd
#        chmod 755 /usr/sbin/hostapd
#        echo "hostapd configuration complete"
#    fi

#    We now run hostapd directly
#    echo "copying hostapd.conf"
#    cp /usr/lib/iicontrollibs/misc/hostapd.conf /etc/hostapd/

#    # Ensure i2c-dev module is loaded
#    testresult=$(grep -c 'i2c-dev' /etc/modules)
#    if [ ${testresult} -ne 0 ]
#      then
#        echo "i2c-dev already exists"
#    else
#      echo "loading dev module"
#      echo "i2c-dev" >> /etc/modules
#    fi
#    echo "i2c-dev configuration complete"

#    echo "Copying icons to desktop"
#    cp /usr/lib/iicontrollibs/misc/icons/* /home/pi/Desktop

#    echo "Changing desktop wallpaper"
    cp /usr/lib/iicontrollibs/misc/desktop-items-0.conf /home/pi/.config/pcmanfm/LXDE-pi/
#
#    echo "Copying icons"
    cp /usr/lib/iicontrollibs/misc/icons/* ~/
    echo -e "${WHT}************************************${NC}"
    echo -e "${WHT}******* FINISHED  ADDITIONAL  ******${NC}"
    echo -e "${WHT}*******  INSTALL CONPONENTS  *******${NC}"
    echo -e "${WHT}************************************${NC}"
fi

if [ "$1" != "install" -a "$1" != "full" ]
  then
    echo "Invalid argument received: "
    echo "$2"
    echo "Usage: ./install.sh install [full]"
fi