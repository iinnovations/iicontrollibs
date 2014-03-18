iicontrollibs TODO
=========================================

## System config
### Complete network configuration
We've got a good start on network configuration using hostapd, isc-dhcp-server and pyiface. We need to smooth out the
edges and incorporate full control, including dhcp server configuration and creation of our network interfaces file from
scratch (or successful manipulation using pyiface).

## Sensors
### Module disable
Interfaces not used need to all be error-protected code blocks
These should be capable of disable from UI database, and also should self-detect and disable on user error

### i2c
Autodetect i2c devices on interface

### 1Wire
Develop 1Wire device library
Devices type family library

## Algorithms
### Develop duty-cycle framework

### Develop Integral and Derivative for PID

## Versioning
### Update git to use tags with versions
### Start using stable branches