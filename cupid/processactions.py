#!/usr/bin/python

import pilib

# Read database to get our actions

actions = pilib.readalldbrows(pilib.controldatabase, 'actions')

for action in actions:
    alert = False
    statusmsg = ''

    # process condition
    if action['conditiontype'] == 'dbvalue':
        enabled = action['enabled']
        if action['enabled']:
            statusmsg += 'Action enabled.'

            actiontype = action['actiontype']
            actiondetail = action['actiondetail']
            database = action['database']
            tablename = action['tablename']
            rowid = action['rowid']
            column = action['column']
            operator = action['operator']
            criterion = action['criterion']
            ondelay = action['ondelay']
            offdelay = action['offdelay']
            status = action['status']   # status is conditional comparison
            active = action['active']   # active is after ontime
            ontime = action['ontime']
            offtime = action['offtime']
            actionfrequency = action['actionfrequency']
            lastactiontime = action['lastactiontime']

            dbpath = getattr(pilib, database + 'database')

            variablevalue = pilib.getsinglevalue(dbpath, tablename, column, 'rowid=' + str(rowid))

            # get variable type to handle
            variablesdict = pilib.getpragmanametypedict(pilib.controldatabase, tablename)
            vartype = variablesdict[column]
            statusmsg += ' Variablevalue: ' + str(variablevalue) + '. Criterion: ' + str(criterion) + ' . '

            # process criterion according to type
            curstatus = False
            if vartype == 'boolean':
                statusmsg += ' Processing boolean. '
                if variablevalue == criterion:
                    curstatus = True
            elif vartype == 'integer' or vartype == 'real':
                statusmsg += ' Processing integer/real. '
                if operator == '>':
                    if variablevalue > criterion:
                        curstatus = True
                elif operator == '>=':
                    if variablevalue >= criterion:
                        curstatus = True
                elif operator == '<':
                    if variablevalue < criterion:
                        curstatus = True
                elif operator == '<=':
                    if variablevalue <= criterion:
                        curstatus = True
                elif operator == '=':
                    if variablevalue == criterion:
                        curstatus = True
                else:
                    statusmsg += 'Operator error. '
                if variablevalue == criterion:
                    curstatus = True
            elif vartype == 'text':
                statusmsg += ' Processing text. '
                if variablevalue == criterion:
                    curstatus = True
            else:
                statusmsg += ' Mode Error for vartype ' + vartype + '. '

            if curstatus:
                statusmsg += 'Status is true. '

            currenttime = pilib.gettimestring()
            # if status is true and current status is false, set ontime
            if curstatus and not status:
                statusmsg += 'Setting status ontime. '
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'ontime', pilib.gettimestring(), 'rowid=' + str(rowid))
                status = 1
            elif not curstatus and status:
                statusmsg += 'Setting status offtime. '
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'offtime', pilib.gettimestring(), 'rowid=' + str(rowid))
                status = 0

            if curstatus and not active:
                statusontime = pilib.timestringtoseconds(ontime) - pilib.timestringtoseconds(currenttime)
                if statusontime > ondelay:
                    statusmsg += 'Setting action active'
                    active = 1
                else:
                    statusmsg += 'On delay not reached'

            if not curstatus and active:
                statusofftime = pilib.timestringtoseconds(offtime) - pilib.timestringtoseconds(currenttime)
                if statusontime > offdelay:
                    statusmsg += 'Setting action inactive'
                    active = 0
                else:
                    statusmsg += 'Off delay not reached'

            # set status and active in table
            # active is the status, e.g. whether we would be alerting if there were an
            # ontime of zero

            pilib.setsinglevalue(pilib.controldatabase, 'actions', 'active', str(int(active)), 'rowid=' + str(rowid))
            pilib.setsinglevalue(pilib.controldatabase, 'actions', 'status', str(int(status)), 'rowid=' + str(rowid))

            # test to see if it is time to alert, based on delay ond alert time

            if active:
                # check to see if it is time to alert
                if pilib.timestringtoseconds(currenttime) - pilib.timestringtoseconds(lastactiontime):
                    alert=True
                else:
                    alert=False



    if alert:
        # test if it's ok to alert again
        alertfrequency = action['alertfrequency']

        # carry out alert
        if action['actiontype'] == 'email':
            # process email action
            email = action['actiondetail']

        elif action['actiontype'] == 'indicator':
            # process indicator action
            indicatorname = action['actiondetail']
print(statusmsg)
