#!/usr/bin/env python

import os, sys, inspect

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

import unittest
import importlib

def runalltests():
    unittest.main()


class TestImport(unittest.TestCase):

    # Call init to add parameters without overriding
    def test(self):
        importsuccess = False
        try:
            importlib.import_module(self.modulename)
        except:
            pass
        else:
            importsuccess=True
        self.assertTrue(importsuccess)


class ImportTester(TestImport):
    def __init__(self, methodname, modulename):
        TestImport.__init__(self, methodname)
        self.modulename = modulename


def testModule(modulename):
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(ImportTester(methodname='test', modulename=modulename))
    stringfailures=[]
    for failure in result.failures:
        stringfailures.append(str(failure))
    resultdict = {'module':modulename, 'testsrun':result.testsRun, 'errors':result.errors, 'failuremessages': 'blurg', 'failurecount': len(result.failures)}
    # resultdict = {'module':modulename, 'testsrun':result.testsRun, 'errors':result.errors, 'failurecount': len(result.failures)}
    return resultdict

def testModules(modulenames):
    resultdictarray=[]
    for modulename in modulenames:
        resultdictarray.append(testModule(modulename))

    return resultdictarray


if __name__ == "__main__":

    # modules = ['cupid.pilib', 'cupid.picontrol', 'cupid.controllib', 'cupid.netconfig', 'cupid.netfun', 'cupid.owfslib', 'cupid.processactions', 'cupid.sessioncontrol', 'cupid.systemstatus', 'cupid.cupiddaemon']
    modules = ['cupid.pilib', 'cupid.picontrol']
    results = testModules(modules)
    print(results)

    for result in results:
        print(type(result['module']))
        print(type(result['testsrun']))
        print(type(result['errors']))
        print(type(result['failuremessages']))
        print(type(result['failurecount']))