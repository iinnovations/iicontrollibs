#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import os
import sys
import inspect

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)


def runping(pingAddress='8.8.8.8', numpings=1):
    pingtimes = []
    from cupid import pilib
    import subprocess
    for i in range(numpings):
        # Perform the ping using the system ping command (one ping only)
        try:
            # result, err = Popen(['ping','-c','1', pingAddress], stdout=PIPE, stderr=PIPE).communicate()
            # Default ping timeout is 500ms. This is about right.
            result = subprocess.Popen(['fping','-c','1', pingAddress], stdout=subprocess.PIPE)
            pingresult = result.stdout.read()
            # print(pingresult)
        except:
            # print('there is problem')
            pingtimes.append(-1)
        else:
            # Extract the ping time
            if pingresult:
                resultsplit = pingresult.split(',')
                # print(resultsplit)
                # print(resultsplit[2].split('ms')[0].strip())
                latency = float(resultsplit[2].split('ms')[0].strip())
                # print('latency is ' + str(latency))
                pingtimes.append(latency)

            else:
                pingtimes.append(0)


            """ OLD STUFF
            if len(result) < 2:
                # Failed to find a DNS resolution or route
                failed = True
                latency = 0
            else:
                index = result.find('time=')
                if index == -1:
                    # Ping failed or timed-out
                    failed = True
                    latency = 0
                else:
                    # We have a ping time, isolate it and convert to a number
                    failed = False
                    latency = result[index + 5:]
                    latency = latency[:latency.find(' ')]
                    latency = float(latency)
            """
    return pingtimes


def pingstatus(pingAddress='8.8.8.8', numpings=1, threshold=2000):
    pingtimes = runping(pingAddress, numpings)
    pingmax = max(pingtimes)
    pingmin = min(pingtimes)
    pingave = sum(pingtimes)/len(pingtimes)
    if pingave == 0:
        status = 2
    elif pingave <= threshold:
        status = 0
    else:
        status = 2

    return {'pingtimes': pingtimes, 'pingmax': pingmax, 'pingmin': pingmin, 'pingave': pingave, 'status':status}


def getiwstatus(interface='wlan0'):
    from subprocess import check_output, PIPE
    iwresult = check_output(['iwconfig', interface], stderr=PIPE)
    resultdict = {}
    for iwresult in iwresult.split('  '):
        if iwresult:
            if iwresult.find(':') > 0:
                datumname = iwresult.strip().split(':')[0]
                datum = iwresult.strip().split(':')[1].split(' ')[0].split('/')[0].replace('"','')
                resultdict[datumname] = datum
            elif iwresult.find('=') > 0:
                datumname = iwresult.strip().split('=')[0]
                datum = iwresult.strip().split('=')[1].split(' ')[0].split('/')[0].replace('"','')
                resultdict[datumname] = datum
    return resultdict


# This was great, but does nto seem to function properly. We are going to have to manually parse
def getifacestatus():
    from pilib import dirs, loglevels
    from iiutilities.utility import log
    import resource.pyiface.iface as pyiface

    allIfaces = pyiface.getIfaces()
    log(dirs.logs.network, 'Got ifaces data. ', 5, loglevels.network)
    ifacesdictarray=[]
    for iface in allIfaces:
        ifacedict = {}
        ifacedict['name'] = iface.name.strip()
        ifacedict['hwaddress'] = iface.hwaddr.strip()
        ifacedict['address'] = iface._Interface__sockaddrToStr(iface.addr).strip()
        ifacedict['ifaceindex'] = str(iface.index).strip()
        ifacedict['bcast'] = iface._Interface__sockaddrToStr(iface.broadaddr).strip()
        ifacedict['mask'] = iface._Interface__sockaddrToStr(iface.netmask).strip()
        ifacedict['flags'] = pyiface.flagsToStr(iface.flags).replace('\n','').replace('\t',' ').strip()
        ifacesdictarray.append(ifacedict)

    return ifacesdictarray


