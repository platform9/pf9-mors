#!/usr/bin/env python
"""
Copyright 2016 Platform9 Systems Inc.(http://www.platform9.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from setuptools import setup

setup(name='mors',
      version='0.1',
      description='Platform9 Mors (lease manager)',
      author='Platform9',
      author_email='opensource@platform9.com',
      url='https://github.com/platform9/pf9-mors',
      packages=['mors',
                'mors/leasehandler',
                'mors_repo',
                'mors_repo/versions'],
      install_requires=['pbr', 'pytz', 'keystoneauth1', 'oslo.i18n',
                        'oslo.serialization', 'oslo.utils',
                        'keystonemiddleware', 'Paste', 'PasteDeploy',
                        'pip==19.2', 'python-novaclient', 'flask',
                        'SQLAlchemy', 'sqlalchemy-migrate', 'PyMySQL',
                        'eventlet', 'requests', 'nose', 'proboscis'],
      scripts=['mors/pf9_mors.py', 'mors/mors_manage.py']
      )
