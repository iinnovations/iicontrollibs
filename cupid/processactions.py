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
        if ['enabled']:
            statusmsg += 'Action enabled.'

            database = action['database']
            tablename = action['tablename']
            rowid = action['rowid']
            column = action['column']
            operator = action['operator']
            criterion = action['criterion']
            delay = ['delay']
            active = ['active']
            ontime = ['ontime']
            offtime = ['offtime']

            variablevalue = pilib.getsinglevalue(pilib.controldatabase, tablename, column, 'rowid=' + str(rowid))

            # get variable type to handle
            variablesdict = pilib.getpragmanametypedict(pilib.controldatabase, tablename)
            vartype = variablesdict[column]

            # process criterion according to type
            Status = False
            if vartype == 'boolean':
                statusmsg += ' Processing boolean. '
                if variablevalue == criterion:
                    status = True
            elif vartype == 'integer' or type == 'real':
                statusmsg += ' Processing integer/real. '
                if operator == '>':
                    if variablevalue > criterion:
                        Status = True
                elif operator == '>=':
                    if variablevalue >= criterion:
                        Status = True
                elif operator == '<':
                    if variablevalue < criterion:
                        Status = True
                elif operator == '<=':
                    if variablevalue <= criterion:
                        Status = True
                elif operator == '=':
                    if variablevalue == criterion:
                        Status = True
                else:
                    status += 'Operator error. '
                if variablevalue == criterion:
                    status = True
            elif vartype == 'text':
                statusmsg += ' Processing text. '
                if variablevalue == criterion:
                    status = True
            else:
                statusmsg += ' Mode Error. '

            if Status:
                statusmsg += 'Condition Active. '

            # if status is true and current status is false, set ontime
            if Status and not active:
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'ontime', pilib.gettimestring(), 'rowid=' + str(rowid))
            elif not Status and active:
                pilib.setsinglevalue(pilib.controldatabase, 'actions', 'offtime', pilib.gettimestring(), 'rowid=' + str(rowid))

            # set status in table
            # active is the status, e.g. whether we would be alerting if there were an
            # ontime of zero.
            dbpath = getattr(pilib, database + 'database')
            pilib.setsinglevalue(pilib.controldatabase, 'actions', 'active', str(int(Status)), 'rowid=' + str(rowid))

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