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
import os
import sys;

import eventlet
import requests
from migrate.versioning.api import upgrade, version_control

print(sys.path)
from mors.pf9_mors import start_server
from mors.mors_wsgi import DATE_FORMAT
import logging, sys
from datetime import datetime, timedelta
from proboscis.asserts import assert_equal
from proboscis import test
import shutil
from mors.leasehandler.fake_lease_handler import FakeLeaseHandler

from six.moves.configparser import ConfigParser
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client

http_client.HTTPConnection.debuglevel = 1

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
root.addHandler(ch)

logger = logging.getLogger(__name__)
eventlet.monkey_patch()
conf = None

headers = {
    'X-User-Id': 'asdfsd-asdf-sdadf',
    'X-User': 'roopak@pf9.com',
    'X-roles': 'admin,_member_',
    'X-Tenant-Id': 'poioio-oio-oioo'
}
tenant_id1 = "tenantid-1"
tenant_id2 = "tenantid-2"
instance_id1 = "instanceid-1-t-1"
instance_id2 = "instanceid-2-t-1"
instance_id3 = "instanceid-3-t-2"

action1 = 'delete'
action2 = 'power off'
expiry_mins1 = 4
port = 8080


def _setup_lease_handler():
    fakeLeaseHandler = FakeLeaseHandler(conf)
    now = datetime.now()
    dt = timedelta(days=3)
    creation_time = now - dt
    t1_vms = [{'instance_uuid': 'instance-123-t1', 'tenant_uuid': tenant_id1, 'created_at': creation_time},
              {'instance_uuid': 'instance-456-t1', 'tenant_uuid': tenant_id1, 'created_at': now},
              {'instance_uuid': instance_id1, 'tenant_uuid': tenant_id1, 'created_at': now},
              {'instance_uuid': instance_id2, 'tenant_uuid': tenant_id1, 'created_at': now}]
    fakeLeaseHandler.add_tenant_data(tenant_id1, t1_vms)

    t2_vms = [{'instance_uuid': 'instance-123-t2', 'tenant_uuid': tenant_id2, 'created_at': creation_time},
              {'instance_uuid': 'instance-456-t2', 'tenant_uuid': tenant_id2, 'created_at': now},
              {'instance_uuid': instance_id3, 'tenant_uuid': tenant_id2, 'created_at': now}]
    fakeLeaseHandler.add_tenant_data(tenant_id2, t2_vms)


@test
def initialize():
    global conf
    global port
    if os.path.exists("./sqlite+pysqlite:"):
        shutil.rmtree("./sqlite+pysqlite:")
    if os.path.exists("./test/test.db"):
        os.remove("./test/test.db")
    conf = ConfigParser()
    conf.readfp(open("test/pf9-mors.ini"))
    #create(conf.get("DEFAULT", "db_conn"), "./mors_repo")
    version_control(conf.get("DEFAULT", "db_conn"), "./mors_repo")
    upgrade(conf.get("DEFAULT", "db_conn"), "./mors_repo")
    port = conf.get("DEFAULT", "listen_port")

    _setup_lease_handler()
    api_paste_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'api-paste.ini')
    eventlet.greenthread.spawn(start_server, conf, api_paste_file)
    eventlet.greenthread.sleep(5)


@test(depends_on=[initialize])
def test_create_tenant():
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1,
                      json={"vm_lease_policy": {"tenant_uuid": tenant_id1, "expiry_mins": expiry_mins1, "action": action1}},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_create_tenant])
def test_update_tenant():
    r = requests.put('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1,
                     json={"vm_lease_policy": {"tenant_uuid": tenant_id1, "expiry_mins": 3, "action": action1}}, headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_update_tenant])
def test_get_all_tenants():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/',
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_get_all_tenants])
def test_get_tenant():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1, headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_get_tenant])
def test_create_tenant_neg():
    # Try creating again and it should result in error
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1,
                      json={"vm_lease_policy": {"tenant_uuid": tenant_id1, "expiry_mins": expiry_mins1, "action": action1}},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 409)


@test(depends_on=[test_create_tenant_neg])
def test_create_instance():
    # Now test the instance manipulation
    expiry = datetime.utcnow()
    expiry_str = datetime.strftime(expiry, DATE_FORMAT)
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                      json={"instance_uuid": instance_id1, "expiry": expiry_str, "action": action1},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_create_instance])
def test_get_instance():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)

@test(depends_on=[test_get_instance])
def test_update_instance():
    expiry = datetime.utcnow()
    expiry_str = datetime.strftime(expiry, DATE_FORMAT)
    r = requests.put('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                      json={"instance_uuid": instance_id1, "expiry": expiry_str, "action": action1},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)

@test(depends_on=[test_update_instance])
def test_update_instance_violation():
    expiry = datetime.utcnow() + timedelta(days=4)
    expiry_str = datetime.strftime(expiry, DATE_FORMAT)
    r = requests.put('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                      json={"instance_uuid": instance_id1, "expiry": expiry_str, "action": action1},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 422)

@test(depends_on=[test_update_instance])
def test_get_instance2():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_get_instance2])
def test_deleted_instance():
    eventlet.greenthread.sleep(50)
    # The instance lease should be deleted by now
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id1,
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 404)


@test(depends_on=[test_deleted_instance])
def test_create_instance2():
    # Now test the instance manipulation
    expiry = datetime.utcnow()
    expiry_str = datetime.strftime(expiry, DATE_FORMAT)
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id2,
                      json={"instance_uuid": instance_id2, "expiry": expiry_str, "action": action2},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_create_instance2])
def test_delete_instance_lease():
    r = requests.delete('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id1 + '/instance/' + instance_id2,
                        json={"tenant_uuid": tenant_id1, "instance_uuid": instance_id2},
                        headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_deleted_instance])
def test_create_tenant2():
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2,
                      json={"vm_lease_policy": {"tenant_uuid": tenant_id2, "expiry_mins": expiry_mins1, "action": action2}},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_create_tenant2])
def test_create_instance3():
    # Now test the instance manipulation
    expiry = datetime.utcnow()
    expiry_str = datetime.strftime(expiry, DATE_FORMAT)
    r = requests.post('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2 + '/instance/' + instance_id3,
                      json={"tenant_uuid": tenant_id2, "instance_uuid": instance_id3, "expiry": expiry_str, "action": action2},
                      headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_create_instance3])
def test_delete_tenant2():
    r = requests.delete('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2,
                        json={"tenant_uuid": tenant_id2}, headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)


@test(depends_on=[test_delete_tenant2])
def test_get_tenant2():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2, headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 404)


@test(depends_on=[test_delete_tenant2])
def test_get_instance3():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2 + '/instance/' + instance_id3,
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 404)


@test(depends_on=[test_get_instance3])
def test_get_all_instances_for_tenant2():
    r = requests.get('http://127.0.0.1:' + port + '/v1/tenant/' + tenant_id2 + '/instances/',
                     headers=headers)
    logger.debug(r.text)
    assert_equal(r.status_code, 200)
