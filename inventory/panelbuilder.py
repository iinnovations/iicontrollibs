#!/usr/bin/python3

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

import inventorylib
from inventorylib import sysvars
from iiutilities.datalib import setprecision


""" These are used multiple places. They will be in the parts inventory meta shortly """

partsaliases = {
        # Enclosures
        'encl_12x12x06':{'partid':'A001', 'pclass':'parts','psubclass':'enclosure'},
        'encl_16x16x06':{'partid':'A002', 'pclass':'parts','psubclass':'enclosure'},
        'encl_20x20x06':{'partid':'A003', 'pclass':'parts','psubclass':'enclosure'},
        'encl_24x20x08':{'partid':'A004', 'pclass':'parts','psubclass':'enclosure'},
        'enclpan_12x12':{'partid':'A901', 'pclass':'parts','psubclass':'enclosure'},
        'enclpan_16x16':{'partid':'A902', 'pclass':'parts','psubclass':'enclosure'},
        'enclpan_20x20':{'partid':'A903', 'pclass':'parts','psubclass':'enclosure'},
        'enclpan_24x20':{'partid':'A904', 'pclass':'parts','psubclass':'enclosure'},

        # Panel label
        'encl_label':{'partid':'Z099', 'pclass':'parts','psubclass':'enclosure'},

        # Power supplies
        'ps24VDC1p4A':{'partid':'H001', 'pclass':'electronics','psubclass':'powersupplies', 'railwidth':3.07},
        'ps5VDC2p4A':{'partid':'H002', 'pclass':'electronics','psubclass':'powersupplies', 'railwidth':0.98},
        'ps24VDC2p5A':{'partid':'H003', 'pclass':'electronics','psubclass':'powersupplies', 'railwidth':0.98},

        # Switches and indicators
        'ledswitch': {'partid': 'K007', 'pclass':'parts','psubclass':'switchesindicators','controlsload': 0.011 * 24/110}, #24V @ 11mA
        'twoposgreen24VLEDswitch': {'partid': 'K005', 'pclass':'parts','psubclass':'switchesindicators','controlsload': 0.011 * 24/110}, #24V @ 11mA
        'twoposswitch':{'partid':'K002', 'pclass':'parts','psubclass':'switchesindicators'},
        'threeposswitch':{'partid':'K001', 'pclass':'parts','psubclass':'switchesindicators'},
        'estop':{'partid':'K030', 'pclass':'parts','psubclass':'switchesindicators'},

        'greendome110VACLED':{'partid':'K060', 'pclass':'parts', 'controlsload': 0.011 * 24/110},
        'reddome110VACLED':{'partid':'K061', 'pclass':'parts', 'controlsload': 0.011 * 24/110},
        'greendome24VDCLED':{'partid':'K080', 'pclass':'parts', 'controlsload': 0.011 * 24/110},
        'reddome24VDCLED':{'partid':'K081', 'pclass':'parts', 'controlsload': 0.011 * 24/110},

        # Software
        'windows7embedded': {'partid': 'SW-W7EMB', 'pclass': 'software', 'psubclass': 'software'},

        # Electronics
        'LOVE4C':{'partid':'E002', 'pclass':'parts', 'psubclass':'electronics', 'controllerload': 5.0/110},
        'LOVE16C':{'partid':'E005', 'pclass':'parts','psubclass':'electronics', 'controllerload': 5.0/110},
        '10inchTS':{'partid':'E104', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.127}, # These are unverified
        '17inchTS':{'partid':'E102', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.273}, # These are unverified

        'cupidbrewpanel':{'partid':'C005', 'pclass':'parts','psubclass':'electronics', 'controllerload': 2.5*5/110},
        'cupidinputmodule':{'partid':'C006', 'pclass':'parts','psubclass':'electronics'},
        'cupidbrewmote':{'partid':'C004', 'pclass':'parts','psubclass':'electronics'},
        'remoteestop':{'partid':'C020', 'pclass':'parts','psubclass':'electronics'},

        'clickplc': {'partid':'E140', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.140 * 24.0/110, 'railwidth':2.11},

        'click8digitalsinkinput': {'partid':'E142', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.030 * 24/110, 'railwidth':1.06},
        'click16digitalsinkinput': {'partid':'E143', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.040 * 24/110, 'railwidth':1.06},
        'click4tcinput': {'partid':'E145', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.025 * 24.0/110, 'railwidth':1.06},
        'click4rtdinput': {'partid':'E146', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.025 * 24.0/110, 'railwidth':1.06},
        'click4analogvoltageinput': {'partid':'E148', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.023 * 24.0/110, 'railwidth':1.06},
        'click8digitalsourceoutput': {'partid':'E150', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.050 * 24.0/110, 'railwidth':1.06},
        'click16digitalsourceoutput': {'partid':'E151', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.080 * 24.0/110, 'railwidth':1.06},
        'click4isorelayoutput': {'partid':'E153', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.100 * 24.0/110, 'railwidth':1.06},
        'click8isorelayoutput': {'partid':'E154', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.100 * 24.0/110, 'railwidth':1.06},
        'click4analogvoltageoutput': {'partid':'E155', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.020 * 24.0/110, 'railwidth':1.06},

        'enetswitch': {'partid':'E130', 'pclass':'parts','psubclass':'electronics', 'controllerload': 0.09 * 24/110, 'railwidth':1.19},
        'usbantwifi':{'partid':'D010', 'pclass':'parts','psubclass':'electronics'},
        '916ant':{'partid':'D002', 'pclass':'parts','psubclass':'electronics'},
        'smacable':{'partid':'D020', 'pclass':'parts','psubclass':'electronics'},
        'rpsmacable':{'partid':'D021', 'pclass':'parts','psubclass':'electronics'},

        '3P25Adisco':{'partid':'K010', 'pclass':'parts','psubclass':'switchesindicators'},
        'blkreddiscohandle':{'partid':'K016', 'pclass':'parts','psubclass':'switchesindicators'},
        '180mmdiscoshaft':{'partid':'K020', 'pclass':'parts','psubclass':'switchesindicators'},

        'speedpot':{'partid':'K121', 'pclass':'parts','psubclass':'electronics'},
        'leveltimer':{'partid':'F040', 'pclass':'parts','psubclass':'electronics'},

        '1p5TC8inTWRTD_20ft':{'partid':'S003', 'pclass':'parts','psubclass':'sensors'},
        'plainrtd':{'partid':'S001', 'pclass':'parts','psubclass':'sensors'},
        'rtdwithhead':{'partid':'S004', 'pclass':'parts','psubclass':'sensors'},
        'opticallevelsensor':{'partid':'S012', 'pclass':'parts','psubclass':'sensors'},
        'tuningforklevelsensor':{'partid':'S011', 'pclass':'parts','psubclass':'sensors'},
        'mechanicallevelsensor':{'partid':'S017', 'pclass':'parts','psubclass':'sensors'},
        'thermallevelsensor':{'partid':'S015', 'pclass':'parts','psubclass':'sensors'},

        'connectionhead':{'partid':'U110', 'pclass':'parts','psubclass':'sensors'},
        'connectionheadtb':{'partid':'U113', 'pclass':'parts','psubclass':'sensors'},

        # VFDs
        'VFD-1HP-2083P' :{'partid':'VFD-1HP-2083P', 'pclass':'pumps', 'psubclass':'vfds'},
        'VFD-2HP-2083P' :{'partid':'VFD-2HP-2083P', 'pclass':'pumps', 'psubclass':'vfds'},
        'VFD-3HP-2083P' :{'partid':'VFD-3HP-2083P', 'pclass':'pumps', 'psubclass':'vfds'},
        'VFD-5HP-2083P' :{'partid':'VFD-5HP-2083P', 'pclass':'pumps', 'psubclass':'vfds'},

        # TBs, etc
        'dltb':{'partid':'U001', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.2},
        'dltbgnd':{'partid':'U002', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.2},
        'sltb':{'partid':'U010', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.2},
        'sltbgnd':{'partid':'U010', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.2},
        'cbtb':{'partid':'U020', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.32},
        'tbendstop':{'partid':'U070', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.37},

        'tblabel1-10':{'partid':'U060', 'pclass':'parts','psubclass':'terminals'},
        'tblabel11-20':{'partid':'U061', 'pclass':'parts','psubclass':'terminals'},
        'tblabel21-30':{'partid':'U062', 'pclass':'parts','psubclass':'terminals'},
        'tblabel31-40':{'partid':'U063', 'pclass':'parts','psubclass':'terminals'},
        'tblabel41-50':{'partid':'U064', 'pclass':'parts','psubclass':'terminals'},
        'tblabel51-60':{'partid':'U065', 'pclass':'parts','psubclass':'terminals'},

        'dltbendcover':{'partid':'U003', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.09},
        'sltbendcover':{'partid':'U012', 'pclass':'parts','psubclass':'terminals', 'railwidth':0.09},

        'dinrail':{'partid':'Z001', 'pclass':'parts','psubclass':'terminals'},
        'twoinchduct':{'partid':'Y003', 'pclass':'parts','psubclass':'terminals'},
        'twoinchductcover':{'partid':'Y013', 'pclass':'parts','psubclass':'terminals'},

        # Relays, etc.
        'dpdtrelay':{'partid':'F030', 'pclass':'parts','psubclass':'relays', 'railwidth':0.64},

        'dpdtcuberelay':{'partid':'F001', 'pclass':'parts','psubclass':'relays', 'controlsload': 0.037 * 24/110},
        'dpdtcubesocket':{'partid':'F002', 'pclass':'parts','psubclass':'relays','railwidth':0.22},
        'dpdtcubespring':{'partid':'F003', 'pclass':'parts','psubclass':'relays'},

        '4pdtcuberelay':{'partid':'F004', 'pclass':'parts','psubclass':'relays', 'controlsload': 0.037 * 24/110},
        '4pdtcubesocket':{'partid':'F005', 'pclass':'parts','psubclass':'relays','railwidth':0.22},
        # '4pdtcubespring':{'partid':'F006', 'pclass':'parts','psubclass':'relays'},

        'spdttbrelay':{'partid':'F020', 'pclass':'parts','psubclass':'relays', 'railwidth':0.22, 'controlsload': 0.009 * 24/110},

        # Protection
        '1Atbcb':{'partid':'B010', 'pclass':'parts','psubclass':'protection'},
        '2Atbcb':{'partid':'B011', 'pclass':'parts','psubclass':'protection'},
        '3Atbcb':{'partid':'B012', 'pclass':'parts','psubclass':'protection'},
        '4Atbcb':{'partid':'B013', 'pclass':'parts','psubclass':'protection'},
        '6Atbcb':{'partid':'B014', 'pclass':'parts','psubclass':'protection'},
        '8Atbcb':{'partid':'B015', 'pclass':'parts','psubclass':'protection'},
        '10Atbcb':{'partid':'B016', 'pclass':'parts','psubclass':'protection'},

        '10ACB':{'partid':'B105', 'pclass':'parts','psubclass':'protection'},
        '15ACB':{'partid':'B106', 'pclass':'parts','psubclass':'protection'},
        '20ACB':{'partid':'B107', 'pclass':'parts','psubclass':'protection'},
        '25ACB':{'partid':'B100', 'pclass':'parts','psubclass':'protection'},

        # Labor
        'laborpanelfab':{'partid':'L001', 'pclass':'labor'},
        'laborprog':{'partid':'L002', 'pclass':'labor'},
        'laborcommissioning':{'partid':'L006', 'pclass':'labor'},
        'laborengineering':{'partid':'L005', 'pclass':'labor'}
        }


