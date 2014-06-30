#!/usr/bin/python
# 
# Colin Reese
# August 27, 2013
#
# netfun.py
#
# Network operations, including status/device testing and modbus operations

import os
import inspect
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)



def runping(pingAddress, numpings=1):
    pingtimes = []
    for i in range(numpings):
        # Perform the ping using the system ping command (one ping only)
        try:
            rawPingFile = os.popen('ping -c 1 %s' % (pingAddress))
        except:
            failed = True
            latency = 0
        else:
            # Extract the ping time
            rawPingData = rawPingFile.readlines()
            rawPingFile.close()
            if len(rawPingData) < 2:
                # Failed to find a DNS resolution or route
                failed = True
                latency = 0
            else:
                index = rawPingData[1].find('time=')
                if index == -1:
                    # Ping failed or timed-out
                    failed = True
                    latency = 0
                else:
                    # We have a ping time, isolate it and convert to a number
                    failed = False
                    latency = rawPingData[1][index + 5:]
                    latency = latency[:latency.find(' ')]
                    latency = float(latency)

        # Set our outputs
        if failed:
            # Could not ping
            pingtimes.append(0)
        else:
            # Ping stored in latency in milliseconds
            #print '%f ms' % (latency)
            pingtimes.append(latency)
            pilib.writedatedlogmsg(pilib.networklog, 'ping times: ' + str(pingtimes), 3, pilib.networkloglevel)
    return pingtimes


def gethamachidata():
    from subprocess import Popen, PIPE

    rawoutput = Popen(['hamachi', 'list'], stdout=PIPE)
    output = rawoutput.stdout.read()
    lines = output.split('\n')
    data = lines[1:-1]  # one whitespace line at end
    dictarray = []
    #print(data)
    for row in data:
        dict = {}

        if row[5] == '*':
            dict['onlinestatus'] = 'online'
        else:
            dict['onlinestatus'] = 'offline'
        dict['name'] = row[21:35].strip()
        dict['clientid'] = row[7:17].strip()
        dict['hamachiip'] = row[48:64].strip()
        dict['alias'] = row[73:88].strip()
        dict['connipport'] = row[90:100].strip()
        dict['conntype'] = row[135:145].strip()
        dict['connprotocol'] = row[147:151].strip()
        dict['connipport'] = row[152:173].strip()
        dictarray.append(dict)
    return dictarray


def checksharemount(sharepath):
    from subprocess import Popen, PIPE

    mountresponse = Popen(['cat', '/proc/mounts'], shell=False, stdout=PIPE)

    linedata = ''
    for line in mountresponse.stdout:
        linedata = linedata + line

    print(linedata.find(sharepath))
    if linedata.find(sharepath) >= 0:
        status = True
    else:
        status = False
    return status


#--------------------------------------------------#
#
#   MODBUS Read/write functions
#
#--------------------------------------------------#