def getifconfigstatus():
    import subprocess
    import pilib
    from iiutilities import utility

    ifconfigdata = subprocess.check_output(['/sbin/ifconfig']).split('\n')
    interfaces = []
    ifaceindex = -1
    blankinterface = {'name':'', 'hwaddress':'', 'address':'', 'ifaceindex':'', 'bcast':'', 'mask': '', 'flags':''}
    for line in ifconfigdata:
        if line.find('Link encap:') >= 0:
            # print('item!')
            ifaceindex += 1
            interfaces.append(blankinterface.copy())
            interfaces[ifaceindex]['ifaceindex'] = str(ifaceindex)
            interfaces[ifaceindex]['name'] = line.split(' ')[0].strip()
            try:
                interfaces[ifaceindex]['hwaddress'] = line.split('HWaddr')[1].strip()
            except:
                # print('error parsing interface - ' + )
                utility.log(pilib.dirs.logs.network, 'Error parsing hwaddress in ifconfig for interface' + interfaces[ifaceindex]['name'], 4, pilib.loglevels.network)

        else:
            if line.find('addr') >= 0:
                items = {}
                splits = line.split(':')
                numitems = len(splits) - 1
                if numitems == 1:
                    items[splits[0].strip()]=splits[1].strip()
                elif numitems == 2:
                    items[splits[0].strip()]= splits[1].split(' ')[0].strip()
                    items[splits[1].split(' ')[-1]] = splits[2].strip()
                elif numitems == 3:
                    items[splits[0].strip()]= splits[1].split(' ')[0].strip()
                    items[splits[1].split(' ')[-1]] = splits[2].split(' ')[0].strip()
                    items[splits[2].split(' ')[-1]] = splits[3].strip()

                if 'inet addr' in items:
                    interfaces[ifaceindex]['address'] = items['inet addr']
                if 'Mask' in items:
                    interfaces[ifaceindex]['mask'] = items['Mask']
                if 'Bcast' in items:
                    interfaces[ifaceindex]['bcast'] = items['Bcast']

    return interfaces


def getwirelessnetworks(interface='wlan0'):
    from subprocess import check_output
    networkresponse = check_output(['iwlist',interface,'scan']).split('\n')
    networks = []
    # print(networkresponse)
    networkindex = -1

    items = ['Address:', 'ESSID:','Protocol:', 'Mode:','Frequency:','Encryption key:', 'Bit Rates:','Extra:','IE: IEEE']
    itemnames = ['address','ssid','protocol','mode','frequency','encryptionkey','bitrates','extra']
    for index, line in enumerate(networkresponse):

        if line.find(' Cell ') >= 0:
            try:
                if network['ssid']:
                    networks.append(network)
            except:
                # no network yet, or no ssid
                pass
            network = {}
            networkindex += 1
        for item, itemname in zip(items, itemnames):
            if line.find(item) >=0:
                try:
                    network[itemname] = line.split(item)[1].replace('"','').strip()
                except:
                    print('error with item: ')
                    print(itemname)
                    print(line)
        if line.find('Signal level')>= 0:
            network['signallevel'] = line.split('Signal level')[1].split('/')[0].replace('=','')

    # catch last one on the way out
    if network['ssid']:
        networks.append(network)
    return networks


def getwpaclientstatus(interface='wlan0'):
    import subprocess
    from pilib import dirs, loglevels
    from iiutilities.utility import log

    resultdict = {}
    try:
        log(dirs.logs.network, 'Attempting WPA client status read for interface ' + interface, 4, loglevels.network)
        result = subprocess.check_output(['/sbin/wpa_cli', 'status', '-i', interface], stderr=subprocess.PIPE)
    except:
        log(dirs.logs.network, 'Error reading wpa client status. Setting error status for systemstatus to catch.', 0, loglevels.network)
        resultdict['wpa_state'] = 'ERROR'
    else:
        log(dirs.logs.network, 'Completed WPA client status read. ', 4, loglevels.network)

        # prune interface ID
        resultitems = result.split('\n')
        for resultitem in resultitems:
            if resultitem.find('=') > 0:
                split = resultitem.split('=')
                resultdict[split[0]] = split[1].strip()
    if 'wpa_state' not in resultdict:
        resultdict['wpa_state'] = 'UNCAUGHT ERROR'
    return resultdict


