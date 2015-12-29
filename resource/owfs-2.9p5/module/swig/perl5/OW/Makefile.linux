#!/usr/bin/perl -w

use ExtUtils::MakeMaker ;

WriteMakefile(
    'CC'	=>	'gcc',
    'ABSTRACT'	=>	q[Perl interface to the 1-wire filesytem] ,
    'AUTHOR'	=>	q[Paul H Alfille <paul.alfille@gmail.com>] ,
    'VERSION'	=>	q[2.9p5],
# Avoid compilation problem for Fedora Core 1 and Slackware 10.2
    'DEFINE'    =>	q[-pthread -D_FILE_OFFSET_BITS=64 -DSKIP_SEARCH_H -DHAVE_CONFIG_H],
    'INC'       =>	q[-I../../../../src/include -I../../../owlib/src/include ],
# Default value for LDDLFLAGS is $Config{lddlflags}="-shared -L/usr/local/lib"
# but we want rpath to be ${exec_prefix}/lib or ${prefix}/lib
    'LDDLFLAGS' =>      q[-shared -L../../../owlib/src/c/.libs -Wl,-rpath=/opt/owfs/lib],
    'LIBS'      =>	q[-L../../../owlib/src/c/.libs -low  -lm -ldl ],
    'OBJECT'	=>	'ow_wrap.o',
    'NAME'      =>	'OW',
	'POLLUTE'	=>  1,
) ;