def addincpartsdicts(componentdicts, modpartid, inc=1, **kwargs):

    # Sometimes we forget to make these lists.
    if type(componentdicts) != type([]):
        componentdicts = [componentdicts]

    for componentdict in componentdicts:
        if modpartid in componentdict:
            componentdict[modpartid]['qty'] += inc
        else:
            componentdict[modpartid] = {'qty':inc}
    
        # kwargs contains other fields we want to add. They are just updated.
        if kwargs:
            if 'qty' in kwargs:
                # protect against overwriting quantity
                del kwargs['qty']
            if 'partid' in kwargs:
                # protect against overwriting quantity
                del kwargs['partid']
            componentdict[modpartid].update(kwargs)


def addincpartslist(partslist, partid, inc=1.0, **kwargs):
    if any(part['partid'] == partid for part in partslist):
        for index, part in enumerate(partslist):
            if part['partid'] == partid:
                partslist[index]['qty'] += inc
                if 'addprops' in kwargs:

                    # merge additional properties to be added
                    partslist[index] = kwargs['addprops'].update(partslist[index])

    else:
        partslist.append({'partid': partid, 'qty': inc})

    return partslist


def flattenbomdicttobom(bomdict):
    bom = []
    for partid, items in bomdict.items():
        # print(partid, items)
        items['partid'] = partid
        # print(items)
        bom.append(items.copy())

    # Sort by partid
    sortedbom = sorted(bom, key=lambda k: k['partid'])

    return sortedbom


def calcloads(componentsdict, partsdict, loadtypes):
    # print('we are starting with loads .. ')
    # for loadtype in loadtypes:
    #     print(loadtype,componentsdict['loads'][loadtype])
    for component in componentsdict:
        if component in partsdict:
            for loadtype in loadtypes:
                if loadtype in partsdict[component]:
                    componentsdict['loads'][loadtype] += partsdict[component][loadtype]


def componentsdicttobomdict(componentsdict, bomdict):

    message = ''
    # we are going to grab all the fields, including classes. This also means we can add directly to the bomdict,
    # as long as we include classes.
    for component, data in componentsdict.items():
        if component in partsaliases:
            # print(component,data)
            # We want to rettain component data from the componentsdict (this is where we add options data)
            # and also data that is contained in partsaliases (this is where we keep load data)
            # We will will let the components dict supersede, allowing the defaults to be overriden (partsaliases are
            # considered the defaults) We will remove quantity data, however

            cleanbomdata = data.copy()
            del cleanbomdata['qty']
            partsaliases[component].update(cleanbomdata)

            addincpartsdicts([bomdict], partsaliases[component]['partid'], data['qty'], **cleanbomdata)

        else:
            message += 'Component ' + component + ' not found. '

    return {'message':message}