def readMBinputs(clientIP, coil, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    result = client.read_discrete_inputs(coil, number)
    client.close()
    try:
        return result.bits[0:number]
    except AttributeError:
        print('there are no registers!')
        return result


def readMBcoils(clientIP, coil, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    result = client.read_coils(coil, number)
    client.close()
    try:
        return result.bits[0:number]
    except AttributeError:
        print('there are no registers!')
        return result


def writeMBcoils(clientIP, coil, valuelist):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    client.write_coils(coil, valuelist)
    result = client.read_coils(coil, len(valuelist))
    client.close()
    try:
        return result.bits[0:len(valuelist)]
    except AttributeError:
        return result


def readMBholdingregisters(clientIP, register, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)

    try:
        rawresult = client.read_holding_registers(register, number)
    except:
        result = {'message': 'modbus client error !', 'statuscode': 9, 'values': []}
        client.close()
        return result

    try:
        resultregisters = rawresult.registers
    except AttributeError:
        result = {'message': 'there are no registers!', 'statuscode': 8}
        client.close()
        return result

    result = {'message':'result returned', 'statuscode':0, 'values':resultregisters}
    client.close()
    return result


def readMBinputregisters(clientIP, register, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    try:
        rawresult = client.read_input_registers(register, number)
    except:
        result = {'message': 'modbus client error !', 'statuscode': 9, 'values': []}
        client.close()
        return result

    try:
        resultregisters = rawresult.registers
    except AttributeError:
        result = {'message': 'there are no registers!', 'statuscode': 8}
        client.close()
        return result

    result = {'message':'result returned', 'statuscode':0, 'values':resultregisters}
    client.close()
    return result


def writeMBholdingregisters(clientIP, register, valuelist):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    client.write_registers(register, valuelist)
    result = client.read_holding_registers(register, len(valuelist))
    client.close()
    try:
        return result.registers
    except AttributeError:
        print('there are no registers!')
        return result
    except:
        print('other unhandled error')
        return result


def readMBcodedaddresses(clientIP, address, length=1):
    # addresses are as following:
    # Input registers   : 300000    -  399999
    # Holding registers : 400000    -  400000
    # Coils             : 000001.00 -  099999.07
    # Discrete inputs   : 100001.00 -  199999.07

    # Bit addresses are in float 
    # 16 bits per word

    # determine what we are doing by address
    if isinstance(address, int) or isinstance(address, float):
        pass
    elif isinstance(address, str):
        address = float(address)
    else:
        # valueerror 
        return

    if address >= 0 and address < 100000:
        # coils
        readaddress = int(address) * 16 + int((address % 1) * 100)
        result = readMBcoils(clientIP, readaddress, length)
        #print(result)
        return result
    elif address >= 100000 and address < 200000:
        # discrete inputs
        readaddress = int(address - 100000) * 16 + int(((address - 100000) % 1) * 100)
        result = readMBinputs(clientIP, readaddress, length)
        return result
    elif address >= 300000 and address < 400000:
        # input registers
        readaddress = int(address) - 300000
        result = readMBinputregisters(clientIP, readaddress, length)
        return result
    elif address >= 400000 and address < 500000:
        # holding registers 
        readaddress = int(address) - 400000
        result = readMBholdingregisters(clientIP, readaddress, length)
        return result
    else:
        return


def MBFCfromaddress(address):
    if address >= 0 and address < 100000:
        FC = 0
    elif address >= 100000 and address < 200000:
        FC = 1
    elif address >= 300000 and address < 400000:
        FC = 4
    elif address >= 400000 and address < 500000:
        FC = 3
    else:
        FC = -1
    return FC


def datamaptoblockreads(datamap):
    import netfun

    # This takes raw entries in the datamap and converts them into blockreads, special dictionaries that
    # tell datareader what to read and where to put it.

    maxwordblocksize = 24
    maxbitblocksize = 1024

    # We manipulate the datamap. We leave some stuff alone and block/manipulate other stuff.
    # First, we are going to block together the MB reads

    editedmap = []
    mapkeys = []
    for item in datamap:
        # Device a unique key for each readtype
        if item['inputtype'] == 'MBTCP':
            # For MB, this is IP address
            # We'll process types later
            mapkey = item['inputid1']
            if mapkey in mapkeys:
                dictindex = mapkeys.index(mapkey)

                # inputid2 is the MB address
                editedmap[dictindex]['addresses'].append(item['inputid2'])
                editedmap[dictindex]['indices'].append(item['index'])

            else:
                editedmap.append(
                    {'inputtype': 'MBTCPblock', 'ipaddress': item['inputid1'], 'addresses': [item['inputid2']],
                     'indices': [item['index']]})
                mapkeys.append(mapkey)
        else:
            mapkey = item['inputid1'] + '_' + item['inputid2'] + '_' + item['inputid3']
            if mapkey in mapkeys:
                pass
            else:
                editedmap.append(item)
                mapkeys.append(mapkey)

    returnmap = []
    for item in editedmap:
        if item['inputtype'] == 'MBTCPblock':
            # Reorder MB addresses by number
            intaddresses = map(int, item['addresses'])
            sortedaddresses, sortedindices = zip(*sorted(zip(intaddresses, item['indices'])))

            print(sortedaddresses)
            print(sortedindices)
            newitems = []
            newitem = {}
            for address, index in zip(sortedaddresses, sortedindices):
                # If there isn't a new item, add one
                if not newitem:
                    newitem = {'inputtype': 'MBTCPblock', 'ipaddress': item['ipaddress'], 'addresses': [address],
                               'indices': [index], 'start': address, 'length': 1}

                # We check to see if we can just add to the existing item
                else:

                    FC = netfun.MBFCfromaddress(address)
                    lastFC = netfun.MBFCfromaddress(newitem['addresses'][len(newitem['addresses']) - 1])
                    if FC in [0, 1]:
                        maxsize = maxbitblocksize
                    elif FC in [3, 4]:
                        maxsize = maxwordblocksize
                    else:
                        print('ERROR')

                    # Are we in the same memory block type?
                    if FC != lastFC:
                        startnewitem = True

                    # Are within the max range?
                    elif address - newitem['addresses'][0] > maxsize:
                        startnewitem = True
                    else:
                        startnewitem = False

                    # If we can add to the existing item, do it.
                    if not startnewitem:
                        newitem['addresses'].append(address)
                        newitem['indices'].append(index)
                        newitem['length'] = address - newitem['addresses'][0] + 1
                    # Otherwise, add to newitems and start another
                    else:
                        newitems.append(newitem)
                        newitem = {'inputtype': 'MBTCPblock', 'ipaddress': item['ipaddress'], 'addresses': [address],
                                   'indices': [index], 'start': address, 'length': 1}
            returnmap.extend(newitems)
        else:
            returnmap.append(item)

    return returnmap