#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2016, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import inspect
import os
import sys

top_folder = \
    os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

"""
This library is for control functions. It has been ignored for some time and probably needs some love
"""

"""
WSGI helper functions
"""


def handle_modify_channel_alarm(d, output):

    import pilib
    from iiutilities import dblib

    output['message'] += 'modifychannelalarm keyword found. '
    required_keywords = ['database', 'valuename', 'value', 'actionname']
    if not all(keyword in d for keyword in required_keywords):
        output['message'] += 'Not all required keywords were found: ' + str(required_keywords) + '. '
        return

    allowed_valuenames = ['enabled', 'PV_low', 'PV_high', 'actiondetail']

    if d['valuename'] not in allowed_valuenames:
        output['message'] += 'Selected valuename is not allowed for this action. '
        return

    dbpath = pilib.dbnametopath(d['database'])
    database = pilib.cupidDatabase(dbpath)

    action_condition = '"name"=\'' + d['actionname'] + "'"
    if d['valuename'] in ['enabled','actiondetail']:

        try:
            if d['valuename'] == 'enabled':
                set_value = int(d['value'])
            else:
                set_value = str(d['value'])
        except:
            output['message'] += 'Missing keys or bad value conversion. '
        else:
            output['message'] += 'Setting value' + str(set_value) + ' with condition ' + action_condition + '. '
            try:
                database.set_single_value('actions',d['valuename'],set_value, action_condition)
            except:
                output['message'] += 'Query error. '
            else:
                output['message'] += 'That appears to have worked. '

    elif d['valuename'] in ['PV_high', 'PV_low']:
        """
        These values have to be set in the options field.
        So we have to pull it out as a json string, put it into a dict, modify values, and then put it back as a string
        """
        from iiutilities.datalib import parseoptions, dicttojson

        optionstring = database.get_single_value('actions','actiondata',action_condition)
        output['message'] += 'Existing options: ' + optionstring + '. '
        options = parseoptions(optionstring)

        try:
            set_value = float(d['value'])
        except:
            output['message'] += 'Bad value conversion. '
            return

        if not d['valuename'] in options:
            output['message'] += 'Valuename does not exist in options. Creating. '

        options[d['valuename']] = set_value

        # Now rewrite to actions
        optionstring = dicttojson(options)
        output['message'] += 'New optionstring: ' + optionstring + '. '
        try:
            database.set_single_value('actions','actiondata',optionstring, action_condition)
        except:
            output['message'] += 'Query error. '
        else:
            output['message'] += 'That appears to have worked. '

    return


def handle_modify_channel(d, output):
    import pilib
    from iiutilities import dblib

    output['message'] += 'modifychannelalarm keyword found. '
    required_keywords = ['database', 'valuename', 'value', 'channelname']
    if not all(keyword in d for keyword in required_keywords):
        output['message'] += 'Not all required keywords were found: ' + str(required_keywords) + '. '
        return

    allowed_valuenames = ['enabled', 'setpointvalue']

    if d['valuename'] not in allowed_valuenames:
        output['message'] += 'Selected valuename is not allowed for this action. '
        return

    dbpath = pilib.dbnametopath(d['database'])
    database = pilib.cupidDatabase(dbpath)

    channel_condition = '"name"=\'' + d['channelname'] + "'"
    if d['valuename'] in allowed_valuenames:

        try:
            if d['valuename'] == 'enabled':
                set_value = int(d['value'])
            else:
                set_value = float(d['value'])
        except:
            output['message'] += 'Missing keys or bad value conversion. '
            return


        """
        For a channel, we will check type. If remote, we set as pending and then initiate processing the channel.

        """
        from iiutilities.datalib import parseoptions, dicttojson

        # Handle error here.
        the_channel = database.read_table('channels',channel_condition)[0]

        if the_channel['type'] == 'remote':
            output['message'] += 'Processing remote channel, setting pending value. '
            print(output['message'])

            if the_channel['pending']:
                pending = parseoptions(the_channel['pending'])
            else:
                pending = {}

            pending[d['valuename']] = set_value
            pending_string = dicttojson(pending)
            try:
                database.set_single_value('channels', 'pending', pending_string, channel_condition)
            except:
                output['message'] +=  'Query error. '
                return
            else:
                output['message'] += 'That appears to have worked. Now running channel processing on channel. '


        else:

            output['message'] += 'Setting local setpoint value. '
            try:
                database.set_single_value('channels','setpointvalue',set_value)
            except:
                output['message'] += 'Query error. '
                return
            else:
                output['message'] += 'That appears to have worked. '

        # Process channel now
        from cupid.picontrol import process_channel
        process_channel(channel_name=d['channelname'])

        # Let's also update the input while we're at it



    return