def gethamachidata():
    from subprocess import Popen, PIPE

    rawoutput = Popen(['hamachi', 'list'], stdout=PIPE)
    output = rawoutput.stdout.read()
    lines = output.split('\n')
    data = lines[0:-1]  # one whitespace line at end
    dictarrays = []
    networks = []
    index = -1
    for row in data:
        #print(str(index) + ' : ' + row)
        # print(row.find('['))
        if row[3] == '[':
            #print("network")
            networks.append({'id':row.split('[')[1].split(']')[0].strip(), 'name':row.split(']')[1].split('capacity')[0].strip()})
            index += 1
            # print(index)
            dictarrays.append([])
        else:
            #print('not network')
            dict = {}

            if row[5] == '*':
                dict['onlinestatus'] = 'online'
            else:
                dict['onlinestatus'] = 'offline'
            dict['name'] = row[21:45].strip()
            dict['id'] = row[7:17].strip()
            dict['hamachiip'] = row[48:64].strip()
            dict['alias'] = row[73:88].strip()
            dict['connipport'] = row[90:100].strip()
            dict['conntype'] = row[135:145].strip()
            dict['connprotocol'] = row[147:151].strip()
            dict['connipport'] = row[152:173].strip()
            dictarrays[index].append(dict)

    return {'networks':networks, 'clients':dictarrays}


def gethamachistatusdata():
    from subprocess import Popen, PIPE
    rawoutput = Popen(['hamachi',], stdout=PIPE)
    output = rawoutput.stdout.read()
    lines = output.split('\n')
    statusdict = {}
    # print(lines)
    for line in lines:
        try:
            split = line.split(':')
            itemname = split[0].strip()
            itemvalue = ':'.join(split[1:]).strip()
            statusdict[itemname] = itemvalue
        except:
            # print('oops')
            pass
    return statusdict


def restarthamachi():
    import subprocess
    from time import sleep
    subprocess.call(['/etc/init.d/logmein-hamachi','restart'])
    sleep(15)
    subprocess.call(['hamachi','login'])
    return


# left here for compatibility
def killhamachi():
    from iiutilities.utility import killprocbyname
    killprocbyname('hamachi')


def checksharemount(sharepath):
    from subprocess import Popen, PIPE

    mountresponse = Popen(['cat', '/proc/mounts'], shell=False, stdout=PIPE)

    linedata = ''
    for line in mountresponse.stdout:
        linedata = linedata + line

    # print(linedata.find(sharepath))
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

# Status codes:
#   First are mapped to standard MB exception codes:
#       0: Everything went fine
#       1: Invalid Function code
#       2: Invalid Address
#       3: Invalid Value
#       4, 5, 6: Invalid Execution
#       7: Unable to connect to host

def messagefrommbstatuscode(code):
    if code == 0:
        message = 'status ok'
    elif code == 1:
        message = 'Invalid Function Code'
    elif code == 2:
        message = 'Invalid Address'
    elif code == 3:
        message = 'Invalid Value'
    elif code in [4, 5, 6]:
        message = 'Invalid MB Execution'
    elif code == 7:
        message = 'Connection Exception'
    return message


def readMBinputs(clientIP, coil, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    result = client.read_discrete_inputs(coil, number)
    client.close()
    try:
        return result.bits[0:number]
    except AttributeError:
        # print('there are no registers!')
        return result


def readMBcoils(clientIP, coil, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient

    client = ModbusTcpClient(clientIP)
    result = client.read_coils(coil, number)
    client.close()
    try:
        return result.bits[0:number]
    except AttributeError:
        # print('there are no registers!')
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
    from resource.pymodbus.client.sync import ModbusTcpClient, ConnectionException

    client = ModbusTcpClient(clientIP)
    values = []
    try:
        rawresult = client.read_holding_registers(register, number)
    except ConnectionException:
        # print('we were unable to connect to the host')
        statuscode = 7
    else:
        # print(rawresult)
        try:
            resultregisters = rawresult.registers
        except AttributeError:
            statuscode = rawresult.exception_code
        else:
            statuscode = 0
            values = resultregisters
    client.close()
    result = {'message': messagefrommbstatuscode(statuscode), 'statuscode': statuscode, 'values':values}
    return result


def readMBinputregisters(clientIP, register, number=1):
    from resource.pymodbus.client.sync import ModbusTcpClient, ConnectionException
    values = []
    client = ModbusTcpClient(clientIP)
    try:
        rawresult = client.read_input_registers(register, number)
    except ConnectionException:
        # print('we were unable to connect to the host')
        statuscode = 7
    else:
        # print(rawresult)
        try:
            resultregisters = rawresult.registers
        except AttributeError:
            statuscode = rawresult.exception_code
        else:
            statuscode = 0
            values = resultregisters
    client.close()
    result = {'message': messagefrommbstatuscode(statuscode), 'statuscode': statuscode, 'values':values}
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
        # print('there are no registers!')
        return result
    except:
        # print('other unhandled error')
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

            # print(sortedaddresses)
            # print(sortedindices)
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