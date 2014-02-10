#!/usr/bin/python

import pilib

# Read database to get our actions

actiondicts = pilib.readalldbrows(pilib.controldatabase, 'actions')

for actiondict in actiondicts:
    alert = False

    thisaction = pilib.action(actiondict)
    thisaction.statusmsg = ''
    # process condition
    if thisaction.conditiontype == 'dbvalue':
        if thisaction.enabled:
            thisaction.statusmsg += 'Action enabled.'

            dbpath = getattr(pilib, thisaction.database + 'database')

            # variablename is columnname for dbvalue conditiontype
            thisaction.variablevalue = pilib.getsinglevalue(dbpath, thisaction.tablename, thisaction.variablename, 'rowid=' + str(thisaction.rowid))

            # get variable type to handle
            variablestypedict = pilib.getpragmanametypedict(pilib.controldatabase, thisaction.tablename)
            vartype = variablestypedict[thisaction.variablename]
            thisaction.statusmsg += ' Variablevalue: ' + str(thisaction.variablevalue) + '. Criterion: ' + str(thisaction.criterion) + ' . '

            # process criterion according to type
            curstatus = False
            if vartype == 'boolean':
                thisaction.statusmsg += ' Processing boolean. '
                if thisaction.variablevalue == thisaction.criterion:
                    curstatus = True
            elif vartype == 'integer' or vartype == 'real':
                thisaction.statusmsg += ' Processing integer/real. '
                if thisaction.operator == '>':
                    if thisaction.variablevalue > thisaction.criterion:
                        curstatus = True
                elif thisaction.operator == '>=':
                    if thisaction.variablevalue >= thisaction.criterion:
                        curstatus = True
                elif thisaction.operator == '<':
                    if thisaction.variablevalue < thisaction.criterion:
                        curstatus = True
                elif thisaction.operator == '<=':
                    if thisaction.variablevalue <= thisaction.criterion:
                        curstatus = True
                elif thisaction.operator == '=':
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
                thisaction.statusmsg += 'Setting status ontime. '
                thisaction.ontime=pilib.gettimestring()
                thisaction.status = 1
            elif not curstatus and thisaction.status:
                thisaction.statusmsg += 'Setting status offtime. '
                thisaction.ontime=pilib.gettimestring()
                thisaction.status = 0

            # if status is true and alarm isn't yet active, see if ondelay exceeded
            if curstatus and not thisaction.active:
                print(pilib.timestringtoseconds(currenttime))
                statusontime = pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(thisaction.ontime)
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
                if pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(thisaction.lastactiontime) > thisaction.actionfrequency:
                    alert = True
                    thisaction.statusmsg += "Time to act. "
                else:
                    alert = False
                    thisaction.statusmsg += "Not yet time to act."

            if alert:
                # We're ready to alert or alert again.
                thisaction.lastactiontime = currenttime
                thisaction.act()
        else:
            thisaction.statusmsg += 'Action disabled.'
    else:
        thisaction.statusmsg += 'Mode unrecognized.'

    print(thisaction.statusmsg)
    thisaction.publish()