"""
Control Functions
"""


def runalgorithm(controldbpath, recipedbpath, channelname):
    from iiutilities.datalib import timestringtoseconds, gettimestring
    from iiutilities.dblib import sqlitequery, datarowtodict
    import time

    message = ''

    # get our details of our channel
    channeldata = sqlitequery(controldbpath, 'select * from channels where name=' + "'" + channelname + "'")[0]
    channeldict = datarowtodict(controldbpath, 'channels', channeldata)
    # check to see if we are running a recipe

    controlrecipename = channeldict['controlrecipe']
    if controlrecipename and controlrecipename != 'none':

        # Get recipe details
        # If recipes get too big, we'll just get 
        # a couple stages. For now, we make a 
        # dictionary array

        #print('we are in recipe ' + controlrecipename)
        #print(dirs.dbs.session)

        recipedata = sqlitequery(recipedbpath, 'select * from \'' + controlrecipename + '\'')
        recipedictarray = []

        for stage in recipedata:
            recipedict = datarowtodict(recipedbpath, controlrecipename, stage)
            recipedictarray.append(recipedict)

        # get current stage
        currentstagenumber = int(channeldict['recipestage'])
        #print('current stage is ' + str(currentstagenumber) ) 

        # Get data for current stage
        stagefound = False
        for stage in recipedictarray:
            if int(stage['stagenumber']) == currentstagenumber:
                currentstage = stage
                stagefound = True
                break
        if stagefound:
            #print("stage found")
            pass
        else:
            print('error. stage not found.')

        # Check to see if we need to move to next stage
        currenttime = time.time()
        #print('Time')
        #print(currenttime)
        #print(gettimestring(currenttime)) 

        if currentstagenumber == 0 or currenttime - timestringtoseconds(channeldict['recipestagestarttime']) > int(
                currentstage['stagelength']):
            print('stage time expired for stage ' + str(currentstagenumber) + '. Checking on stage advance. ')

            # Advance stage if there is another stage. Otherwise
            # update channel to be off a recipe. We assume explicitly 
            # that the stages are sequential integers.

            nextstagenumber = currentstagenumber + 1

            # look for next stage

            stagefound = False
            for stage in recipedictarray:
                if int(stage['stagenumber']) == nextstagenumber:
                    nextstage = stage
                    stagefound = True
                    break

            if stagefound:
                print(' Next stage was found. Setting next stage. ')
                if currentstagenumber == 0:
                    print("Stagenumber is 0. Setting recipe start time. ")

                    # Set recipe start time 
                    sqlitequery(controldbpath, 'update channels set recipestarttime=\'' + gettimestring(
                        currenttime) + '\' where name=\'' + channelname + '\'')

                # Set stage to new stage number
                sqlitequery(controldbpath, 'update channels set recipestage=\'' + str(
                    nextstagenumber) + '\' where name=\'' + channelname + '\'')

                # Set setpointvalue
                sqlitequery(controldbpath, 'update channels set setpointvalue=\'' + str(
                    nextstage['setpointvalue']) + '\' where name=\'' + channelname + '\'')

                # Set stage start time to now 
                sqlitequery(controldbpath, 'update channels set recipestagestarttime=\'' + gettimestring(
                    currenttime) + '\' where name=\'' + channelname + '\'')

                # Set new controlalgorithm 
                sqlitequery(controldbpath, 'update channels set controlalgorithm=\'' + nextstage[
                    'controlalgorithm'] + '\' where name=\'' + channelname + '\'')

            else:

                # Take channel off recipe
                sqlitequery(controldbpath,
                            'update channels set controlrecipe=\'none\' where name=\'' + channelname + '\'')
                sqlitequery(controldbpath, 'update channels set recipestate=\'0\' where name=\'' + channelname + '\'')

                sqlitequery(controldbpath,
                            'update channels set recipestage=\'0\' where name=\'' + channelname + '\'')


                # if lengthmode is setpoint

                # get current stage

                # check stage start against stage length
                # and current time

                # move to next stage if time and revise setpoint

                # adjust setpoint based on stage

                # set action based on setpoint

    else:
        # make sure we're not on recipe and on stage 0
        sqlitequery(controldbpath,
                    'update channels set controlrecipe=\'none\' where name=\'' + channelname + '\'')
        sqlitequery(controldbpath, 'update channels set recipestate=\'0\' where name=\'' + channelname + '\'')

        sqlitequery(controldbpath,
                    'update channels set recipestage=\'0\' where name=\'' + channelname + '\'')

    algorithm = channeldict['controlalgorithm']
    setpointvalue = float(channeldict['setpointvalue'])
    controlvalue = float(channeldict['controlvalue'])

    algorithmrows = sqlitequery(controldbpath, 'select * from controlalgorithms where name=' + "'" + algorithm + "'")
    algorithmrow = algorithmrows[0]
    algorithm = datarowtodict(controldbpath, 'controlalgorithms', algorithmrow)
    algtype = algorithm['type']

    if algtype == 'on/off with deadband':
        #print(type) 
        deadbandhigh = algorithm['deadbandhigh']
        deadbandlow = algorithm['deadbandlow']
        if setpointvalue > (controlvalue + deadbandhigh):
            action = 100
        elif setpointvalue < (controlvalue - deadbandlow):
            action = -100
        else:
            action = 0
    #print('setpoint' + str(setpoint))
    #print('controlvalue' + str(controlvalue)) 
    #print(action)
    #print(message)
    return [action, message]


