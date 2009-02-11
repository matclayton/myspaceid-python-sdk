#!/usr/bin/python
#
# Copyright (C) 2007, 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'cnanga@myspace.com (Chak Nanga)'


from distutils.core import setup

setup(
    name='myspace.py',
    version='0.1.0',
    description='Python client library for MySpace REST APIs',
    author='Chak Nanga',
    author_email='cnanga@myspace.com',
    license='Apache 2.0',
    url='http://code.google.com/p/myspaceid-python-sdk',
    packages=['myspace',
              'myspace.oauthlib',
    	      'myspace.simplejson',   
              'myspace.openid',
              'myspace.openid.consumer',
              'myspace.openid.store',
              'myspace.openid.yadis',
              'myspace.openid.extensions',
              ],
    package_dir={'myspace': 'src/myspace'}
)

