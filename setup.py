#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='superboucle',
    version='1.2.0',
    packages=find_packages(),
    author='Vampouille',
    author_email='superboucle@nura.eu',
    description='Loop application synced with jack transport',
    long_description=open('readme.md').read(),
    install_requires=["JACK-Client>=0.4.5",
                      "PyQt5>=5.11",
                      "SoundFile>=0.10",
                      "numpy>=1.16"],
    include_package_data=True,
    url='http://superboucle.nura.eu',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
    ],
    entry_points={'console_scripts':
                  ['superboucle = superboucle.boucle:start']},
)