# I think we need a channel class here. Not used yet, but in development.

class channel:
    def __init__(self,propertydict):
        for key,value in propertydict.items():
            setattr(self,key,value)

    def setsetpoint(self,setpointvalue):
        from pilib import dirs
        from iiutilities.dblib import sqlitequery
        sqlitequery(dirs.dbs.control, 'update channels set setpointvalue=\'' + str(setpointvalue) + '\' where name=\'' + channel.name + '\'')

    def setaction(self,action):
         from pilib import dirs
         from iiutilities.dblib import sqlitequery
         sqlitequery(dirs.dbs.control,
            'update channels set action = \'' + str(action) + '\' where name = \'' + channel.name + '\'')

    def setcontrolinput(self,inputid):
        from pilib import dirs
        from iiutilities.dblib import sqlitequery
        sqlitequery(dirs.dbs.control,
                'update channels set controlinput = \'' + inputid + '\' where name = \'' + channel.name + '\'')

    def getaction(self):
        from pilib import dirs
        from iiutilities.dblib import sqlitedatumquery
        self.action = sqlitedatumquery(dirs.dbs.control,'select action from channels where name=\'' + channel.name + '\'')

    def getsetpointvalue(self):
        from pilib import dirs
        from iiutilities.dblib import sqlitedatumquery
        self.setpointvalue = sqlitedatumquery(dirs.dbs.control, 'select setpointvalue from channels where name=\'' + channel.name + '\'')

    def incsetpoint(self):
        self.getsetpointvalue()
        self.setsetpoint(self.setpointvalue+1)

    def decsetpoint(self):
        self.getsetpointvalue()
        self.setsetpoint(self.setpointvalue-1)

    def getmode(self):
        from pilib import dirs
        from iiutilities.dblib import sqlitedatumquery
        self.mode = sqlitedatumquery(dirs.dbs.control, 'select mode from channels where name=\'' + channel.name + '\'')

    def setmode(self,mode):
        from pilib import dirs
        from iiutilities.dblib import sqlitequery
        sqlitequery(dirs.dbs.control, 'update channels set mode=\'' + str(mode) + '\' where name=\'' + channel.name + '\'')

    def togglemode(self,mode):
        from pilib import dirs
        from iiutilities.dblib import sqlitedatumquery
        self.getmode()
        if self.mode == 'manual':
            self.mode = 'auto'
        else:
            self.mode = 'manual'

# This works fine, for now.

def setsetpoint(controldbpath, channelname, setpointvalue):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath, 'update channels set setpointvalue=\'' + str(
        setpointvalue) + '\' where name=\'' + channelname + '\'')


def setaction(controldbpath, channelname, action):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set action = \'' + str(action) + '\' where name = \'' + channelname + '\'')


def setcontrolinput(controldbpath, channelname, inputid):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set controlinput = \'' + inputid + '\' where name = \'' + channelname + '\'')