def priceoptions(optionsdict):

    # print(optionsdict)
    for key, value in optionsdict.items():
        # print(key)
        pass
    # {'myoptionname',
    #       'bom': {
    #           'partid',
    #               {'qty':2, 'class':'someclassname'}
    #           'partid',
    #               {'qty':2, 'class':'someclassname'}
    #           'partid',
    #               {'qty':2, 'class':'someclassname'}
    #       },
    #       'price':123,34,
    #       'cost':123.55
    optionscalcs = {}

    for optionname, optiondata in optionsdict.items():

        flatoptionsbom = flattenbomdicttobom(optiondata['bom'])

        inventorylib.backfillbomfromstock(flatoptionsbom, recalc=True)

        try:
            optioncalcs = inventorylib.calcbomprice({'bomdictarray':flatoptionsbom})
        except:
            print('there was a problem with the optionsbom: ' + optionname )
            # print(flatoptionsbom)

        optionsdict[optionname]['cost'] = optioncalcs['data']['totalcost']
        optionsdict[optionname]['price'] = optioncalcs['data']['totalprice']
        optionsdict[optionname]['flatbom'] = flatoptionsbom

        # We operated on the optionsdict in place by reference ...


def calcrailandduct(componentsdict, optiondict=None):

    raillength = 0
    for compname, compitem in componentsdict.items():
        if compname in partsaliases:
            if 'railwidth' in partsaliases[compname]:
                # print(compname, componentsdict[compname]['qty'], partsaliases[compname]['railwidth'], componentsdict[compname]['qty']*partsaliases[compname]['railwidth'])
                # print(float(componentsdict[compname]['qty'] * partsaliases[compname]['railwidth']) / 12)
                raillength += float(componentsdict[compname]['qty'] * partsaliases[compname]['railwidth']) / 12

    from math import ceil

    # 25% fudge factor for length and scrap
    raillength = setprecision(raillength * 1.25, 2)

    # print('RAILLENGTH = ' + str(raillength))

    addincpartsdicts([componentsdict], 'dinrail', raillength)
    if optiondict:
        addincpartsdicts([optiondict], 'dinrail', raillength)

    # duct is about 2x din rail
    addincpartsdicts([componentsdict], 'twoinchduct', 2 * raillength)
    addincpartsdicts([componentsdict], 'twoinchductcover', 2 * raillength)

    if optiondict:
        addincpartsdicts([optiondict], 'twoinchduct', 2 * raillength)
        addincpartsdicts([optiondict], 'twoinchductcover', 2 * raillength)


def handlecard(componentsdict, custoptions, pointname, cardname, cardpointcount, qtypercount=1):

    # This requires that we have added the component to the custoptions dict.

    # qty per count is if we need to add fractional per unit costs, i.e. to install 1 card, it takes half a unit
    # of labor. So we used the discrete numcards, then multiply times the number per card

    if pointname in componentsdict:
        from math import ceil
        # Determine how many card we need
        requiredinputs = float(componentsdict[pointname]['qty'])
        numcards = float(ceil(float(requiredinputs)/cardpointcount))

        # print(pointname,'points:',requiredinputs,'cards:',numcards)

        # Assign fractional value for options price calcs
        for optionname, optionvalue in custoptions.items():
            if pointname in optionvalue['bom']:
                # What fraction of the cards are attributed to this option
                fractionofcards = setprecision(optionvalue['bom'][pointname]['qty'] / requiredinputs, 2)
                # print('fractional',optionname,optionvalue['bom'][pointname]['qty'], requiredinputs, fractionofcards)

                addincpartsdicts([custoptions[optionname]['bom']], cardname, numcards * fractionofcards * qtypercount)
                # custoptions[optionname]['bom'][cardname] += numcards * fractionofcards

        addincpartsdicts([componentsdict], cardname, numcards * qtypercount)


def handlelevel(componentsdict, custoptions, leveltype, interfacetype, optionname):

    # Parts common to all level interfaces and sensors
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 3)

    # Parts common to all level sensors

    if interfacetype in ['4C', '16C']:
    # Std option
        for adddict in componentsdict, custoptions[optionname]['bom']:
            # for cupid interface
            addincpartsdicts(adddict, 'sltb', 2)
            addincpartsdicts(adddict, 'dpdtrelay')
            addincpartsdicts(adddict, 'greendome24VDCLED')
            addincpartsdicts(adddict, 'laborpanelfab', 1.25)
            addincpartsdicts(adddict, 'laborengineering', 0.25)
            addincpartsdicts(adddict, 'laborcommissioning', 0.25)

    elif interfacetype in ['10inchTS', '17inchTS']:
    # TS option
        for adddict in componentsdict, custoptions[optionname]['bom']:
            # 24VDC output to output relay is on card
            addincpartsdicts(adddict, 'digitalsourceoutput')
            addincpartsdicts(adddict, 'digitalsinkinput')

            # input/output install
            addincpartsdicts(adddict, 'laborpanelfab', 0.25)

            # Drawing work
            addincpartsdicts(adddict, 'laborengineering', 0.25)

            # Setup
            addincpartsdicts(adddict, 'laborcommissioning', 0.25)

            # Timer is handled internally
            # Cupid reads status from PLC

    if leveltype in ['optical','opticalwithtimer']:
        addincpartsdicts([componentsdict,custoptions[optionname]['bom']], 'opticallevelsensor')
    elif leveltype in ['mechanical', 'mechanicalwithtimer']:
        addincpartsdicts([componentsdict,custoptions[optionname]['bom']], 'mechanicallevelsensor')
        addincpartsdicts([componentsdict,custoptions[optionname]['bom']], 'connectionhead')
        addincpartsdicts([componentsdict,custoptions[optionname]['bom']], 'connectionheadtb')
    elif leveltype in ['tuningfork', 'tuningforkwithtimer']:
        addincpartsdicts([componentsdict,custoptions[optionname]['bom']], 'tuningforklevelsensor')

    if leveltype in ['mechanicalwithtimer', 'opticalwithtimer', 'tuningforkwithtimer']:

        # Only add if not touchscreen. If TS, just add commissioning time
        if interfacetype in ['4C', '16C']:
            addincpartsdicts([componentsdict,custoptions[optionname]['bom']],'leveltimer', option=optionname)

            for adddict in componentsdict, custoptions[optionname]['bom']:

                # for cupid interface
                addincpartsdicts(adddict, 'dltb', 2)
                addincpartsdicts(adddict, 'sltb', 1)
                addincpartsdicts(adddict, 'laborpanelfab', 0.25)
                addincpartsdicts(adddict, 'laborengineering', 0.25)
                addincpartsdicts(adddict, 'laborcommissioning', 0.25)
        else:
            for adddict in componentsdict, custoptions[optionname]['bom']:

                # Timer is all in PLC
                addincpartsdicts(adddict, 'laborengineering', 0.25)
                addincpartsdicts(adddict, 'laborcommissioning', 0.25)


