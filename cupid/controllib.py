#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# This library is for control functions 

#######################################################
## Control Functions
#######################################################

def runalgorithm(controldatabase, recipedatabase, channelname):
    from utilities.utility import timestringtoseconds
    from utilities.utility import gettimestring
    from utilities.dblib import sqlitequery
    from utilities.dblib import datarowtodict
    import time

    message = ''

    # get our details of our channel
    channeldata = sqlitequery(controldatabase, 'select * from channels where name=' + "'" + channelname + "'")[0]
    channeldict = datarowtodict(controldatabase, 'channels', channeldata)
    # check to see if we are running a recipe

    controlrecipename = channeldict['controlrecipe']
    if controlrecipename and controlrecipename != 'none':

        # Get recipe details
        # If recipes get too big, we'll just get 
        # a couple stages. For now, we make a 
        # dictionary array

        #print('we are in recipe ' + controlrecipename)
        #print(recipedatabase)

        recipedata = sqlitequery(recipedatabase, 'select * from \'' + controlrecipename + '\'')
        recipedictarray = []

        for stage in recipedata:
            recipedict = datarowtodict(recipedatabase, controlrecipename, stage)
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
                    sqlitequery(controldatabase, 'update channels set recipestarttime=\'' + gettimestring(
                        currenttime) + '\' where name=\'' + channelname + '\'')

                # Set stage to new stage number
                sqlitequery(controldatabase, 'update channels set recipestage=\'' + str(
                    nextstagenumber) + '\' where name=\'' + channelname + '\'')

                # Set setpointvalue
                sqlitequery(controldatabase, 'update channels set setpointvalue=\'' + str(
                    nextstage['setpointvalue']) + '\' where name=\'' + channelname + '\'')

                # Set stage start time to now 
                sqlitequery(controldatabase, 'update channels set recipestagestarttime=\'' + gettimestring(
                    currenttime) + '\' where name=\'' + channelname + '\'')

                # Set new controlalgorithm 
                sqlitequery(controldatabase, 'update channels set controlalgorithm=\'' + nextstage[
                    'controlalgorithm'] + '\' where name=\'' + channelname + '\'')

            else:

                # Take channel off recipe
                sqlitequery(controldatabase,
                            'update channels set controlrecipe=\'none\' where name=\'' + channelname + '\'')
                sqlitequery(controldatabase, 'update channels set recipestate=\'0\' where name=\'' + channelname + '\'')

                sqlitequery(controldatabase,
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
        sqlitequery(controldatabase,
                    'update channels set controlrecipe=\'none\' where name=\'' + channelname + '\'')
        sqlitequery(controldatabase, 'update channels set recipestate=\'0\' where name=\'' + channelname + '\'')

        sqlitequery(controldatabase,
                    'update channels set recipestage=\'0\' where name=\'' + channelname + '\'')

    algorithm = channeldict['controlalgorithm']
    setpointvalue = float(channeldict['setpointvalue'])
    controlvalue = float(channeldict['controlvalue'])

    algorithmrows = sqlitequery(controldatabase, 'select * from controlalgorithms where name=' + "'" + algorithm + "'")
    algorithmrow = algorithmrows[0]
    algorithm = datarowtodict(controldatabase, 'controlalgorithms', algorithmrow)
    type = algorithm['type']

    if type == 'on/off with deadband':
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
        from pilib import controldatabase
        from utilities.dblib import sqlitequery
        sqlitequery(controldatabase, 'update channels set setpointvalue=\'' + str(setpointvalue) + '\' where name=\'' + channel.name + '\'')

    def setaction(self,action):
         from pilib import controldatabase
         from utilities.dblib import sqlitequery
         sqlitequery(controldatabase,
            'update channels set action = \'' + str(action) + '\' where name = \'' + channel.name + '\'')

    def setcontrolinput(self,inputid):
        from pilib import controldatabase
        from utilities.dblib import sqlitequery
        sqlitequery(controldatabase,
                'update channels set controlinput = \'' + inputid + '\' where name = \'' + channel.name + '\'')

    def getaction(self):
        from pilib import controldatabase
        from utilities.dblib import sqlitedatumquery
        self.action = sqlitedatumquery(controldatabase,'select action from channels where name=\'' + channel.name + '\'')

    def getsetpointvalue(self):
        from pilib import controldatabase
        from utilities.dblib import sqlitedatumquery
        self.setpointvalue = sqlitedatumquery(controldatabase, 'select setpointvalue from channels where name=\'' + channel.name + '\'')

    def incsetpoint(self):
        self.getsetpointvalue()
        self.setsetpoint(self.setpointvalue+1)

    def decsetpoint(self):
        self.getsetpointvalue()
        self.setsetpoint(self.setpointvalue-1)

    def getmode(self):
        from pilib import controldatabase
        from utilities.dblib import sqlitedatumquery
        self.mode = sqlitedatumquery(controldatabase, 'select mode from channels where name=\'' + channel.name + '\'')

    def setmode(self,mode):
        from pilib import controldatabase
        from utilities.dblib import sqlitequery
        sqlitequery(controldatabase, 'update channels set mode=\'' + str(mode) + '\' where name=\'' + channel.name + '\'')

    def togglemode(self,mode):
        from pilib import controldatabase
        from utilities.dblib import sqlitedatumquery
        self.getmode()
        if self.mode == 'manual':
            self.mode = 'auto'
        else:
            self.mode = 'manual'

# This works fine, for now.

def setsetpoint(controldatabase, channelname, setpointvalue):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase, 'update channels set setpointvalue=\'' + str(
        setpointvalue) + '\' where name=\'' + channelname + '\'')


