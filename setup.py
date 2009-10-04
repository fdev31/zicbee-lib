#!/usr/bin/env python
import sys
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
from setuptools import setup, find_packages

sys.path.insert(0, '.')
import zicbee_lib
VERSION=zicbee_lib.__version__

setup (
        name='zicbee-lib',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        url = 'http://zicbee.gnux.info/',
        download_url='http://zicbee.gnux.info/hg/index.cgi/zicbee-lib/archive/%s.tar.bz2'%VERSION,
        license='BSD',
        platform='all',
        description='Base client libraries for zicbee project',
        long_description='''
ZicBee is a project grouping multiple applications to manage play and handle music databases.
It takes ideas from Quodlibet and Mpd, both very good music mplayers with their own strengths.

This package allow any python developper to build his own client
        ''',
        keywords = 'database music tags metadata management',
        packages = find_packages(),
        entry_points = {
#            "console_scripts": [
#                'wasp = zicbee_lib:startup',
#                ],
#            "setuptools.installation" : [
#                'eggsecutable = zicbee_wasp:startup'
#                ]
            },

        dependency_links = [
            'http://zicbee.gnux.info/files/',
            ],
        classifiers = [
                'Development Status :: 4 - Beta',
                'Intended Audience :: Developers',
#                'Intended Audience :: End Users/Desktop',
                'Operating System :: OS Independent',
                'Operating System :: Microsoft :: Windows',
                'Operating System :: POSIX',
                'Programming Language :: Python',
                'Environment :: Console',
                'Environment :: No Input/Output (Daemon)',
                'Environment :: X11 Applications',
                'Natural Language :: English',
                'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
                'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
                'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                'Topic :: Software Development',
                'Topic :: Software Development :: Libraries :: Python Modules',
                'Topic :: Multimedia :: Sound/Audio :: Players',
                'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
                'Topic :: Text Processing :: Markup',
                'Topic :: Utilities',
                ],

        )

