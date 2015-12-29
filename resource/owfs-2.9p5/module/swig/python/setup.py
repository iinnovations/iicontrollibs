"""
::BOH
$Id$
$HeadURL: http://subversion/stuff/svn/owfs/trunk/setup.py $

Copyright (c) 2004, 2005 Peter Kropf. All rights reserved.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
::EOH

distutils setup file for use in creating a Python module from the owfs
project.
"""

import os
# platform doesn't exist for python 2.2
#import platform
from distutils.core import setup, Extension
from distutils import sysconfig
import string

#python_version = platform.python_version()[0:3]
python_version = sysconfig.get_config_vars()["VERSION"]


classifiers = """
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
Intended Audience :: System Administrators
Operating System :: POSIX :: Linux
Programming Language :: C
Programming Language :: Python
Topic :: System :: Hardware
Topic :: Utilities
"""

my_libraries = []
my_library_dirs = []
my_include_dirs = []
my_extra_link_args = []
my_extra_compile_args = []
my_runtime_library_dirs = []
my_extra_objects = []
my_define_macros = []
my_undef_macros = []

def write_configuration(define_macros, include_dirs, libraries, library_dirs,
                        extra_link_args, extra_compile_args,
                        runtime_library_dirs,extra_objects):    
    #Write the compilation configuration into a file
    out=open('configuration.log','w')
    print >> out, "Current configuration"
    print >> out, "libraries", libraries
    print >> out, "library_dirs", library_dirs
    print >> out, "include_dirs", include_dirs
    print >> out, "define_macros", define_macros
    print >> out, "extra_link_args", extra_link_args
    print >> out, "extra_compile_args", extra_compile_args
    print >> out, "runtime_library_dirs", runtime_library_dirs
    print >> out, "extra_objects", extra_objects
    out.close()


enable_usb = 'true'
enable_mt = '@ENABLE_MT@'
have_darwin = 'false'
have_freebsd = 'false'

bsd_fixes = have_darwin == 'true' or have_freebsd == 'true'

# have to split up the _CFLAGS, _LIBS variables since there are problem
# when they contain spaces. The append() function doesn't work very good.
# extra_l_args.append ( '' )

# Should perhaps add ${LD_EXTRALIBS} ${OSLIBS} to extra_l_args too if
# supporting MacOSX.

my_extra_compile_args = [ '-D_FILE_OFFSET_BITS=64' ]
if len('-I/usr/include/python2.7 -I/usr/include/python2.7 -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -D_FORTIFY_SOURCE=2 -g -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security') > 0:
	my_extra_compile_args = my_extra_compile_args + string.split('-I/usr/include/python2.7 -I/usr/include/python2.7 -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -D_FORTIFY_SOURCE=2 -g -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security', ' ')

if len('') > 0:
	my_extra_compile_args = my_extra_compile_args + string.split('', ' ')

my_extra_link_args = [ ]
if enable_usb == 'true':
    if len('') > 1:
	my_extra_compile_args = my_extra_compile_args + string.split('', ' ')

if enable_usb == 'true':
    if len('-L/usr/lib/arm-linux-gnueabihf -lusb') > 1:
	my_extra_link_args = my_extra_link_args + string.split('-L/usr/lib/arm-linux-gnueabihf -lusb', ' ')

if enable_mt == 'true':
    if len('-pthread') > 1:
	my_extra_compile_args = my_extra_compile_args + string.split('-pthread', ' ')

if enable_mt == 'true':
    if len('') > 1:
	my_extra_link_args = my_extra_link_args + string.split('', ' ')

if bsd_fixes:
    my_extra_link_args = my_extra_link_args + string.split('../../owlib/src/c/.libs/libow.so', ' ')

if len('-L/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7 -Xlinker -export-dynamic -Wl,-O1 -Wl,-Bsymbolic-functions') > 1:
	my_extra_link_args = my_extra_link_args + string.split('-L/usr/lib/python2.7/config -lpthread -ldl -lutil -lm -lpython2.7 -Xlinker -export-dynamic -Wl,-O1 -Wl,-Bsymbolic-functions', ' ')

ARCH=""
my_platform = ''
#my_platform = [ platform.machine() ]
if my_platform == "x86_64" or my_platform == "amd64" or my_platform == "64":
    print "64bit system detected"
    ARCH = "x64"

my_libraries = [ 'ow' ]

#if ARCH == "x64":
#    my_extra_objects = [ '../../owlib/src/c/.libs/libow.a' ]
#    my_libraries = [ ]
#    #my_extra_link_args = my_extra_link_args + string.split('-Wl,--export-dynamic', ' ')
#elif ARCH != "x64":
#    my_extra_objects = ""
#    my_libraries = [ 'ow' ]

if bsd_fixes:
    my_libraries = [ ]

removals = ['-Wstrict-prototypes']
   
if python_version == '2.5':
    cv_opt = sysconfig.get_config_vars()["CFLAGS"]
    for removal in removals:
        cv_opt = cv_opt.replace(removal, " ")
    sysconfig.get_config_vars()["CFLAGS"] = ' '.join(cv_opt.split())
    cv_opt = ' '.join(my_extra_compile_args)
    for removal in removals:
        cv_opt = cv_opt.replace(removal, " ")
    my_extra_compile_args = ' '.join(cv_opt.split())
else:
    cv_opt = sysconfig.get_config_vars()["OPT"]
    for removal in removals:
        cv_opt = cv_opt.replace(removal, " ")
    sysconfig.get_config_vars()["OPT"] = ' '.join(cv_opt.split())
#    cv_opt = ' '.join(my_extra_compile_args)
#    my_extra_compile_args = ' '.join(cv_opt.split())

			
#print "my_extra_compile_args=", my_extra_compile_args
my_extra_compile_args = [ arg for arg in my_extra_compile_args if len(arg) > 1 ]
#print "my_extra_compile_args=", my_extra_compile_args
my_extra_link_args = [ arg for arg in my_extra_link_args if len(arg) > 1 ]
my_include_dirs = [ '../../owlib/src/include', '../../../src/include' ]
my_library_dirs = [ '../../owlib/src/c/.libs' ]
my_runtime_library_dirs = [ '/opt/owfs/lib' ]

sources = [ 'ow_wrap.c' ]

write_configuration(my_define_macros, my_include_dirs, my_libraries, my_library_dirs,
                    my_extra_link_args, my_extra_compile_args,
                    my_runtime_library_dirs,my_extra_objects)

setup(
    name             = 'ow',
    description      = '1-wire hardware interface.',
    version          = '2.9p5',
    author           = 'Peter Kropf',
    author_email     = 'pkropf@gmail.com',
    url              = 'http://www.owfs.org/',
    license          = 'GPL',
    platforms        = 'Linux',
    long_description = 'Interface with 1-wire controllers and sensors from Python.',
    classifiers      = filter( None, classifiers.split( '\n' ) ),
    packages         = ['ow'],
    ext_package      = 'ow',
    ext_modules      = [ Extension( '_OW',
                                    sources,
                                    include_dirs = my_include_dirs,
                                    library_dirs = my_library_dirs,
                                    libraries    = my_libraries,
                                    extra_compile_args = my_extra_compile_args,
                                    extra_link_args = my_extra_link_args,
                                    runtime_library_dirs = my_runtime_library_dirs,
                                    extra_objects=my_extra_objects)
                         ],
    )

