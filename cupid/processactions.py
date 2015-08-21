#!/usr/bin/env python

__author__ = "Colin Reese"
__copyright__ = "Copyright 2014, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import pilib


def processactions():

    # Read database to get our actions

    actiondicts = pilib.readalldbrows(pilib.controldatabase, 'actions')

    for actiondict in actiondicts:
        alert = False

        # Instantiate the action class
        thisaction = pilib.action(actiondict)
        thisaction.statusmsg = ''
        # print(actiondict)
        # process condition
        if thisaction.conditiontype == 'dbvalue':
            if thisaction.enabled:
                thisaction.statusmsg += 'Action enabled.'

                dbdir = getattr(pilib, 'databasedir')
                # print(dbdir)
                dbpath = dbdir + thisaction.database + '.db'

                # variablename is columnname for dbvalue conditiontype
                thisaction.variablevalue = pilib.getsinglevalue(dbpath, thisaction.tablename, thisaction.variablename, 'rowid=' + str(thisaction.valuerowid))

                # get variable type to handle
                variablestypedict = pilib.getpragmanametypedict(dbpath, thisaction.tablename)
                vartype = variablestypedict[thisaction.variablename]
                thisaction.statusmsg += ' Variablevalue: ' + str(thisaction.variablevalue) + '. Criterion: ' + str(thisaction.criterion) + ' . '

                # process criterion according to type
                curstatus = False
                if vartype == 'boolean':
                    thisaction.statusmsg += ' Processing boolean. '
                    # TODO: String conversion is a hack here and needs series work.
                    if str(thisaction.variablevalue) == str(thisaction.criterion):
                        curstatus = True
                elif vartype == 'integer' or vartype == 'real':
                    thisaction.statusmsg += ' Processing integer/real. '
                    # print(thisaction.operator)
                    thisaction.variablevalue = float(thisaction.variablevalue)
                    thisaction.criterion = float(thisaction.criterion)
                    if thisaction.operator == 'greater':
                        if thisaction.variablevalue > thisaction.criterion:
                            curstatus = True
                    elif thisaction.operator == 'greaterorequal':
                        if thisaction.variablevalue >= thisaction.criterion:
                            curstatus = True
                    elif thisaction.operator == 'less':
                        if thisaction.variablevalue < thisaction.criterion:
                            curstatus = True
                    elif thisaction.operator == 'lessorequal':
                        if thisaction.variablevalue <= thisaction.criterion:
                            curstatus = True
                    elif thisaction.operator == 'equal':
                        if thisaction.variablevalue == thisaction.criterion:
                            curstatus = True
                    else:
                        thisaction.statusmsg += 'Operator error. '
                    if thisaction.variablevalue == thisaction.criterion:
                        curstatus = True
                elif vartype == 'text':
                    thisaction.statusmsg += ' Processing text. '
                    if thisaction.variablevalue == thisaction.criterion:
                        curstatus = True
                else:
                    thisaction.statusmsg += ' Mode Error for vartype ' + vartype + '. '

                if curstatus:
                    thisaction.statusmsg += 'Status is true. '
                else:
                    thisaction.statusmsg += 'Status is not true. '

                currenttime = pilib.gettimestring()

                # if status is true and current status is false, set ontime
                if curstatus and not thisaction.status:
                    # print(str(curstatus) + ' ' + str(thisaction.status))
                    thisaction.statusmsg += 'Setting status ontime. '
                    thisaction.ontime = pilib.gettimestring()
                    thisaction.status = 1
                elif not curstatus and thisaction.status:
                    thisaction.statusmsg += 'Setting status offtime. '
                    thisaction.offtime = pilib.gettimestring()
                    thisaction.status = 0

                # Set current status
                if curstatus:
                    thisaction.status = 1
                    # print('settings status')
                else:
                    thisaction.status = 0
                    # print('resetting status')

                # if status is true and alarm isn't yet active, see if ondelay exceeded
                if curstatus and not thisaction.active:
                    # print(pilib.timestringtoseconds(currenttime))
                    statusontime = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(thisaction.ontime)
                    # print(statusontime)
                    if statusontime > thisaction.ondelay:
                        thisaction.statusmsg += 'Setting action active'
                        thisaction.active = 1
                    else:
                        thisaction.statusmsg += 'On delay not reached'

                # if status is not true and alarm is active, see if offdelay exceeded
                if not curstatus and thisaction.active:
                    statusofftime = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(thisaction.offtime)
                    if statusofftime > thisaction.offdelay:
                        thisaction.statusmsg += 'Setting action inactive'
                        thisaction.active = 0
                        # Send an alert / reset indicator if activereset is on
                        if thisaction.activereset:
                            thisaction.offact()
                    else:
                        thisaction.statusmsg += 'Off delay not reached'

                # test to see if it is time to alert, based on delay ond alert time
                if thisaction.active:
                    # check to see if it is time to alert
                    # For things like outputs, actionfrequency should be zero to always enforce that action is on.

                    # print(pilib.timestringtoseconds(currenttime))
                    # print(pilib.timestringtoseconds(thisaction.lastactiontime))
                    # print(float(thisaction.actionfrequency))
                    # print(pilib.timestringtoseconds(currenttime)-pilib.timestringtoseconds(thisaction.lastactiontime))
                    if pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(thisaction.lastactiontime) > float(thisaction.actionfrequency):
                        alert = True
                        thisaction.statusmsg += "Time to act. "
                    else:
                        alert = False
                        thisaction.statusmsg += "Not yet time to act."

                if alert:
                    # We're ready to alert or alert again.
                    thisaction.lastactiontime = currenttime
                    if curstatus:
                        thisaction.onact()
                    else:
                        thisaction.offact()
            else:
                thisaction.statusmsg += 'Action disabled.'
                thisaction.status = 0
        else:
            thisaction.statusmsg += 'Mode unrecognized.'

        # print(thisaction.statusmsg)
        thisaction.publish()

if __name__ == '__main__':
    processactions()