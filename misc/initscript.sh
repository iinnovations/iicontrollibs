#!/bin/sh

# Initialize users and priuileges
echo $1

if [ $1 = "update" ]
  then
    apt-get update
    apt-get upgrade
    apt-get install apache2 php5 sqlite3 php5-sqlite libapache2-mod-wsgi libapache2-mod-php5
    a2enmod rewrite
    apt-get install python-dev python3 python-setuptools
    apt-get install swig libfuse-dev libusb-dev php5-dev
    apt-get install i2c-tools python-smbus
    apt-get install hostapd
    apt-get install isc-dhcp-server
    update-rc.d -f isc-dhcp-server remove
    easy_install rpi.gpio
    easy_install gitpython
    apt-get install python-serial
    apt-get install python-gtk2
fi

if [ $1 = "update" && $2 = "only" ]
    then
      echo "updated only, as requested"
else
    echo "Configuring users and directories"
    mkdir /usr/lib/iicontrollibs
    chown -R root:pi /usr/lib/iicontrollibs
    chmod -R 775 /usr/lib/iicontrollibs

    mkdir /var/wwwsafe
    chown -R root:pi /var/wwwsafe
    chmod -R 775 /var/www/safe

    chown -R root:www-data /var/www
    chmod -R 775 /var/www

    mkdir /usr/lib/cgi-bin
    chown -R root:www-data /usr/lib/cgi-bin

    mkdir /var/log/cupid
    mkdir /var/1wire

    addgroup sshers
    usermod -aG sshers pi
    usermod -aG www-data pi

    useradd websync
    usermod -aG sshers websync
    usermod -aG www-data websync
    echo "complete"

    echo "Configuring sshd"
    #       Add to sshd_config: AllowGroups sshers
    testresult=$(grep -c 'AllowGroups' /etc/ssh/sshd_config)
    if [ ${testresult} -ne 0 ]
      then
        echo "Groups ssh already configured"
    else
      echo "AllowGroups sshers" >> /etc/ssh/sshd_config
    fi
    echo "complete"


    echo "Initializing web library repo"
    cd /var/www
    git init .
    git remote add origin https://github.com/iinnovations/cupidweblib
    chown -R root:www-data .git
    chmod -R 775 .git
    git pull origin master
    echo "complete"


    echo "Initializing control libraries repo"
    cd /usr/lib/iicontrollibs
    git init .
    git remote add origin https://github.com/iinnovations/iicontrollibs
    chown -R root:www-data .git
    chmod -R 775 .git
    git pull origin master
    echo "complete"

    git config --global user.email "info@interfaceinnovations.org"
    git config --global user.name "iinnovations"

    echo "Creating default databases"
    /usr/lib/iicontrollibs/cupid/rebuilddatabases.py DEFAULTS
    echo "Complete"

    echo "Copying boot script"
    cp /usr/lib/iicontrollibs/misc/rc.local /etc/
    echo "complete"

    echo "Updating crontab"
    crontab /usr/lib/iicontrollibs/misc/crontab
    echo "complete"

    echo "Copying inittab"
    cp /usr/lib/iicontrollibs/misc/inittab /etc/
    echo "Complete"

    echo "Copying cmdline.txt"
    cp /usr/lib/iicontrollibs/misc/cmdline.txt /boot/
    echo "Complete"

    echo "Copying apache sites"
    cp /usr/lib/iicontrollibs/misc/apachesites /etc/apache2/sites-available/default
    echo "Complete"

    echo "Copying phpmyadmin configuration"
    cp /usr/lib/iicontrollibs/misc/apachesites /etc/apache2/sites-available/default
    echo "Complete"

    testresult=$(/opt/owfs/bin/owfs -V | grep -c '2.9p5')
    if [ ${testresult} -ne 0 ]
      then
        echo "owfs 2.9p5 already installed"
    else
        echo "installing owfs 2.9p5"
        #wget http://sourceforge.net/projects/owfs/files/owfs/2.9p5/owfs-2.9p5.tar.gz
        #tar -xvf owfs-2.9p5.tar.gz
        cd /usr/lib/iicontrollibs/owfs-2.9p5
        ./configure
        make install
        #cd ..
        #rm -R owfs-2.9p5
    fi
    echo "complete"

    if [ $(ls /usr/sbin/ | grep -c 'hostapd.edimax') -ne 0 ]
        then
            echo "hostapd already configured"
    else
        echo "copying hostapd"
        mv /usr/sbin/hostapd /usr/sbin/hostapd.bak
        cp /usr/lib/iicontrollibs/resource/hostapd /usr/sbin/hostapd.edimax
        ln -sf /usr/sbin/hostapd.edimax /usr/sbin/hostapd
        chown root:root /usr/sbin/hostapd
        chmod 755 /usr/sbin/hostapd
        echo "hostapd configuration complete"
    fi

    echo "copying hostapd.conf"
    cp /usr/lib/iicontrollibs/

fi
