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

from flask import request, jsonify
import functools, os


def get_context():
    return Context(request.headers['X-User-Id'],
                   request.headers['X-User'],
                   request.headers['X-Roles'],
                   request.headers['X-Tenant-Id'])


def error_handler(func):
    from sqlalchemy.exc import IntegrityError
    import traceback,sys
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as exc:
            traceback.print_exc(file=sys.stdout)
            return jsonify({'error': '{}'.format(str(exc))}), 422, {'ContentType': 'application/json'}

        except IntegrityError as exc:
            traceback.print_exc(file=sys.stdout)
            return jsonify({'error': 'Already exists'}), 409, {'ContentType': 'application/json'}

    return inner

def enforce(required=[]):
    """
    Generates a decorator that checks permissions before calling the
    contained pecan handler function.
    :param list[str] required: Roles require to run function.
    """

    def _enforce(fun):

        @functools.wraps(fun)
        def newfun(self, *args, **kwargs):

            if not (required):
                return fun(*args, **kwargs)
            else:
                roles_hdr = request.headers('X-Roles')
                if roles_hdr:
                    roles = roles_hdr.split(',')
                else:
                    roles = []

                if set(roles) & set(required):

                    return fun( *args, **kwargs)
                else:
                    return jsonify({'error': 'Unauthorized'}), 403, {'ContentType': 'application/json'}

        return newfun

    return _enforce


class Context:
    def __init__(self, user_id, user_name, roles_str, tenant_id):
        self.user_id = user_id
        self.user_name = user_name
        self.roles = roles_str.split(',')
        self.tenant_id = tenant_id
