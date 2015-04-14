#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2014, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'

''' This is all pseudocode at the moment

All messages begin with x0000 and end with xFFFF (four bytes)
As a result, messages must be checked for inclusion of these sequences

Typical Remote sequence:
    Send Xmit Request:
        Message Type        2 Byte      (xmitreq type)
        Message Source ID   4 Bytes     (Dest ID 00 for unknown)
        Message Dest ID     4 Bytes     (Dest ID xFF for broadcast or non-specific message)
        Message CRC16       2 Bytes

    Remote waits for ack for *xmitreqwait
    Message repeats number of times *xmitreqretries

    Controller responds with Ack(first nine bytes are repeat of Remote message):
        Message Type        1 Byte
        Message Source ID   4 Bytes
        Message Dest ID     4 Bytes     (ID of controller)
        Action              1 Byte
        Message CRC16       2 Bytes

    If response Action is Go Ahead, send message:
        Message Type        1 Byte      (xmit)
        Message Source ID   4 Bytes
        Message Dest ID     4 Bytes     (received address of controller)
        PAYLOAD:
            Number Data Items   1 Byte
            Total Data Size     1 Byte
            Data Items:
                Data Type           2 Bytes
                Data Length         1 Byte
                Data                *DataLength Bytes
        Message CRC16           2 Bytes

    Wait for response for time *messageackwait
    Retry message send *messagesendretries

    Controller response with Ack:
        Message Type        2 Byte
        Message Source ID   2 Bytes
        Action              1 Byte (typical would be Sleep, Stand by for command)

Message Types:
    xmitreq
    xmit
    init
    wait for cmd
Actions for remote:
    00 Go Ahead (xmit)
    01 Wait 1
    02 Wait 2
    03 Stand by for command
    FF Sleep
Data Types:
    00 00   ASCII command (delimited by characters, length specified)













'''