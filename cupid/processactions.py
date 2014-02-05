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
            delay = action['delay']  
            status = action['status']   # status is conditional comparison
            active = action['active']   # active is after ontime
            ontime = action['ontime']
            offtime = action['offtime']
            dbpath = getattr(pilib, database + 'database')
            print(dbpath)

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

            # if status is true and current status is false, set ontime
            if curstatus and not status:
                statusmsg += 'Setting ontime. '
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'ontime', pilib.gettimestring(), 'rowid=' + str(rowid))
            elif not curstatus and status:
                statusmsg += 'Setting offtime. '
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'offtime', pilib.gettimestring(), 'rowid=' + str(rowid))

            # set status in table
            # active is the status, e.g. whether we would be alerting if there were an
            # ontime of zero.
            pilib.setsinglevalue(pilib.controldatabase, 'actions', 'active', str(int(status)), 'rowid=' + str(rowid))

            # test to see if it is time to alert, based on delay ond ontime

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