def processaccessories(paneldesc, accessories, componentsdict, custoptions):
    statusmessage = ''
    bomdescription = ''

    for accessory in accessories:
        if accessory['itemname'] in paneldesc:
            try:
                numberitems = int(paneldesc[accessory['itemname']])

                if numberitems > 0:

                    optionname = accessory['itemdesc'] + ' (' + str(numberitems) + ')'
                    custoptions[optionname] = {'bom':{}}

                    bomdescription += optionname + '\n\r'

                    for itemlistitem in accessory['itemlist']:
                        if 'qty' in itemlistitem:
                            try:
                                peritemqty = float(itemlistitem['qty'])
                            except:
                                print('OOPS ON QTY')
                                peritemqty = 1.0
                        else:
                            peritemqty = 1.0

                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], itemlistitem['alias'], numberitems * peritemqty)

            except:
                statusmessage += 'There was a problem with the entry ' + accessory['itemname'] + '. '

    return {'statusmessage':statusmessage, 'bomdescription':bomdescription}


def paneltobom(**kwargs):
    """
    This function is designed to take a panel specification and convert it to a bom.
    Another (existing) function will then take this BOM and convert it to price.

    The main purpose of this is to take a basic specification like "I need three controllers, a few switches, a couple
    pump controls, with the ability to control stack and fan" from the webUI (or elsewhere) and turn it into a
    complete list of part and labor required for the panel. This will do stuff like determine the number of PLC inputs,
    return free/available inputs, size enclosure, size and spec DC power supplies, etc.

    We use two dictionaries here. One is a componentsdict, which has common names for things, like 'opticallevel' or
    'isorelayoutput' or 'reddome24vdcled'. We use these so that at the end we can switch them into part numbers. This
    has the dual benefits of making it clear what we are adding, and also leaving one place at the end where we can
    change the part numbers we use for each function. So, for example, when we decide to use a different part for an
    optical switch, we don't have to run through this whole thing and swap out part definitions. Just one place.

    Bomdict also contains meta such as loads for load analysis, and other details that we may need to use for sizing
    and spec.

    To generate print and quote versions, we will produce a hierarchical set of data to describe it:

    Description:
    {'name':'section name',
     'price':'1.00',
     'stuff':'things'
     'children': [
        {
        'name':'child section name',
        'price':'0.50',
        'smallerstuff':'smallerthings',
        'children': [
            {
            'name':'child 2 section name',
            'price':'0.50',
            'smalleststuff':'smallestthings'
            }
            ]
        },
        {
        'name':'child section name',
        'price':'0.50',
        'smallerstuff':'smallerthings',
        'children': [
            {
            'name':'child 2 section name',
            'price':'0.50',
            'smalleststuff':'smallestthings'
            }
            ]
        }]
    }

    Using this, we can print as deep or shallow as we want.

    ** Options:
        Customer wants to see what additional options cost.

        We are going to do this in two ways:

        1. Tag componentsdict and bomdict items with metadata 'option'. This allows us to do it inline with bom additions
           It will also allow us to determine what has not been assigned an option, and put it in a default bucket.

        2. Create an optionsdict, called 'custoptions', where we can create arbitrary options. This will be good if we
           want to do comparisons. For example, if we want a 'touchscreen upgrade' option to display, we would add
           the necessary components, but then also do negative qty of those we don't need.


    custoptions =
    {'myoptionname': {
          'price':1323.45,
          'bom':
             << componentdict >>
    }
    componentsdict (as above)
    {   'anexamplepartid',
            {'qty':18, 'pclass':'parts','psubclass':'specialparts'}
        'anexamplepartid',
            {'qty':18, 'pclass':'parts','psubclass':'specialparts'}
    }


    """

    interfacetypes = ['4C', '16C', '10inchTS', '17inchTS']
    vesselcontroltypes = ['monitor', 'acoutput', 'dcoutput', 'thermostat']
    outputtypes = ['24VDC1A', '110VAC0p5A', 'dry', 'isocardrelay', 'isoextrelay']
    vfdsizes = ['1HP', '2HP', '3HP', '5HP']
    motorcontroltypes = ['vfdonly', 'onoffcontactoroverload', 'vfdpanelonoff', 'vfdpanelonoffspeed',
                         'vfdpanelonoffreverse', 'vfdpanelonoffspeedreverse']
    leveltypes = ['opticalwithtimer', 'mechanicalwithtimer', 'mechanical', 'optical', 'tuningforkwithtimer', 'tuningfork']

    # Defaults

    # Standard controller panel
    # paneldesc = {'paneltype': 'brewpanel',
    #             'panelfinish': 'greystd',
    #             'interfacetype': '4C',
    #             'vessels': [
    #                 {'name': 'HLT', 'controltype': 'acoutput', 'highlevel': None, 'lowlevel': None, 'tempsensor':'1p5TC8inTWRTD_20ft'},
    #                 {'name': 'MLT', 'controltype': 'acoutput', 'highlevel': None, 'lowlevel': None, 'tempsensor':'1p5TC8inTWRTD_20ft'},
    #                 {'name': 'Kettle', 'controltype': 'acoutput', 'highlevel': None, 'lowlevel': None, 'tempsensor':'1p5TC8inTWRTD_20ft'}
    #             ],
    #             'pumps': [
    #                 {'name': 'Pump 1', 'size': '1HP', 'controltype': 'vfdpanelonoff'},
    #                 {'name': 'Pump 2', 'size': '2HP', 'controltype': 'vfdpanelonoffreverse'},
    #                 {'name': 'Pump 3', 'size': '1HP', 'controltype': 'vfdpanelonoffspeed'},
    #                 {'name': 'Pump 4', 'size': '1HP', 'controltype': 'vfdpanelonoffreversespeed'}
    #             ],
    #             }
    paneldesc = {'pumps':[], 'vessels':[]}

    output = {'message':''}

    # Update with defaults
    if 'paneldesc' in kwargs:
        paneldesc.update(kwargs['paneldesc'])
    else:
        output['message'] += 'No paneldesc provided in arguments. Using default values. Hopefully you are testing. '

    componentsdict = {}
    bomdict = {}
    custoptions = {}

    bomdescription = ''
    bomhdescription = {'name':'Our Neat-o BOM'}

    """
    Loads. By default, these panels have three breakers:
    * Controllers - this is the controllers, PLC (just the CPU and logic, not IO), and/or screen.
        We keep these separate in case things get shorted out in the controls
    * Controls - DC PS responsible for powering all relay coils and requisite PS, FP LEDs, etc.
    * Outputs - Solenoids, Aux outputs, etc.

    All load units are in AC
    """


    loadtypes = ['controllerload', 'controlsload', 'outputsload']
    componentsdict['loads'] = {}
    for loadtype in loadtypes:
        componentsdict['loads'][loadtype] = 0.0

    # Add controls for all vessels. Do this here to control options
    numvessels = len(paneldesc['vessels'])

    optiondesc = 'Control interface: ' + paneldesc['interfacetype'] + ': ' + str(numvessels) + ' vessels'
    bomdescription += optiondesc + '\n'

    optionname = optiondesc
    custoptions[optionname] = {'bom':{}}

    # Controls 24VDC PS
    if paneldesc['interfacetype'] in ['4C', '16C']:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'ps24VDC1p4A', pclass='electronics',psubclass='powersupplies')
    else:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'ps24VDC2p5A', pclass='electronics',psubclass='powersupplies')

    if paneldesc['paneltype'] == 'brewpanel':

        # CuPID standard on brewpanel
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'cupidbrewpanel')

        # CuPID PS
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'ps5VDC2p4A')

        # IO for non-TS unit
        if paneldesc['interfacetype'] in ['4C', '16C']:
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'cupidinputmodule')
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.5)
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.5)
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 0.5)

    elif paneldesc['paneltype'] == 'temppanel':

        if paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'cupidbrewpanel')

        elif paneldesc['interfacetype'] in ['4C', '16C']:

            # CuPID remote for temppanel
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'cupidbrewpanel')

    # Commissioning time
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 2)

    # CuPID WiFi and cable
    # These are included in the brewpanel CuPID model
    # addincpartsdict(componentsdict, 'usbantwifi', option='CuPID')
    # addincpartsdict(componentsdict, 'smacable', option='CuPID')

    if paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'clickplc', option=optionname)

        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enetswitch', option=optionname)

        if paneldesc['interfacetype'] == '10inchTS':
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], '10inchTS', option=optionname)
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'windows7embedded', option=optionname)

        if paneldesc['interfacetype'] == '17inchTS':
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], '17inchTS', option=optionname)
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'windows7embedded', option=optionname)

    if paneldesc['interfacetype'] in ['4C', '16C']:

         # Time to install controllers in panel, wire.
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 3*numvessels, option=optionname)

        # Time for commissioning
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning',0.25*numvessels, option=optionname)

        if paneldesc['interfacetype'] == '4C':
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'LOVE4C', numvessels, option=optionname)

        elif paneldesc['interfacetype'] == '16C':
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'LOVE16C', numvessels, option=optionname)

    elif paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:

        # Time to install touchscreen in panel
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 1.25, option=optionname)

        # labor for commissioning screen, PLC
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 3, option=optionname)


    # Add basic options
    # RTD TBs
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'sltb', 3*numvessels)

    # RS485 TBs
    if paneldesc['interfacetype'] in ['4C', '16C']:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'sltb', 2)

        # Somehow need a way to attribute PLC options to TS option ... call it PLC/TS?

    for vessel in paneldesc['vessels']:
        print(vessel)
        bomdescription += 'Control vessel: ' + vessel['name'] + ' : ' + vessel['controltype'] + '\n\r'

        if 'tempsensor' in vessel and vessel['tempsensor'] == '1p5TC8inTWRTD_20ft':
            optionname = vessel['name'] + ' Temp sensor'
            custoptions[optionname] = {'bom':{}}
            bomdescription += '\t' + ' 1.5" TC RTD, 8in TW, 20ft cable ' + '\n\r'
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], '1p5TC8inTWRTD_20ft', option=optionname)

        # Control portion
        optionname = vessel['name'] + ' control' + ': ' + vessel['controltype']
        custoptions[optionname] = {'bom':{}}

        # Unconditional components
        if paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'rtdinput', option=optionname)

        # Add control components
        if vessel['controltype'] in ['acoutput', 'dcoutput', 'thermostat']:
            # optionname = vessel['name'] + ' output' + ': ' + vessel['controltype']
            # custoptions[optionname] = {'bom':{}}

            # TBs
            #   DL : one switch/coil, one output contact, one control contact
            #   SL : one for cupid
            # For now, say these are the same for PLC and non-PLC. Pretty close anyway.
            # Relay on these outputs will remain external

            # Loads
            if vessel['controltype'] == 'acoutput':
                # Add 0.5A AC. PLENTY
                componentsdict['loads']['outputsload'] += 0.5
                # print('ADDING AC LOAD')
            elif vessel['controltype'] == 'dcoutput':
                # Add 1.5A DC
                componentsdict['loads']['outputsload'] += 1.5 * 24 / 110
                # print('ADDING DC LOAD')

            # else ... totally unknown.


            # This accounts for wiring relays and such
            # Use dpdt relays for brewpanel
            if paneldesc['paneltype'] == 'brewpanel':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 3, option=optionname)
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 1, option=optionname)
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dpdtrelay', option=optionname)

            # Use spdt relays for temppanel
            elif paneldesc['paneltype'] == 'temppanel':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 1, option=optionname)
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.75, option=optionname)
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'spdttbrelay', option=optionname)

            # Add ground for AC output
            if vessel['controltype'] == 'acoutput':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltbgnd', option=optionname)

            # Outputs, indicators
            if paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'digitalsourceoutput', option=optionname)

            else:
                if paneldesc['paneltype'] == 'brewpanel':

                    # Add FP components
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'threeposswitch', option=optionname)
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'greendome24VDCLED', option=optionname)
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 2, option=optionname)

        if 'highlevel' in vessel and vessel['highlevel'] and vessel['highlevel'] not in ['None','none']:
            optionname = vessel['name'] + ' high level: ' + vessel['highlevel']
            custoptions[optionname] = {'bom':{}}
            bomdescription += '\tHigh level: ' + vessel['highlevel'] + '\n\r'

            handlelevel(componentsdict, custoptions, vessel['highlevel'], paneldesc['interfacetype'], optionname)

        if 'lowlevel' in vessel and vessel['lowlevel'] and vessel['lowlevel'] not in ['none','None']:
            optionname = vessel['name'] + ' low level: ' + vessel['lowlevel']
            custoptions[optionname] = {'bom': {}}
            bomdescription += '\tLow level: ' + vessel['lowlevel'] + '\n\r'

            handlelevel(componentsdict, custoptions, vessel['lowlevel'], paneldesc['interfacetype'], optionname)

    for pump in paneldesc['pumps']:
        if pump['size'] and pump['controltype']:
            pumpselected = (pump['size'] not in ['none', 'None'] or pump['controltype'] not in ['none', 'None'])
        else:
            pumpselected = False

        if pumpselected:
            bomdescription += 'Pump: ' + pump['name'] + '\n\r'
            if pump['size'] not in ['none', 'None']:
                optionname = 'Pump: ' + pump['name'] + ': ' + pump['controltype'] + ' ' + pump['size']
            else:
                optionname = 'Pump: ' + pump['name'] + ': ' + pump['controltype'] + ' (no VFD)'
            custoptions[optionname] = {'bom':{}}

            # Add VFD
            if pump['size'] == '1HP':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'VFD-1HP-2083P')
            elif pump['size'] == '2HP':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'VFD-2HP-2083P')
            elif pump['size'] == '3HP':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'VFD-3HP-2083P')
            elif pump['size'] == '5HP':
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'VFD-5HP-2083P')

            if pump['controltype'] in motorcontroltypes:


                if pump['controltype'] in ['vfdpanelonoff', 'vfdpanelonoffspeed', 'vfdpanelonoffreverse',
                             'vfdpanelonoffspeedreverse']:

                    # On/off (all vfd types)
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 3)

                    if paneldesc['interfacetype'] in ['4C', '16C']:
                        # Pump disable contact
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'disablecontact', option=optionname)
                        # Disable contact tb
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', option=optionname)
                        # Disable contact wiring
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.25, option=optionname)

                        # FP switch
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'ledswitch')
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 1.25)
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.25)
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 0.5)

                    elif paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'isooutput')
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.25)
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.25)
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 0.5)

                    # Speed control
                    if pump['controltype'] in ['vfdpanelonoffspeed', 'vfdpanelonoffspeedreverse']:
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 3)

                        if paneldesc['interfacetype'] in ['4C', '16C']:
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'speedpot')
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.75)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.25)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 0.5)

                        elif paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'analogvoltageoutput')
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.25)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.1)

                    # Reverse
                    if pump['controltype'] in ['vfdpanelonoffreverse', 'vfdpanelonoffspeedreverse']:
                        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 2)

                        if paneldesc['interfacetype'] in ['4C', '16C']:
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'twoposswitch')
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.75)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.25)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborcommissioning', 0.25)

                        elif paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'isooutput')
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.25)
                            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborengineering', 0.1)

                elif pump['controltype'] in ['onoffcontactoroverload']:
                    # Add contactor, overload, etc.
                    pass
            else:
                output['message'] += 'Control type for ' + pump['name'] + ' : ' + pump['controltype'] + ' not found. '

    """
    Enclosure
    # TODO: Size enclosure
    # TODO: Add SS option
    """


    optionname = 'Enclosure with fab, hardware'
    custoptions[optionname] = {'bom': {}}

    # This labor accounts for basic handling, setup

    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 2)

    if paneldesc['paneltype'] == 'brewpanel':
        if paneldesc['interfacetype'] in ['4C', '17inchTS']:
            if paneldesc['panelfinish'] == 'greystd':

                # Should be provision for 20x20 in here if we want it ...

                bomdescription += 'Enclosure: 24x20x8, grey paint finish \n\r'

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_24x20x08')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_24x20')

            elif paneldesc['panelfinish'] == 'stainless':

                # Should be provision for 20x20 in here if we want it ...
                # THIS DOES NOT EXIST (no SS enclosure in this dimension yet)

                bomdescription += 'Enclosure: 24x20x8, stainless steel \n\r'

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_24x20x08SS')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_24x20')

        elif paneldesc['interfacetype'] in ['16C', '10inchTS']:
            if paneldesc['panelfinish'] == 'greystd':
                bomdescription += 'Enclosure: 20x20x6, grey paint finish \n\r'

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_20x20')

            elif paneldesc['panelfinish'] == 'stainless':

                bomdescription += 'Enclosure: 20x20x6, stainless steel \n\r'

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06SS')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_20x20')

    if paneldesc['paneltype'] == 'temppanel':
        if paneldesc['interfacetype'] in ['16C']:

            if numvessels in [5] or int(numvessels) < 5:
                # 12 x 12
                if paneldesc['panelfinish'] == 'greystd':

                    bomdescription += 'Enclosure: 12x12x6, grey paint finish \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_12x12x06')

                elif paneldesc['panelfinish'] == 'stainless':

                    bomdescription += 'Enclosure: 12x12x6 stainless \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_12x12x06SS')

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_12x12')

            elif numvessels in [7,8,9,10]:
                # 16 x 16
                if paneldesc['panelfinish'] == 'greystd':
                    bomdescription += 'Enclosure: 16x16x6, grey paint finish \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_16x16x06')

                elif paneldesc['panelfinish'] == 'stainless':
                    bomdescription += 'Enclosure: 16x16x6 stainless \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_16x16x06SS')

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_16x16')

            elif numvessels in [11,12]:
                # 20 x 20
                if paneldesc['panelfinish'] == 'greystd':
                    bomdescription += 'Enclosure: 20x20x6, grey paint finish \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06')
                elif paneldesc['panelfinish'] == 'stainless':
                    bomdescription += 'Enclosure: 20x20x6, stainless \n\r'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06SS')

                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_20x20')

        elif paneldesc['interfacetype'] in ['10inchTS']:

            if numvessels in [5,6]:
                # 16 x 16
                if paneldesc['panelfinish'] == 'greystd':
                    bomdescription += 'Enclosure: 16x16x6, grey paint finish'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_16x16x06')
                elif paneldesc['panelfinish'] == 'stainless':
                    bomdescription += 'Enclosure: 16x16x6, stainless'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_16x16x06SS')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_16x16')

            elif numvessels in [7,8,9,10,11,12,13,14,15,16,17,18,19,20]:
                # 20 x 20
                if paneldesc['panelfinish'] == 'greystd':
                    bomdescription += 'Enclosure: 20x20x6, grey paint finish'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06')
                elif paneldesc['panelfinish'] == 'stainless':
                    bomdescription += 'Enclosure: 20x20x6, stainless'
                    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_20x20x06SS')
                addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'enclpan_20x20')

    if paneldesc['paneltype'] == 'brewpanel':

        # Panel label
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_label', 100)  # THis should be price and not quantity
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.5)

        # E stop
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'estop')
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'greendome24VDCLED')
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'reddome24VDCLED')
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 2)

        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 1)

        if paneldesc['interfacetype'] not in ['10inchTS', '17inchTS']:

            # CuPID Estop TBs
            addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'sltb', 2)

        # Door interlock
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], '3P25Adisco')
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'blkreddiscohandle')
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], '180mmdiscoshaft')

        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.5)

    elif paneldesc['paneltype'] == 'temppanel':

        # Panel label
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'encl_label', 40)  # THis should be price and not quantity
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 0.5)

        # Solenoid enable/disable
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'twoposgreen24VLEDswitch', 1)  # THis should be price and not quantity
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 1)
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'laborpanelfab', 1)

    # Add 4PDT relays for disabling items
    # Need to fractionally attribute. Use our card algorithm
    # Should refactor. number per card at the end can be used as a hack for qty per point.
    # Labor here should just be the flat amount used per relay. Per point costs should be done outside.

    handlecard(componentsdict, custoptions, 'disablecontact', '4pdtcuberelay', 4)
    handlecard(componentsdict, custoptions, 'disablecontact', '4pdtcubesocket', 4)

    # This says that per relay, it will take 1/4hr of engineering and panel fab to put the relay in.
    handlecard(componentsdict, custoptions, 'disablecontact', 'laborpanelfab', 4, qtypercount=0.25)
    handlecard(componentsdict, custoptions, 'disablecontact', 'laborengineering', 4, qtypercount=0.25)

    #
    # from math import ceil
    #
    # if numcontacts > 0:
    #     numrelays = ceil(numcontacts / 4)
    #
    #     addincpartsdict(componentsdict, '4pdtcuberelay', numrelays)
    #     addincpartsdict(componentsdict, '4pdtcuberelaysocket', numrelays)
    #     addincpartsdict(componentsdict, 'dltb', numcontacts)
    #     addincpartsdict(componentsdict, 'laborpanelfab', numcontacts * 0.25)
    #     addincpartsdict(componentsdict, 'laborengineering', numcontacts * 0.25)

    # Power distribution
    # 2 for (post CB) line distribution, 2 for neutral distribution

    optionname = 'Base Panel'
    custoptions[optionname] = {'bom':{}}

    # TODO: Is this only brewpanel?
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltb', 4)
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'dltbgnd', 2)

    # Block labels, accessories
    totaldltb = componentsdict['dltb']['qty'] + componentsdict['dltbgnd']['qty']
    if totaldltb > 0:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel1-10')
    if totaldltb > 10:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel11-20')
    if totaldltb > 20:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel21-30')
    if totaldltb > 30:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel31-40')
    if totaldltb > 40:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel41-50')

    totalsltb = componentsdict['dltb']['qty'] + componentsdict['dltbgnd']['qty']
    if totalsltb > 0:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel1-10')
    if totalsltb > 10:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel11-20')
    if totalsltb > 20:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel21-30')
    if totalsltb > 30:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel31-40')
    if totalsltb > 40:
        addincpartsdicts([componentsdict, custoptions[optionname]['bom']], 'tblabel41-50')

    # Endcovers
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']],'dltbendcover', 2)
    addincpartsdicts([componentsdict, custoptions[optionname]['bom']],'sltbendcover', 2)

    """
    Accessories
    """

    if 'externalloads' in paneldesc:
        pass

    if 'addcontrolchannels' in paneldesc:
        pass


    """
    itemdesc = 'Plain RTDs'     # Desscription for reading
    itemname = 'plainrtds'      # Name in paneldesc variable
    itemlist = {'alias':'plainrtds', 'qty':1}     alias in aliases dict above (will be in inventory database
                                                  eventually) Qty is optional

    qty in itemlist is the number per accessory item. total qty is number of options * per item qty

    This format is pretty nice. We could extend this to many other things, I suppose.
    Some of these items are not compatible with all interfaces. We will have to do the verification client-side
    This makes sense anyway, since we'll have to correct the selection in the UI
    """


    accessories = [
        {'itemdesc':'Remote EStops', 'itemname':'remoteestops',
            'itemlist':[{'alias':'remoteestop'}, {'alias':'dltb','qty':2},
                        {'alias':'laborpanelfab','qty':0.25},
                        {'alias':'laborengineering','qty':0.25},
                        {'alias':'laborcommissioning','qty':0.25}]
         },
        {'itemdesc':'Thermowell RTDs', 'itemname':'twrtds', 'itemlist':[{'alias':'1p5TC8inTWRTD_20ft'}]},
        {'itemdesc':'Plain RTDs', 'itemname':'plainrtds', 'itemlist':[{'alias':'plainrtd'}]}
    ]
    tsonlyaccessories = [
        {'itemdesc':'Additional RTD Inputs', 'itemname':'addtempinputs',
            'itemlist':[{'alias':'rtdinput'},
                        {'alias':'laborpanelfab','qty':0.25},
                        {'alias':'laborengineering','qty':0.25},
                        {'alias':'laborcommissioning','qty':0.25}]
         },
        {'itemdesc':'Accessory Relay loads', 'itemname':'addexternalloads',
            'itemlist':[{'alias':'digitalsourceoutput'},
                {'alias':'dpdtrelay','qty':1},
                {'alias':'laborpanelfab','qty':0.25},
                {'alias':'laborengineering','qty':0.25},
                {'alias':'laborcommissioning','qty':0.25}
            ]
        },
        # This guy is the combination of the temperature input and external load, with a little more time to
        # program the control channel
        {'itemdesc':'Additional Control Channels', 'itemname':'addcontrolchannels',
            'itemlist':[{'alias':'digitalsourceoutput'},
                {'alias':'dpdtrelay','qty':1},
                {'alias':'laborpanelfab','qty':0.25},
                {'alias':'laborengineering','qty':0.25},
                {'alias':'laborcommissioning','qty':0.25},

                {'alias':'rtdinput'},
                {'alias':'laborpanelfab','qty':0.25},
                {'alias':'laborengineering','qty':0.25},
                {'alias':'laborcommissioning','qty':0.25},

                {'alias':'laborcommissioning','qty':0.5}
            ]
        }
    ]

    accresult = processaccessories(paneldesc, accessories, componentsdict, custoptions)
    bomdescription += accresult['bomdescription']

    if paneldesc['interfacetype'] in ['10inchTS', '17inchTS']:
        accresult = processaccessories(paneldesc, tsonlyaccessories, componentsdict, custoptions)
        bomdescription += accresult['bomdescription']


    """
    PLC cards and stuffs

    TODO: Attribute portions of card prices to options (done in handle cards routine)
    """

    # Ok, so we will get card proportions from custoptions dict.
    # We will get a total for each component required, then divide this up into fractions
    # Then we get the actual component count, and divide it among the options by adding it back into the component
    # dictionary.

    cards = [
        {'pointname': 'digitalsourceoutput', 'cardname': 'click16digitalsourceoutput', 'cardpointcount': 16},
        {'pointname': 'digitalsinkinput', 'cardname': 'click16digitalsinkinput', 'cardpointcount': 16},
        {'pointname': 'analogvoltageoutput', 'cardname': 'click4analogvoltageoutput', 'cardpointcount': 4},
        {'pointname': 'isooutput', 'cardname': 'click4isorelayoutput', 'cardpointcount': 4},
        {'pointname': 'rtdinput', 'cardname': 'click4rtdinput', 'cardpointcount': 4}
    ]

    for card in cards:
        handlecard(componentsdict, custoptions,
                   pointname=card['pointname'],
                   cardname=card['cardname'],
                   cardpointcount=card['cardpointcount'])


    """
    Calculate some base and auxiliary quantities
    """

    # Calculate loads
    # print(componentsdict)
    calcloads(componentsdict, partsaliases, loadtypes)

    # Size breakers based on loads
    for loadtype in loadtypes:
        addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], 'cbtb')
        loadmax = componentsdict['loads'][loadtype] * 1.25
        if loadmax < 1:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '1Atbcb')
        elif loadmax < 2:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '2Atbcb')
        elif loadmax < 3:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '3Atbcb')
        elif loadmax < 4:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '4Atbcb')
        elif loadmax < 6:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '6Atbcb')
        elif loadmax < 8:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '8Atbcb')
        elif loadmax < 10:
            addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '10Atbcb')


    # Calculate DIN Rail and wire duct necessary. Add in labor based on these for install

    # DIN rail is per foot. TBs are 0.2" wide


    calcrailandduct(componentsdict, optiondict=custoptions['Base Panel']['bom'])

    """

    Calculate base labor based on panel stuff
    # Engineering, labor, based on base and tb number
    """

    railtoengmultiplier = 1             # Hours per foot
    railtolabormultiplier = 1           # Hours per foot

    raillength = componentsdict['dinrail']['qty']
    addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], 'laborengineering', setprecision(2 + railtoengmultiplier*raillength, 1))
    addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], 'laborpanelfab', 2 + setprecision(railtolabormultiplier*raillength, 2))


    """
    Calculate Panel loading
    """

    componentsdict['loads']['totalload'] = componentsdict['loads']['controllerload'] + \
                                           componentsdict['loads']['controlsload'] + \
                                           componentsdict['loads']['outputsload']

    # Add a UL489 Circuit breaker
    if componentsdict['loads']['totalload'] < 10 / 1.25:
        addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '10ACB')
    elif componentsdict['loads']['totalload'] < 15 / 1.25:
        addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '15ACB')
    elif componentsdict['loads']['totalload'] < 20 / 1.25:
        addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '20ACB')
    else:
        addincpartsdicts([componentsdict, custoptions['Base Panel']['bom']], '25ACB')

    """
    Now convert components to bomdict
    componentsdict ...
    Also need to add a bunch of miscellaneous crap. TB stops, endcaps, DIN Rail. Can think of ad hoc ways of
     calculating this stuff.

    Eventually all of this data will be in the parts database. We'll build it up here to see what works and what doesn't
    """

    convertresponse = componentsdicttobomdict(componentsdict, bomdict)
    output['message'] += convertresponse['message']

    # print(bomdict)
    bom = flattenbomdicttobom(bomdict)
    output['bom'] = inventorylib.backfillbomfromstock(bom, recalc=True)

    output['componentsdict'] = componentsdict

    loadprecision = 2
    bomdescription += 'Loads (A@110VAC) : \r\n'
    bomdescription += '\tController:\t' + str(setprecision(componentsdict['loads']['controllerload'], loadprecision)) + '\r\n'
    bomdescription += '\tControls:\t' + str(setprecision(componentsdict['loads']['controlsload'], loadprecision)) + '\r\n'
    bomdescription += '\tOutputs:\t' + str(setprecision(componentsdict['loads']['outputsload'], loadprecision)) + '\r\n'
    bomdescription += '\tTotal:\t' + str(setprecision(componentsdict['loads']['totalload'], loadprecision)) + '\r\n'

    # TODO: Add DC PS for DC LOADS

    output['bomdescription'] = bomdescription


    """
    Let's summarize the options


    custoptions =
    {'myoptionname': {
          'price':1323.45, # this is not yet implemented. just put into bomdict
          'bom':
             << componentdict >>
    }
    custoptionsbomdict = {
    {'myoptionname':
        'price':1231.34,
        'bom':
           << bomdict >>
    """

    custoptionsbomdict={}
    for key, value in custoptions.items():
        custoptionsbomdict[key] = {'bom':{}}
        componentsdicttobomdict(value['bom'], custoptionsbomdict[key]['bom'])


    priceoptions(custoptionsbomdict)

    output['options'] = custoptionsbomdict

    for key, value in custoptionsbomdict.items():
        # print(key, value['price'])
        pass

    # for key, value in options.items():
    #
    #     # print('*** COMPONENTS VALUE')
    #     optionsbom = {}
    #     componentsdicttobomdict(value, optionsbom)
    #
    #     flatoptionsbom = flattenbomdicttobom(optionsbom)
    #
    #     inventorylib.backfillbomfromstock(flatoptionsbom, recalc=True)
    #
    #     # print('*** flat options bom ***')
    #     # print(flatoptionsbom)
    #     optioncalcs = inventorylib.calcbomprice({'bomdictarray':flatoptionsbom})
    #
    #     # print('*** option calcs')
    #     # print(optioncalcs)
    #     options[key]['cost'] = optioncalcs['data']['totalcost']
    #     options[key]['price'] = optioncalcs['data']['totalprice']
    #     options[key]['flatbom'] = flatoptionsbom
    # output['options'] = options

    """
    Components/bomdict class options method. This has issues. Namely that partials of a component are not
    allowed. Abandoning for now.
    """
    optionsdict= {'Base':{'name':'Base','bom':{}}}
    for item, value in bomdict.items():
        # bomdict is {'U001':{'qty':2, 'option':'stuff'}, 'U002' ...}
        # item is part number. value is the data, including qty and options

        if 'option' in value:
            # print(value['option'])
            if value['option'] not in optionsdict:
                # Add a name in here to help when it comes out as json in ajax
                optionsdict[value['option']] = {'name':value['option'],'bom':{}}
            addincpartsdicts([optionsdict[value['option']]['bom']], item, value['qty'])
        else:
            addincpartsdicts([optionsdict['Base']['bom']], item, value['qty'])

    priceoptions(optionsdict)

    # Now we cave a dict of options.
    # output['options'] = optionsdict

    return output


