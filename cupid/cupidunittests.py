#!/usr/bin/env python

import os, sys, inspect

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

import unittest
import importlib


def runalltests():
    errors = []
    failures = []
    errormodules = []
    failuremodules = []

    totalfailurecount = 0
    totalerrorcount = 0

    functionerrorcount = 0
    moduleerrorcount = 0

    functionfailurecount = 0
    modulefailurecount = 0

    moduleresults = teststdmodules()
    for result in moduleresults:
        if result['errorcount'] != 0:
            errors.append(result)
            errormodules.append(['module'])
            moduleerrorcount += 1
            totalerrorcount += 1
        if result['failurecount'] != 0:
            failures.append(result)
            failuremodules.append(['module'])
            modulefailurecount += 1
            totalfailurecount += 1

    functionresults = teststdfunctions()
    for result in functionresults:
        if result['errorcount'] != 0:
            errors.append(result)
            errormodules.append(result['module'])
            functionerrorcount += 1
            totalerrorcount += 1
        if result['failurecount'] != 0:
            failures.append(result)
            failuremodules.append(result['module'])
            functionfailurecount += 1
            totalfailurecount += 1

    stringresult =  'Total Error Count: \t\t' + str(totalerrorcount) + '\r\n'
    stringresult += 'Function Error Count: \t\t' + str(functionerrorcount) + '\r\n'
    stringresult += 'Module Error Count: \t\t' + str(moduleerrorcount) + '\r\n'

    stringresult =  'Total Falure Count: \t\t' + str(totalfailurecount) + '\r\n'
    stringresult += 'Function Falure Count: \t\t' + str(functionfailurecount) + '\r\n'
    stringresult += 'Module Faliure Count: \t\t' + str(modulefailurecount) + '\r\n'

    if totalerrorcount > 0:
        stringresult += '\r\n'
        stringresult += 'Error Modules:\r\n'
        for errormodule in errormodules:
            stringresult += str(errormodule)
        stringresult += '\r\n\r\n'
        stringresult += 'Errors:\r\n'

        for error in errors:
            stringresult += str(error)

    if totalfailurecount > 0:
        stringresult += '\r\n'
        stringresult += 'Failure Modules:\r\n'
        for failuremodule in failuremodules:
            stringresult += str(failuremodule)
        stringresult += '\r\n\r\n'
        stringresult += 'Falures:\r\n'

        for failure in failures:
            stringresult += str(failure)

    return {'functions':functionresults, 'modules':moduleresults, 'functionerrorcount':functionerrorcount,
            'moduleerrorcount':moduleerrorcount, 'totalerrorcount':totalerrorcount, 'errors':errors,
            'modulefailurecount':modulefailurecount, 'totalfailurecount':totalfailurecount, 'failures':failures,
            'stringresult':stringresult}


class TestFunction(unittest.TestCase):
    def systemstatus(self):
        from systemstatus import runsystemstatus
        print('testing system status ...')
        runsystemstatus(True)
        self.assertTrue(True)

    def updateio(self):
        from cupid.updateio import updateiodata
        from cupid.pilib import dirs
        updateiodata(dirs.dbs.control)

    def netconfig(self):
        from netconfig import runconfig
        runconfig(True)

    def picontrol(self):
        from picontrol import runpicontrol
        runpicontrol(True)


class TestImport(unittest.TestCase):
    def test(self):
        importsuccess = False
        try:
            # Import module by name
            importlib.import_module(self.modulename)
        except:
            pass
        else:
            importsuccess=True
        self.assertTrue(importsuccess)


class ImportTester(TestImport):
    def __init__(self, methodname, modulename):
        # Call init to add parameters without overriding
        TestImport.__init__(self, methodname)
        self.modulename = modulename


def testmodule(modulename):
    print('Testing Module : ' + modulename)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(ImportTester(methodname='test', modulename=modulename))
    errorcount = len(result.errors)
    stringfailures=[]
    for failure in result.failures:
        stringfailures.append(str(failure))
    resultdict = {'module':modulename, 'testsrun':result.testsRun, 'errorcount':errorcount, 'errors':result.errors, 'failuremessages': 'blurg', 'failurecount': len(result.failures)}
    return resultdict


def testfunction(functionname):
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(TestFunction(functionname))
    print(result)
    errorcount = len(result.errors)
    if errorcount > 0:
        testelement = result.errors[0][0]
        errortuple = result.errors[0][1]
        errortuplereplaced = errortuple.replace('\n','')
    else:
        testelement = 'testelement'
        errortuple = 'no error'
        errortuplereplaced = 'no error'

    resultdict = {'module':functionname, 'testsrun':result.testsRun, 'testelement': str(testelement), 'errorcount':errorcount, 'errors': str(errortuple), 'failurecount': len(result.failures)}
    # resultdict = {'module':functionname, 'testsrun':result.testsRun, 'errors':str('blurg'), 'failuremessages': stringfailures, 'failurecount': len(result.failures)}
    # resultdict = {'blurgie': 'blurg', 'blurg2': {'stuff': 'more stuff', 'anotherstuff': 'even more stuff'}}
    # import json
    # print("MYDUMP")
    # json.dumps(resultdict)
    return resultdict


def testmodules(modulenames):
    resultdictarray=[]
    for modulename in modulenames:
        resultdictarray.append(testmodule(modulename))
    return resultdictarray


def testfunctions(functionnames):
    resultdictarray=[]
    for function in functionnames:
        resultdictarray.append(testfunction(function))
    return resultdictarray


def teststdmodules():
    modules = ['cupid.actions', 'cupid.boot', 'cupid.camera', 'cupid.controllib', 'cupid.cupiddaemon',
               'cupid.netconfig', 'cupid.periodicupdateio', 'cupid.pilib', 'cupid.picontrol', 'cupid.rebuilddatabases',
               'cupid.sessioncontrol', 'cupid.systemstatus', 'cupid.updateio']
    modules.extend(['iiutilities.datalib', 'iiutilities.dblib', 'iiutilities.gitupdatelib', 'iiutilities.netfun',
                    'iiutilities.owfslib', 'iiutilities.utility'])
    results = testmodules(modules)
    return results


def teststdfunctions():
    functions = []
    results = testfunctions(functions)
    return results

if __name__ == "__main__":

    results = runalltests()
    print(results['stringresult'])
