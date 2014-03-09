#!/bin/bash


# __author__ = "Colin Reese"
# __copyright__ = "Copyright 2014, Interface Innovations"
# __credits__ = ["Colin Reese"]
# __license__ = "Apache 2.0"
# __version__ = "1.0"
# __maintainer__ = "Colin Reese"
# __email__ = "support@interfaceinnovations.org"
# __status__ = "Development"

if [ "$1" == 'compon' ]; then
  tvservice -sdtvon="NTSC 4:3";
  startx &
  echo 'screen enabled'
fi

if [ "$1" == 'hdmion' ]; then
  tvservice -o;
  tvservice -p;
  startx &
  echo 'hdmi enabled'
fi

if [ "$1" == 'off' ]; then
  tvservice -o
  echo 'screens disabled'
fi

  
