from setuptools import setup
import sys,os

setup(
    name = 'scale-registrator',
    version = '0.1.0',
    description = 'Scale registrator',
    license='GPL v3',
    author = 'vasuk.mobile@gmail.com',
    packages=['src'],
    package_data={'src': ['description.txt','ui/*']
                 },
    entry_points = {
        'gui_scripts': [
            'scale-registrator=src.main:main']
            },
    classifiers = ['Operating System :: OS Independent',
            'Programming Language :: Python :: 3.12',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
)
