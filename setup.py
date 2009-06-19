#!/usr/bin/env python
import sys
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
from setuptools import setup, find_packages

sys.path.insert(0, '.')
import zicbee_wasp
VERSION=zicbee_wasp.__version__

setup (
        name='zicbee-wasp',
        version=VERSION,
        author='Fabien Devaux',
        author_email='fdev31@gmail.com',
        url = 'http://zicbee.gnux.info/',
        download_url='http://zicbee.gnux.info/hg/index.cgi/wasp/archive/wip.tar.bz2',
        license='BSD',
        platform='all',
        description='Lightweight text client for zicbee',
        long_description='''
ZicBee is a project grouping multiple applications to manage play and handle music databases.
It takes ideas from Quodlibet and Mpd, both very good music mplayers with their own strengths.

Wasp is a thin text interface to access zicbee servers via http
        ''',
        keywords = 'database music tags metadata management',
        packages = find_packages(),
        entry_points = {
            "console_scripts": [
                'wasp = zicbee_wasp:startup',
                ],
            "setuptools.installation" : [
                'eggsecutable = zicbee_wasp:startup'
                ]
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