if __name__ == "__main__":
    output = paneltobom()
    print('*** RESULTS ****')

    if False:
        for item in output['bom']:
            print('item:' ,item)
            print(item['partid'], item['qty'], item['totalcost'],item['totalprice'])
        print('***')
        bomcalcs = inventorylib.calcbomprice({'bomdictarray': output['bom']})
        print(bomcalcs)
        print('*** BOM DESCRIPTION')
        print(output['bomdescription'])

    if False:
        print('*** OPTIONS')
        for option, value in output['options'].items():
            print('OPTION: "' + option + '" $' + str(value['price']) + ' (' + str(value['cost']) + ')')
            print('\t items:')
            for item in value['flatbom']:
                # print('\t item[')
                print('\t(' + str(item['qty']) + ') ' + item['partid'] + '\t\t$' + str(item['totalprice']) + ' (' + str(item['totalcost']) + ')')
        # Put into files
    if True:
        from iiutilities.utility import writetextdoctopdf
        from iiutilities.datalib import gettimestring
        from inventorylib import writepanelbomtopdf, writepanelquotetopdf
        print(output['bom'])
        writepanelbomtopdf(**{'bomdata':output['bom'], 'title': 'panelbuilder BOM', 'outputfile': '/var/www/html/panelbuilder/data/downloads/pbbom.pdf'})
        writepanelquotetopdf(**{'bomdata':output['bom'], 'options':output['options'], 'title': 'Quote auto-generated by panelbuilder ' + gettimestring(),
            'outputfile':'/var/www/html/panelbuilder/data/downloads/pbquote.pdf'})

        writetextdoctopdf(output['bomdescription'], outputfile='/var/www/html/inventory/data/iiinventory/download/pbbomdescription.pdf')

    if False:
        for item, value in output['options'].items():
            print(item, value['price'], value['cost'])
            for optitem, optvalue in value['bom'].items():
                print(optitem, optvalue)
                # print(optitem, optvalue['qty'])