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


"""
  This class defines actions taken on stuff.
  We are going to restructure this. An action is something that happens, for example:
     action.type == 'setvalue' : value is sent
        actiondetail contains dbvn reference to value to be set.
        By default this is binary : action active sets to 1, active reset will set to 0
        Active value will be set in actiondata, evaluating formula, etc. This can replace channels, in effect.

     action.type == 'email' : email is sent
        actiondetail contains email address (es)

     action.type == 'incvalue' : value is incremented
        actiondetail contains dbvn reference to value. By default this is add 1

     action.conditiontype == 'logical'
     action.conditiondbname == friendly dbname
     action.conditiontablename == tablename
     action.conditionlogic == equation or equations, using x as variable, separated by ';' e.g. 'x > 42,x < 89'
                              Can also code in other database variables using syntax: [dbname:tablename:valuename]
                              Not yet implemented, but that's the idea.

     action.conditiontype == 'time'
     action.conditionvalue == date time string in UTC seconds
     action.

  Some value have fields. These are universal values:

  All other data is contained in the actiondata field. These are values that are typically actiontype or conditiontype specific
  The actiondata is json, and parsed out by helper functions. If we need to modify it and reinsert it, we can modify the
"""
"""
    actiondata dictionary and parse it back into json before publishing it back to the database
"""


