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
        from iiutilities.datalib import parseoptions
        settings = {
            'ondelay':0,
            'offdelay':0
        }
        settings.update(actiondict)
        for key, value in settings.items():
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
            Publish will then insert these values into the database

            Also, when values are pulled in, use the schema to change value type, e.g. self.ondelay should come in as a
            float, not string.

            """
        self.statusmsg = ''

    def determine_status(self):
        from iiutilities import dblib, datalib

        if self.conditiontype == 'logical':
            currstatus = datalib.evaldbvnformula(self.actiondatadict['condition'])
            # print('CURRSTATUS',currstatus)
            if currstatus == None:
                self.statusmsg += 'None returned by evaldbvn. Setting status to False'
            self.value = 0
            try:
                self.status = int(currstatus)
            except:
                print('error parsing ' + str(currstatus))
                self.status = 0
<<<<<<< HEAD
=======

>>>>>>> 00139bf30d72de3bf4e5bccb6861b6030afd2119

        elif self.conditiontype == 'value':
            self.value = dblib.dbvntovalue(self.actiondatadict['dbvn'])
            print(self.actiondatadict['dbvn'])
            print(self.value)
            # self.value = datalib.evaldbvnformula(self.actiondatadict['dbvn'])
            # self.operator = self.actiondatadict['operator']
            # self.criterion = self.actiondatadict['criterion']
            try:
                self.status = int(datalib.calcastevalformula(str(self.value) + self.actiondatadict['operator'] + self.actiondatadict['criterion']))
            # Should really throw an error here.
            except:
                print('ERROR in asteval')
                print(str(self.value) + self.actiondatadict['operator'] + self.actiondatadict['criterion'])
                self.status = 0

        elif self.conditiontype == 'channel':
            from cupid import pilib
            control_channel_name = self.actiondatadict['channel_name']
            control_db = pilib.cupidDatabase(pilib.dirs.dbs.control)
            self.value = control_db.get_single_value('channels','controlvalue',condition='"name"=\'' + control_channel_name + "'")
            self.status = 0

            if 'PV_low' in self.actiondatadict and self.value < float(self.actiondatadict['PV_low']):
                self.status = 1

            if 'PV_high' in self.actiondatadict and self.value > float(self.actiondatadict['PV_high']):
                self.status = 1


        elif self.conditiontype == 'temporal':
            """ THIS HAS NOT YET WORKED. WE GET THERE.

            For now, idea is to set frequency to 0 for one-time events. > 0 for repeats. Details.
            """

            # Test event time against current time
            # Has time passed, and then is time within action window (don't want to act on all past actions if we miss them)
            timediff = float(
                datalib.timestringtoseconds(datalib.gettimestring()) - datalib.timestringtoseconds(self.actiontime))
            self.value = timediff
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
        # print(self.conditiontype)
        # print(self.status)

    def test(self):
        from iiutilities import utility
        if self.actiontype == 'email':
            # process email action
            self.statusmsg += 'Processing email alert. '
            email = self.actiondetail

            message = 'Test message for action ' + self.name

            subject = 'CuPID Test Alert : ' + self.name
            actionmail = utility.gmail(message=message, subject=subject, recipient=email)
            actionmail.send()


    def onact(self):
        from iiutilities import dblib, datalib, utility
        from cupid import pilib

        if self.actiontype == 'email':
            # process email action
            self.statusmsg += 'Processing email alert. '
            email = self.actiondetail

            # Special messages
            if self.conditiontype == 'channel':
                message = 'Channel alarm for ' + self.name + ' is active with value of ' + str(self.value) + '. '
                if 'PV_low' in self.actiondatadict:
                    message += 'Low alarm: ' + str(self.actiondatadict['PV_low'] + '. ')
                if 'PV_high' in self.actiondatadict:
                    message += 'High alarm: ' + str(self.actiondatadict['PV_high'] + '. ')


            elif self.conditiontype == 'value':

                # message = 'Alert is active for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been on since ' + self.ontime + '.'
                message = 'Alert for alarm ' + self.name + ' . On time of ' + self.ontime + '. Current time of ' \
                          + datalib.gettimestring()

                message += ' Value: ' + str(self.value) + self.actiondatadict['operator'] + str(self.actiondatadict['criterion'])

            else:
                # message = 'Alert is active for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been on since ' + self.ontime + '.'
                message = 'Alert for alarm ' + self.name + ' . On time of ' + self.ontime + '. Current time of ' \
                          + datalib.gettimestring()
            import socket
            hostname = socket.gethostname()

            subject = 'CuPID ' + hostname + ' Alert : Alarm On - ' + self.name
            try:
                actionmail = utility.gmail(message=message, subject=subject, recipient=email)
                actionmail.send()
            except:
                self.statusmsg += 'Error sending email. '
            else:
                self.statusmsg += 'Mail sent. '

        elif self.actiontype == 'indicator':
            # process indicator action
            self.statusmsg += 'Processing indicator on action. '
            indicatorname = self.actiondetail
            dblib.sqlitequery(pilib.dirs.dbs.control, 'update indicators set status=1 where name = \'' + indicatorname + '\'')

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output on action. '
            dblib.setsinglevalue(pilib.dirs.dbs.control, 'outputs', 'value', '1', condition='"id"=\'' + self.actiondetail + "'")

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
        from iiutilities import dblib, datalib, utility
        from cupid import pilib
        if self.actiontype == 'email':
            # process email action
            # TODO: This really needs to queue the email action in case we are not online.
            self.statusmsg +='Processing email alert.'
            email = self.actiondetail
            # message = 'Alert has gone inactive for ' + self.name + '. Criterion ' + self.variablename + ' in ' + self.tablename + ' has value ' + str(self.variablevalue) + ' with a criterion of ' + str(self.criterion) + ' with an operator of ' + self.operator + '. This alarm status has been of since ' + self.offtime + '.'
            message = 'Alert for alarm ' + self.name + ' . Off time of ' + self.offtime + '. Current time of ' \
                      + datalib.gettimestring()
            if self.conditiontype == 'value':
                message += ' Value: ' + str(self.value) + self.actiondatadict['operator'] + str(
                    self.actiondatadict['criterion'])

            import socket
            hostname = socket.gethostname()

            subject = 'CuPID ' + hostname + ' Alert : Alarm Off - ' + self.name
            try:
                actionmail = utility.gmail(message=message, subject=subject, recipient=email)
                actionmail.send()
            except:
                self.statusmsg += 'Error sending email. '
            else:
                self.statusmsg += 'Mail sent. '

        elif self.actiontype == 'indicator':
            # process indicator action
            self.statusmsg +='Processing indicator off action.'
            indicatorname = self.actiondetail
            dblib.setsinglevalue(pilib.dirs.dbs.control, 'indicators', 'status', 0, 'name=\'' + indicatorname+ '\'')
            print('INDICATORNAME = "' + indicatorname + '"')
            # dblib.sqlitequery(pilib.dirs.dbs.control, 'update indicators set status=0 where name = ' + indicatorname)

        elif self.actiontype == 'output':
            self.statusmsg += 'Processing output off action. '
            dblib.setsinglevalue(pilib.dirs.dbs.control, 'outputs', 'value', '0', condition='"id"=\'' + self.actiondetail + "'")

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
    # @profile
    def publish(self):
        from cupid import pilib
        from iiutilities import dblib
        from iiutilities.datalib import dicttojson
        # reinsert updated action back into database
        valuelist=[]
        valuenames=[]

        control_db = pilib.cupidDatabase(pilib.dirs.dbs.control)

        # We convert our actiondatadict back into a string
        self.actiondata = dicttojson(self.actiondatadict)

        for attr in self.__dict__:
            if attr not in ['actiondatadict', 'actionindex', 'actiondata']:
                control_db.set_single_value('actions', attr, getattr(self, attr), condition='"actionindex"=\'' + str(self.actionindex) +"'", queue=True)

<<<<<<< HEAD
        # print(len(control_db.queued_queries))
=======
        print(len(control_db.queued_queries))
>>>>>>> 00139bf30d72de3bf4e5bccb6861b6030afd2119
        control_db.execute_queue()
        # print(valuenames)
        # print(valuelist)

        # dblib.sqliteinsertsingle(pilib.dirs.dbs.control, 'actions', valuelist, valuenames)
        # setsinglevalue(dirs.dbs.control, 'actions', 'ontime', gettimestring(), 'rowid=' + str(self.rowid))
    # @profile
    def process(self):
        from iiutilities import datalib

        # TODO: Always determine status. This loads the value into the indicators, etc.

        if self.enabled:
            act = False

            self.statusmsg = datalib.gettimestring() + ' : Enabled and processing. '

            last_status = bool(self.status)

            # Update status.
            self.determine_status()

            # retrofit. i lazy.
            currstatus = bool(self.status)

            if last_status:
                self.statusmsg += 'Last status is ' + str(last_status) + '. Currstatus is ' + str(currstatus) + '. '
            else:
                self.statusmsg += 'Last status is ' + str(last_status) + '. Currstatus is ' + str(currstatus) + '. '

            currenttime = datalib.gettimestring()

            # if status is true and current status is false, set ontime (or if on/off time field is empty)
            if currstatus and (not last_status or not self.ontime):
                # print(str(curstatus) + ' ' + str(self.status))
                self.statusmsg += 'Setting status ontime. '
                self.ontime = datalib.gettimestring()
            elif not currstatus and (last_status or not self.offtime):
                self.statusmsg += 'Setting status offtime. '
                self.offtime = datalib.gettimestring()

            # print('CURR STATUS',currstatus)
            # print('SELF.ACTIVE',self.active)
            # if status is true and alarm isn't yet active, see if ondelay exceeded
            if currstatus and not self.active:
                # print(pilib.timestringtoseconds(currenttime))
                statusontime = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.ontime, defaulttozero=True)
                # print(statusontime)
                if statusontime >= float(self.ondelay):
                    self.statusmsg += 'Setting action active. '
                    self.active = 1
                else:

                    self.statusmsg += 'On delay not reached. '
                    # print('on',self.ontime)
                    # print('now',currenttime)

            # if status is not true and alarm is active, see if offdelay exceeded
            if not currstatus and self.active:
                statusofftime = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.offtime, defaulttozero=True)
                if statusofftime >= float(self.offdelay):
                    self.statusmsg += 'Setting action inactive. '
                    self.active = 0

                    # act on inactive transition
                    # Send an alert / reset indicator if activereset is on
                    if self.activereset:
                        time_since_last_action = datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(
                            self.lastactiontime, defaulttozero=True)
                        if time_since_last_action >= float(self.actionfrequency):
                            act = True
                            self.statusmsg += "Time to act on activereset. " + str(
                                time_since_last_action) + ' since last action, with action frequency of ' + str(
                                self.actionfrequency) + '. '
                        else:
                            act = False
                            self.statusmsg += "Not yet time to act."

                else:
                    self.statusmsg += 'Off delay not reached. '

            # test to see if it is time to alert, based on delay ond alert time
            # print(self.statusmsg)
            if self.active:
                # check to see if it is time to alert
                # For things like outputs, actionfrequency should be zero to always enforce that action is on.

                # print(pilib.timestringtoseconds(currenttime))
                # print(pilib.timestringtoseconds(self.lastactiontime))
                # print(float(self.actionfrequency))
                # print(pilib.timestringtoseconds(currenttime)-pilib.timestringtoseconds(self.lastactiontime))
                time_since_last_action =  datalib.timestringtoseconds(currenttime) - datalib.timestringtoseconds(self.lastactiontime, defaulttozero=True)
                if time_since_last_action >= float(self.actionfrequency):
                    act = True
                    self.statusmsg += "Time to act. " + str(time_since_last_action) + ' since last action, with action frequency of ' + str(self.actionfrequency) + '. '
                else:
                    act = False
                    self.statusmsg += "Not yet time to act."
            else:
                # Active reset only happens on the transition.
                pass

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

# @profile
<<<<<<< HEAD
def processactions(**kwargs):
=======
def processactions():
>>>>>>> 00139bf30d72de3bf4e5bccb6861b6030afd2119

    # Read database to get our actions
    from iiutilities.dblib import readalldbrows
    from cupid.pilib import dirs

    actiondicts = readalldbrows(dirs.dbs.control, 'actions')

    for actiondict in actiondicts:

<<<<<<< HEAD
        # if we only want to process one action, skip others.
        if 'name' in kwargs:
            if actiondict['name'] != kwargs['name']:
                continue

        alert = False

=======
>>>>>>> 00139bf30d72de3bf4e5bccb6861b6030afd2119
        # print("ACTIONDICT")
        # print(actiondatadict)

        thisaction = action(actiondict)

        thisaction.process()
        # print(thisaction.name)
        # print(thisaction.statusmsg)
        thisaction.publish()

if __name__ == '__main__':
    processactions()