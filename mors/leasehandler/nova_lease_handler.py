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

from novaclient import client
import logging
import time
import novaclient
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneauth1 import exceptions as ks_exceptions
from datetime import datetime
from .constants import SUCCESS_OK, ERR_NOT_FOUND, ERR_UNKNOWN
from mors.constants import LOGGER_PREFIX

logger = logging.getLogger(LOGGER_PREFIX+__name__)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def get_vm_data(data):
    return {'instance_uuid': data.id,
            'tenant_uuid': data.tenant_id,
            'created_at': datetime.strptime(data.created, DATE_FORMAT)}

MAX_AUTH_RETRIES = 3
AUTH_RETRY_DELAY = 5

class NovaLeaseHandler:
    def __init__(self, conf):
        self.conf = conf
        self.keystone_sess = self.get_keystone_session()
        self.pf9_project_id = self._get_project_id_with_retry()
        self.nova_client = client.Client(self.conf.get("nova", "version"),
                             username=self.conf.get("nova", "user_name"),
                             region_name=self.conf.get("nova", "region_name"),
                             tenant_id=self.pf9_project_id,
                             api_key=self.conf.get("nova", "password"),
                             auth_url=self.conf.get("nova", "auth_url"),
                             insecure=True, connection_pool=False,
                             project_domain_name="default",
                             user_domain_name="default",
                             endpoint_type="internal")

    def _get_nova_client(self):
        return self.nova_client

    def _get_project_id_with_retry(self):
        auth_url = self.conf.get('nova', 'auth_url')
        username = self.conf.get('nova', 'user_name')
        for attempt in range(1, MAX_AUTH_RETRIES + 1):
            try:
                project_id = self.keystone_sess.get_project_id()
                logger.info("Keystone authentication successful (attempt %d/%d)",
                            attempt, MAX_AUTH_RETRIES)
                return project_id
            except ks_exceptions.Unauthorized:
                logger.error(
                    "Keystone auth failed (attempt %d/%d): 401 Unauthorized. "
                    "auth_url=%s, username=%s. Verify credentials and that the "
                    "user exists in Keystone.",
                    attempt, MAX_AUTH_RETRIES, auth_url, username)
            except ks_exceptions.ConnectFailure as e:
                logger.error(
                    "Keystone auth failed (attempt %d/%d): unable to connect "
                    "to %s: %s",
                    attempt, MAX_AUTH_RETRIES, auth_url, e)
            except Exception as e:
                logger.error(
                    "Keystone auth failed (attempt %d/%d): %s",
                    attempt, MAX_AUTH_RETRIES, e)
            if attempt < MAX_AUTH_RETRIES:
                logger.info("Retrying in %d seconds...", AUTH_RETRY_DELAY)
                time.sleep(AUTH_RETRY_DELAY)
        raise RuntimeError(
            "Failed to authenticate with Keystone after %d attempts. "
            "auth_url=%s, username=%s" % (MAX_AUTH_RETRIES, auth_url, username))

    def get_keystone_session(self):
        auth_params = {
             'auth_url': self.conf.get('nova', 'auth_url'),
             'username': self.conf.get('nova', 'user_name'),
             'password': self.conf.get('nova', 'password'),
             'project_name': 'services',
             'user_domain_id': 'default',
             'project_domain_id': 'default'
        }
        auth = v3.Password(**auth_params)
        return session.Session(auth=auth)

    def get_all_vms(self, tenant_uuid):
        """
        Get all vms for a given tenant
        :param tenant_uuid:
        :return: an iteratble that returns a set of vms (each vm has a UUID and a created_at field)
        """
        try:
            with self._get_nova_client() as nova:
                vms = nova.servers.list(search_opts={'all_tenants':1, 'tenant_id':tenant_uuid})
                return [get_vm_data(x) for x in vms]
        except Exception as e:
            logger.exception("Error getting list of vms for tenant %s", tenant_uuid)

        return []

    def _poweroff_vm(self, nova, vm_uuid):
        try:
            logger.info("powering off VM %s", vm_uuid)
            nova.servers.stop(vm_uuid)
            return SUCCESS_OK
        except novaclient.exceptions.NotFound:
            return ERR_NOT_FOUND
        except Exception as e:
            # if vm is in stopped state return success
            if "vm_state stopped" in str(e):
                return SUCCESS_OK
            else:
                logger.exception("Error powering off vm %s", vm_uuid)
                return ERR_UNKNOWN

    def _delete_vm(self, nova, vm_uuid):
        try:
            logger.info("Deleting VM %s", vm_uuid)
            nova.servers.delete(vm_uuid)
            return SUCCESS_OK
        except novaclient.exceptions.NotFound:
            return ERR_NOT_FOUND
        except Exception as e:
            logger.exception("Error deleting vm %s", vm_uuid)
            return ERR_UNKNOWN

    def poweroff_vms(self, vms):
        """
        Power off a VM on a given tenant
        :param tenant_uuid:
        :param vm_uuid:
        :return: dictionary of vm_id to result
        """
        result = {}
        try:
            with self._get_nova_client() as nova:
                for vm in vms:
                    result[vm['instance_uuid']] = self._poweroff_vm(nova, vm['instance_uuid'])
            return result
        except Exception as e:
            logger.exception("Error powering off vm %s", vms)
        return result

    def delete_vms(self, vms):
        """
        Delete a VM on a given tenant
        :param tenant_uuid:
        :param vm_uuid:
        :return: dictionary of vm_id to result
        """
        result = {}
        try:
            with self._get_nova_client() as nova:
                for vm in vms:
                    result[vm['instance_uuid']] = self._delete_vm(nova, vm['instance_uuid'])
            return result
        except Exception as e:
            logger.exception("Error deleting vm %s", vms)
        return result