def setaction(controldatabase, channelname, action):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set action = \'' + str(action) + '\' where name = \'' + channelname + '\'')


def setcontrolinput(controldatabase, channelname, inputid):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set controlinput = \'' + inputid + '\' where name = \'' + channelname + '\'')


def setcontrolvalue(controldatabase, channelname, controlvalue):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set controlvalue = \'' + str(controlvalue) + '\' where name = \'' + channelname + '\'')


def getaction(controldatabase, channelname):
    from utilities.dblib import sqlitequery

    action = sqlitequery(controldatabase, 'select action from channels where name=\'' + channelname + '\'')[0][0]
    return action


def getsetpoint(controldatabase, channelname):
    from utilities.dblib import sqlitequery

    currentsetpoint = \
        sqlitequery(controldatabase, 'select setpointvalue from channels where name=\'' + channelname + '\'')[0][0]
    return currentsetpoint


def decsetpoint(controldatabase, channelname):
    currentsetpoint = getsetpoint(controldatabase, channelname)
    newsetpoint = currentsetpoint - 1
    setsetpoint(controldatabase, channelname, newsetpoint)


def incsetpoint(controldatabase, channelname):
    currentsetpoint = getsetpoint(controldatabase, channelname)
    newsetpoint = currentsetpoint + 1
    setsetpoint(controldatabase, channelname, newsetpoint)


def setmode(controldatabase, channelname, mode):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase, 'update channels set mode=\'' + mode + '\' where name=\'' + channelname + '\'')

    # set action to 0 if we switch to manual
    if mode == 'manual':
        setaction(controldatabase, channelname, 0)


def getmode(controldatabase, channelname):
    from utilities.dblib import sqlitequery

    mode = sqlitequery(controldatabase, 'select mode from channels where name=\'' + channelname + '\'')[0][0]
    return mode


def togglemode(controldatabase, channelname):
    from utilities.dblib import sqlitequery
    from controllib import setaction

    curmode = getmode(controldatabase, channelname)
    if curmode == 'manual':
        newmode = 'auto'
    else:
        newmode = 'manual'
        setaction(controldatabase, channelname, 0)

    setmode(controldatabase, channelname, newmode)


def checkifenableready(outputname, outputs):
    from time import time
    from utilities.utility import timestringtoseconds

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
    from utilities.utility import timestringtoseconds

    # Find the variables we want
    for output in outputs:
        if output['name'] == outputname:
            minontime = output['minontime']
            ontime = timestringtoseconds(output['ontime'])

    if time() - ontime > minontime:
        return True
    else:
        return False


def setposout(controldatabase, channelname, outputname):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set positiveoutput=\'' + outputname + '\' where name=\'' + channelname + '\'')


def setnegout(controldatabase, channelname, outputname):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set negativeoutput=\'' + outputname + '\' where name=\'' + channelname + '\'')


def setalgorithm(controldatabase, channelname, algorithm):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set controlalgorithm=\'' + algorithm + '\' where name=\'' + channelname + '\'')


def setrecipe(controldatabase, channelname, recipe, startstage=0):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set controlrecipe=\'' + recipe + '\' where name=\'' + channelname + '\'')
    sqlitequery(controldatabase,
                'update channels set recipestage=\'' + str(startstage) + '\' where name=\'' + channelname + '\'')


def setchannelenabled(controldatabase, channelname, newstatus):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase, 'update channels set enabled=\'' + newstatus + '\' where name=\'' + channelname + '\'')


def setchanneloutputsenabled(controldatabase, channelname, newstatus):
    from utilities.dblib import sqlitequery

    sqlitequery(controldatabase,
                'update channels set outputsenabled=\'' + newstatus + '\' where name=\'' + channelname + '\'')


def disablealloutputs():
    from pilib import controldatabase
    from utilities.dblib import readalldbrows

    outputs = readalldbrows(controldatabase,'outputs')

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


