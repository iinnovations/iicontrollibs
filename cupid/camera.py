#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"


def takesnap(path='/var/www/webcam/images/', filename='current.jpg', quality=75, width=None, timeout=2000):
    # import picamera
    import subprocess
    import os
    from iiutilities.datalib import timestringtoseconds
    from iiutilities.datalib import gettimestring
    # camera = picamera.PiCamera()

    imagepath = path + filename
    timestamp = gettimestring()
    timestamppath = imagepath + '.timestamp'

    time1 = gettimestring()
    if width:
        height = int(float(width) / 1.33333)
        subprocess.call(['raspistill','-q', str(quality), '--width', str(width), '--height', str(height), '-t', str(timeout), '-o', imagepath])
    else:
        width =  2592
        height = 1944
        subprocess.call(['raspistill','-q', str(quality), '-t', str(timeout), '-o', imagepath])

    with open(timestamppath,'w') as f:
        f.write(timestamp)
    f.close()
    # camera.capture(path + filename)
    time2 = gettimestring()

    elapsedtime = timestringtoseconds(time2) - timestringtoseconds(time1)
    try:
        imagesize = os.path.getsize(imagepath)
    except:
        imagesize = 0

    return {'elapsedtime':elapsedtime, 'imagepath':imagepath, 'timestamp':timestamp, 'timestamppath': timestamppath, 'imageheight':height, 'imagewidth':width, 'imagesize':imagesize}

if __name__ == "__main__":
    takesnap()