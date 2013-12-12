#!/usr/bin/python

import gtk
from gitupdatelib import updatecupidweblibs

message=gtk.MessageDialog(buttons=gtk.BUTTONS_OK)

message.set_property('title', 'Update by git')
message.set_property('text', 'Click OK to update cupidweblibs!')
response = message.run()

message2=gtk.MessageDialog(buttons=gtk.BUTTONS_OK)
message.set_property('title', 'Update by git')

if response == gtk.RESPONSE_OK:

    message.destroy()
    updatecupidweblibs() 
    #print(gitresponse)

    message2.set_property('text', 'UpdateComplete!')
else:
    message2.destroy()
    message2.set_property('text', 'Update Aborted')

response=message2.run()
if response:
    message2.destroy()

#print('Update Complete')
os.system("echo 'stuff' > /home/pi/Desktop/output.txt")