def setcontrolvalue(controldbpath, channelname, controlvalue):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set controlvalue = \'' + str(controlvalue) + '\' where name = \'' + channelname + '\'')


def getaction(controldbpath, channelname):
    from iiutilities.dblib import sqlitequery

    action = sqlitequery(controldbpath, 'select action from channels where name=\'' + channelname + '\'')[0][0]
    return action


def getsetpoint(controldbpath, channelname):
    from iiutilities.dblib import sqlitequery

    currentsetpoint = \
        sqlitequery(controldbpath, 'select setpointvalue from channels where name=\'' + channelname + '\'')[0][0]
    return currentsetpoint


def decsetpoint(controldbpath, channelname):
    currentsetpoint = getsetpoint(controldbpath, channelname)
    newsetpoint = currentsetpoint - 1
    setsetpoint(controldbpath, channelname, newsetpoint)


def incsetpoint(controldbpath, channelname):
    currentsetpoint = getsetpoint(controldbpath, channelname)
    newsetpoint = currentsetpoint + 1
    setsetpoint(controldbpath, channelname, newsetpoint)


def setmode(controldbpath, channelname, mode):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath, 'update channels set mode=\'' + mode + '\' where name=\'' + channelname + '\'')

    # set action to 0 if we switch to manual
    if mode == 'manual':
        setaction(controldbpath, channelname, 0)


def getmode(controldbpath, channelname):
    from iiutilities.dblib import sqlitequery

    mode = sqlitequery(controldbpath, 'select mode from channels where name=\'' + channelname + '\'')[0][0]
    return mode


def togglemode(controldbpath, channelname):
    from iiutilities.dblib import sqlitequery
    from controllib import setaction

    curmode = getmode(controldbpath, channelname)
    if curmode == 'manual':
        newmode = 'auto'
    else:
        newmode = 'manual'
        setaction(controldbpath, channelname, 0)

    setmode(controldbpath, channelname, newmode)


def checkifenableready(outputname, outputs):
    from time import time
    from iiutilities.datalib import timestringtoseconds

    # Find the variables we want
    for output in outputs:
        if output['name'] == outputname:
            offtime = timestringtoseconds(output['offtime'])
            minofftime = output['minofftime']

    if time() - offtime > minofftime:
        return True
    else:
        return False


def checkifdisableready(outputname, outputs):
    from time import time
    from iiutilities.datalib import timestringtoseconds

    # Find the variables we want
    for output in outputs:
        if output['name'] == outputname:
            minontime = output['minontime']
            ontime = timestringtoseconds(output['ontime'])

    if time() - ontime > minontime:
        return True
    else:
        return False


def setposout(controldbpath, channelname, outputname):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set positiveoutput=\'' + outputname + '\' where name=\'' + channelname + '\'')


def setnegout(controldbpath, channelname, outputname):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set negativeoutput=\'' + outputname + '\' where name=\'' + channelname + '\'')


def setalgorithm(controldbpath, channelname, algorithm):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set controlalgorithm=\'' + algorithm + '\' where name=\'' + channelname + '\'')


def setrecipe(controldbpath, channelname, recipe, startstage=0):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set controlrecipe=\'' + recipe + '\' where name=\'' + channelname + '\'')
    sqlitequery(controldbpath,
                'update channels set recipestage=\'' + str(startstage) + '\' where name=\'' + channelname + '\'')


def setchannelenabled(controldbpath, channelname, newstatus):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath, 'update channels set enabled=\'' + newstatus + '\' where name=\'' + channelname + '\'')


def setchanneloutputsenabled(controldbpath, channelname, newstatus):
    from iiutilities.dblib import sqlitequery

    sqlitequery(controldbpath,
                'update channels set outputsenabled=\'' + newstatus + '\' where name=\'' + channelname + '\'')


def disablealloutputs():
    from pilib import dirs
    from iiutilities.dblib import readalldbrows

    outputs = readalldbrows(dirs.dbs.control,'outputs')

    querylist=[]
    for output in outputs:
        querylist.append('update outputs set enabled=0 where name=\'' + output['name'] + '\'')

    print('all outputs disabled')

def turnoffgpios(GPIOnumberlist):
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)

    for GPIOnumber in GPIOnumberlist:
        GPIO.setup(int(GPIOnumber), GPIO.OUT)
        GPIO.output(int(GPIOnumber), False)


