#!/bin/bash
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

  
