# -*- coding: utf-8 -*-
#
# Copyright 2015, Jianing Yang
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# Author: Jianing Yang <jianingy.yang@gmail.com>


import setuptools

setuptools.setup(
    name='openwrt-wac',
    version='0.1.1',
    description=('a simple command line tool for managing '
                 'groups of openwrt based rotuers'),
    author='Jianing Yang',
    author_email='jianingy.yang@gmail.com',
    url='http://github.com/jianingy/openwrt-wac',
    install_requires=['tornado', 'click', 'humanize'],
    packages=['wac'],
    entry_points={
        'console_scripts': [
            'wac=wac.cmd:wac',
            ]
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Topic :: Utilities',
    ],
)