class action:

    def __init__(self, actiondict):
        from utilities.datalib import parseoptions
        for key, value in actiondict.items():
            setattr(self, key, value)

            """
            Instantiate the action class
            The dict that we get from the database contains a number of fixed fields, and also an 'actiondata' field
            that contains dynamic properties that may or may not exist for different action types.

            We parse it into a dictionary, and send it in as a property. We could append the dictionary, but then we
            would not be able to easily keep track of where to write back modified entries.
            """

            self.actiondatadict = parseoptions(actiondict['actiondata'])


            """ TODO: Set default values as a condition of alarm type to make alarm work when values are not specified.
            Publish will then insert these values into the database """

    def onact(self):
        from utilities import dblib, datalib, utility
        from cupid import pilib

        if self.actiontype == 'email':
            # process email action
            self.statusmsg += 'Processing email alert. '
            email = self.actiondetail
            message = 'Alert is active for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been on since ' + self.ontime + '.'
            subject = 'CuPID Alert : Alarm On - ' + self.name
            actionmail = utility.gmail(message=message, subject=subject, recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.statusmsg += 'Processing indicator on action. '
            indicatorname = self.actiondetail
            dblib.sqlitequery(pilib.controldatabase, 'update indicators set status=1 where name = \'' + indicatorname + '\'')

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output on action. '
            dblib.setsinglevalue(pilib.controldatabase, 'outputs', 'value', '1', condition='"id"=\'' + self.actiondetail + "'")

        # This should be the generic handler that we migrate to
        elif self.actiontype == 'setvalue':
            # to set a value, we need at minimum:
            #   dbname, tablename, valuename, setmethod and either:
            #   setmethod = increment, incrementvalue=1
            #   setmethod = value
            dbvndict = datalib.parsedbvn(self.actiondetail)
            dbpath = pilib.dbnametopath(dbvndict['dbname'])
            # Special set formula?

            if 'setvalueformula' in self.actiondatadict:
                # Stuff that we don't know yet.
                dblib.setsinglevalue(dbpath, dbvndict['tablename'], dbvndict['valuename'], 'formulastuff here', dbvndict['condition'])
            else:

                """ TODO: Fix this hack. We cannot currently single quote in the database entry because it breaks the reinsert.
                So for now, we have to add quotes on either side of the string literal before executing the sqlite query. """
                if dbvndict['condition']:
                    querycondition = dbvndict['condition'].split('=')[0] + "='" + dbvndict['condition'].split('=')[1] + "'"
                    # print('FIXED CONDITION')
                    # print(querycondition)
                else:
                    querycondition = None
                dblib.setsinglevalue(dbpath, dbvndict['tablename'], dbvndict['valuename'], '1', querycondition)

    def offact(self):
        from utilities import dblib, datalib, utility
        from cupid import pilib
        if self.actiontype == 'email':
            # process email action
            self.statusmsg +='Processing email alert.'
            email = self.actiondetail
            message = 'Alert has gone inactive for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been of since ' + self.offtime + '.'
            subject = 'CuPID Alert : Alarm Off - ' + self.name
            actionmail = utility.gmail(message=message, subject=subject, recipient=email)
            actionmail.send()

        elif self.actiontype == 'indicator':
            # process indicator action
            self.status +='Processing indicator off action.'
            indicatorname = self.actiondetail
            dblib.sqlitequery(pilib.controldatabase, 'update indicators set status=0 where name = ' + indicatorname)

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output off action. '
            dblib.setsinglevalue(pilib.controldatabase, 'outputs', 'value', '0', condition='"id"=\'' + self.actiondetail + "'")

        # This should be the generic handler that we migrate to
        elif self.actiontype == 'setvalue':
            # to set a value, we need at minimum:
            #   dbname, tablename, valuename, setmethod and either:
            #   setmethod = increment, incrementvalue=1
            #   setmethod = value
            dbvndict = datalib.parsedbvn(self.actiondetail)
            dbpath = pilib.dbnametopath(dbvndict['dbname'])
            # Special set formula?

            if 'setvalueformula' in self.actiondatadict:
                # Stuff that we don't know yet.
                dblib.setsinglevalue(dbpath, dbvndict['tablename'], dbvndict['valuename'], 'formulastuff here', dbvndict['condition'])
            else:

                """ TODO: Fix this hack. We cannot currently single quote in the database entry because it breaks the reinsert.
                So for now, we have to add quotes on either side of the string literal before executing the sqlite query. """
                if dbvndict['condition']:
                    querycondition = dbvndict['condition'].split('=')[0] + "='" + dbvndict['condition'].split('=')[1] + "'"
                    # print('FIXED CONDITION')
                    # print(querycondition)
                else:
                    querycondition = None
                dblib.setsinglevalue(dbpath, dbvndict['tablename'], dbvndict['valuename'], '0', querycondition)

    def printvalues(self):
        for attr,value in self.__dict__.iteritems():
            print(str(attr) + ' : ' + str(value))

    def publish(self):
        from cupid import pilib
        from utilities import dblib
        from utilities.datalib import dicttojson
        # reinsert updated action back into database
        valuelist=[]
        valuenames=[]

        # We convert our actiondatadict back into a string
        self.actiondata = dicttojson(self.actiondatadict)

        attrdict = {}
        for attr, value in self.__dict__.iteritems():
            if attr not in ['actiondatadict']:
                attrdict[attr] = value
                valuenames.append(attr)
                valuelist.append(value)

        # print(valuenames)
        # print(valuelist)

        dblib.sqliteinsertsingle(pilib.controldatabase, 'actions', valuelist, valuenames)
        # setsinglevalue(controldatabase, 'actions', 'ontime', gettimestring(), 'rowid=' + str(self.rowid))

    def process(self):
        from utilities import datalib
        if self.enabled:
            self.statusmsg = datalib.gettimestring() + ' : Enabled and processing. '
            if self.conditiontype == 'temporal':

                # Test event time against current time
                # Has time passed, and then is time within action window (don't want to act on all past actions if we miss them)
                timediff = float(
                    datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(self.actiontime))
                if timediff >= 0:
                    if timediff < int(self.actiontimewindow):
                        # We act
                        self.statusmsg += 'Time to act. '

                        # Then create the repeat event if we are supposed to.
                        if hasattr(self, 'repeat'):
                            newtimestring = str(
                                datalib.getnexttime(self.actiontime, self.repeat, int(self.repeatvalue)))
                            self.actiontime = newtimestring

                    else:
                        self.statusmsg += 'Past time but outside of window ' + str(self.actiontimewindow) + '. '
                else:
                    self.statusmsg += 'Not time yet for action scheduled for ' + str(self.actiontime) + '. '


            elif self.conditiontype == 'logical':

                # dbpath = pilib.dbnametopath(self.database)

                # # variablename is columnname for dbvalue conditiontype
                # if hasattr('valuerowid'):
                #     self.variablevalue = pilib.getsinglevalue(self.database, self.tablename, self.variablename, 'rowid=' + str(self.valuerowid))
                # else:
                #     self.variablevalue = pilib.getsinglevalue(self.database, self.tablename, self.variablename)

                currstatus = datalib.evalactionformula(self.actiondatadict['condition'])

                # get variable type to handle
                # variablestypedict = pilib.getpragmanametypedict(dbpath, self.tablename)
                # vartype = variablestypedict[self.variablename]
                # self.statusmsg += ' Variablevalue: ' + str(self.variablevalue) + '. Criterion: ' + str(self.criterion) + ' . '

                # process criterion according to type
                # curstatus = False
                # if vartype == 'boolean':
                #     self.statusmsg += ' Processing boolean. '
                #     # TODO: String conversion is a hack here and needs series work.
                #     if str(self.variablevalue) == str(self.criterion):
                #         curstatus = True
                # elif vartype == 'integer' or vartype == 'real':
                #     self.statusmsg += ' Processing integer/real. '
                #     # print(self.operator)
                #     self.variablevalue = float(self.variablevalue)
                #     self.criterion = float(self.criterion)
                #     if self.operator == 'greater':
                #         if self.variablevalue > self.criterion:
                #             curstatus = True
                #     elif self.operator == 'greaterorequal':
                #         if self.variablevalue >= self.criterion:
                #             curstatus = True
                #     elif self.operator == 'less':
                #         if self.variablevalue < self.criterion:
                #             curstatus = True
                #     elif self.operator == 'lessorequal':
                #         if self.variablevalue <= self.criterion:
                #             curstatus = True
                #     elif self.operator == 'equal':
                #         if self.variablevalue == self.criterion:
                #             curstatus = True
                #     else:
                #         self.statusmsg += 'Operator error. '
                #     if self.variablevalue == self.criterion:
                #         curstatus = True
                # elif vartype == 'text':
                #     self.statusmsg += ' Processing text. '
                #     if self.variablevalue == self.criterion:
                #         curstatus = True
                # else:
                #     self.statusmsg += ' Mode Error for vartype ' + vartype + '. '

                if self.status:
                    self.statusmsg += 'Last status is true. Currstatus is ' + str(currstatus) + '. '
                else:
                    self.statusmsg += 'Last status is not true. Currstatus is ' + str(currstatus) + '. '

                currenttime = datalib.gettimestring()

                # if status is true and current status is false, set ontime
                if currstatus and not self.status:
                    # print(str(curstatus) + ' ' + str(self.status))
                    self.statusmsg += 'Setting status ontime. '
                    self.ontime = datalib.gettimestring()
                    self.status = 1
                elif not currstatus and self.status:
                    self.statusmsg += 'Setting status offtime. '
                    self.offtime = datalib.gettimestring()
                    self.status = 0

                # Set current status
                if currstatus:
                    self.status = 1
                    # print('settings status')
                else:
                    self.status = 0
                    # print('resetting status')

                # if status is true and alarm isn't yet active, see if ondelay exceeded
                if currstatus and not self.active:
                    # print(pilib.timestringtoseconds(currenttime))
                    statusontime = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.ontime)
                    # print(statusontime)
                    if statusontime >= self.ondelay:
                        self.statusmsg += 'Setting action active. '
                        self.active = 1
                    else:
                        self.statusmsg += 'On delay not reached. '

                # if status is not true and alarm is active, see if offdelay exceeded
                if not currstatus and self.active:
                    statusofftime = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.offtime)
                    if statusofftime >= self.offdelay:
                        self.statusmsg += 'Setting action inactive. '
                        self.active = 0

                    else:
                        self.statusmsg += 'Off delay not reached. '

                # test to see if it is time to alert, based on delay ond alert time
                # print(self.statusmsg)
                act = False
                if self.active:
                    # check to see if it is time to alert
                    # For things like outputs, actionfrequency should be zero to always enforce that action is on.

                    # print(pilib.timestringtoseconds(currenttime))
                    # print(pilib.timestringtoseconds(self.lastactiontime))
                    # print(float(self.actionfrequency))
                    # print(pilib.timestringtoseconds(currenttime)-pilib.timestringtoseconds(self.lastactiontime))
                    if datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.lastactiontime) >= float(self.actionfrequency):
                        act = True
                        self.statusmsg += "Time to act. "
                    else:
                        act = False
                        self.statusmsg += "Not yet time to act."
                else:
                    # Send an alert / reset indicator if activereset is on
                    if self.activereset:
                        if datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.lastactiontime) >= float(self.actionfrequency):
                            act = True
                            self.statusmsg += "Time to act. "
                        else:
                            act = False
                            self.statusmsg += "Not yet time to act."

                if act:
                    # We're ready to alert or alert again.
                    self.lastactiontime = currenttime
                    if currstatus:
                        self.onact()
                    else:
                        self.offact()
            else:
                self.statusmsg += 'Action disabled.'
                self.status = 0
        else:
            self.statusmsg += 'Mode unrecognized.'


def processactions():

    # Read database to get our actions
    from utilities.dblib import readalldbrows
    from cupid.pilib import controldatabase

    actiondicts = readalldbrows(controldatabase, 'actions')

    for actiondict in actiondicts:
        alert = False


        # print("ACTIONDICT")
        # print(actiondatadict)

        thisaction = action(actiondict)

        thisaction.process()
        print(thisaction.name)
        print(thisaction.statusmsg)
        thisaction.publish()

if __name__ == '__main__':
    processactions()