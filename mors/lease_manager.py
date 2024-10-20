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

from datetime import datetime, timedelta

from .leasehandler import get_lease_handler
from .persistence import DbPersistence
from eventlet.greenthread import spawn_after
import logging
from .leasehandler.constants import SUCCESS_OK, ERR_UNKNOWN, ERR_NOT_FOUND

logger = logging.getLogger(__name__)
DEFAULT_ACTION = 'power off'

def get_tenant_lease_data(data):
    """
    Simple function to transform tenant database proxy object into an externally
    consumable dictionary.
    :param data: database row object
    """
    return {'vm_lease_policy': {'tenant_uuid': data['tenant_uuid'],
                                'expiry_mins': data['expiry_mins'],
                                'action': data['action'],
                                'created_at': data['created_at'],
                                'created_by': data['created_by'],
                                'updated_at': data['updated_at'],
                                'updated_by': data['updated_by']}}


def get_vm_lease_data(data):
    """
    Simple function to transform instance database proxy object into an externally
    consumable dictionary.
    :param data: database row object
    """
    return {'instance_uuid': data['instance_uuid'],
            'tenant_uuid': data['tenant_uuid'],
            'expiry': data['expiry'],
            'action': data['action'],
            'created_at': data['created_at'],
            'created_by': data['created_by'],
            'updated_at': data['updated_at'],
            'updated_by': data['updated_by']}


class LeaseManager:
    """
    Lease Manager is the main class for mors dealing with CRUD operations for the REST API
    as well as the actual deletion of the Instances. Instance deletion and discovery is achieved
    through an object 'leasehandler'.
    """
    def __init__(self, conf):
        self.domain_mgr = DbPersistence(conf.get("DEFAULT", "db_conn"))
        self.lease_handler = get_lease_handler(conf)
        self.sleep_seconds = conf.getint("DEFAULT", "sleep_seconds")

    def add_tenant_lease(self, context, tenant_obj):
        logger.info("Adding tenant lease %s", tenant_obj)
        if 'action' in tenant_obj:                                        
            action = tenant_obj['action']                                 
        else:                                                             
            action = DEFAULT_ACTION  
        self.domain_mgr.add_tenant_lease(                                 
            tenant_obj['tenant_uuid'],                                          
            tenant_obj['expiry_mins'],                                          
            action,                                                             
            context.user_id,                                                    
            datetime.utcnow())

    def update_tenant_lease(self, context, tenant_obj):
        logger.info("Update tenant lease %s", tenant_obj)
        self.domain_mgr.update_tenant_lease(
            tenant_obj['tenant_uuid'],
            tenant_obj['expiry_mins'],
            tenant_obj['action'],
            context.user_id,
            datetime.utcnow())

    def delete_tenant_lease(self, context, tenant_id):
        logger.info("Delete tenant lease %s", tenant_id)
        return self.domain_mgr.delete_tenant_lease(tenant_id)

    def get_tenant_leases(self, context):
        logger.debug("Getting all tenant lease")
        all_tenants = self.domain_mgr.get_all_tenant_leases()
        all_tenants = [get_tenant_lease_data(x) for x in all_tenants]
        logger.debug("Getting all tenant lease %s", all_tenants)
        return all_tenants

    def get_tenant_lease(self, context, tenant_id):
        data = self.domain_mgr.get_tenant_lease(tenant_id)
        logger.debug("Getting tenant lease %s", data)
        if data:
            return get_tenant_lease_data(data)
        return {}

    def get_tenant_and_associated_instance_leases(self, context, tenant_uuid):
        logger.debug("Getting tenant and instances leases %s", tenant_uuid)
        return {
            'tenant_lease': self.get_tenant_lease(context, tenant_uuid),
            'all_vms':
                [get_vm_lease_data(x) for x in self.domain_mgr.get_instance_leases_by_tenant(tenant_uuid)]
        }

    def check_instance_lease_violation(self, instance_lease, tenant_lease):
        violation = False
        expiry = instance_lease['expiry']
        if (datetime.utcnow() + timedelta(seconds=tenant_lease['expiry_mins']*60)) < expiry:
            violation = True
        return violation

    def get_instance_lease(self, context, instance_id):
        data = self.domain_mgr.get_instance_lease(instance_id)
        if data:
            data = get_vm_lease_data(data)
        logger.debug("Get instance lease %s %s", instance_id, data)
        return data

    def add_instance_lease(self, context, tenant_uuid, instance_lease_obj):
        logger.info("Add instance lease %s", instance_lease_obj)
        tenant_lease = self.domain_mgr.get_tenant_lease(tenant_uuid)
        if not self.check_instance_lease_violation(instance_lease_obj, tenant_lease):
            if 'action' in instance_lease_obj:                            
                action = instance_lease_obj['action']                           
            else:                                                               
                action = DEFAULT_ACTION      
            self.domain_mgr.add_instance_lease(instance_lease_obj['instance_uuid'],  
                                           tenant_uuid,                              
                                           instance_lease_obj['expiry'],             
                                           action,                                   
                                           context.user_id,                          
                                           datetime.utcnow())  
        else:
            raise ValueError("Instance lease exceeds tenant lease")

    def update_instance_lease(self, context, tenant_uuid, instance_lease_obj):
        logger.info("Update instance lease %s", instance_lease_obj)
        tenant_lease = self.domain_mgr.get_tenant_lease(tenant_uuid)
        if not self.check_instance_lease_violation(instance_lease_obj, tenant_lease):
            self.domain_mgr.update_instance_lease(instance_lease_obj['instance_uuid'],
                                              tenant_uuid,
                                              instance_lease_obj['expiry'],
                                              instance_lease_obj['action'],
                                              context.user_id,
                                              datetime.utcnow())
        else:
            raise ValueError("Instance lease exceeds tenant lease")

    def delete_instance_lease(self, context, instance_uuid):
        logger.info("Delete instance lease %s", instance_uuid)
        self.domain_mgr.delete_instance_leases([instance_uuid])

    def start(self):
        spawn_after(self.sleep_seconds, self.run)

    # Could have used a generator here, would save memory but wonder if it is a good idea given the error conditions
    # This is a simple implementation which goes and deletes VMs one by one
    def _get_vms_to_delete_or_poweroff_for_tenant(self, tenant_uuid, expiry_mins, action):
        vms_to_delete = []
        vms_to_poweroff = []
        vm_ids_to_delete = set()
        vm_ids_to_poweroff = set()
        do_not_delete = set()
        now = datetime.utcnow()
        add_seconds = timedelta(seconds=expiry_mins*60)
        instance_leases = self.get_tenant_and_associated_instance_leases(None, tenant_uuid)['all_vms']
        for i_lease in instance_leases:
            if now > i_lease['expiry']:
                if i_lease['action'] == 'delete':
                     logger.info("Explicit lease for %s queueing for deletion", i_lease['instance_uuid'])
                     vms_to_delete.append(i_lease)
                     vm_ids_to_delete.add(i_lease['instance_uuid'])
                else:
                     logger.info("Explicit lease for %s queueing up to Power off", i_lease['instance_uuid'])
                     vms_to_poweroff.append(i_lease)
                     vm_ids_to_poweroff.add(i_lease['instance_uuid'])
            else:
                do_not_delete.add(i_lease['instance_uuid'])
                logger.debug("Ignoring vm, vm not expired yet %s", i_lease['instance_uuid'])

        tenant_vms = self.lease_handler.get_all_vms(tenant_uuid)
        for vm in tenant_vms:
            expiry_date = vm['created_at'] + add_seconds
            if now > expiry_date and vm['instance_uuid'] not in vm_ids_to_delete \
                                 and vm['instance_uuid'] not in vms_to_poweroff \
                                 and vm['instance_uuid'] not in do_not_delete:
                if action == 'delete':
                     logger.info("Instance %s queued up for deletion, creation date %s", vm['instance_uuid'],
                            vm['created_at'])
                     vms_to_delete.append(vm)
                else:
                     logger.info("Instance %s queued up to Power off, creation date %s", vm['instance_uuid'],
                            vm['created_at'])
                     vms_to_poweroff.append(vm)
            else:
                logger.debug("Ignoring vm, vm not expired yet or already powered off or deleted %s, %s", vm['instance_uuid'],
                             vm['created_at'])

        return (vms_to_delete, vms_to_poweroff)

    def _delete_or_poweroff_vms_for_tenant(self, t_lease):
        tenant_vms_to_delete, tenant_vms_to_poweroff = self._get_vms_to_delete_or_poweroff_for_tenant(t_lease['tenant_uuid'], t_lease['expiry_mins'], t_lease['action'])

        remove_from_db = []
        # Keep it simple and delete them serially
        if tenant_vms_to_delete:
            result = self.lease_handler.delete_vms(tenant_vms_to_delete)
            for vm_result in result.items():  
                # If either the VM has been successfully deleted or has already been deleted
                if vm_result[1] == SUCCESS_OK or vm_result[1] == ERR_NOT_FOUND:
                    remove_from_db.append(vm_result[0])
 
        if tenant_vms_to_poweroff:
            result = self.lease_handler.poweroff_vms(tenant_vms_to_poweroff)
            for vm_result in result.items():
                # If either the VM has been successfully powered off or has already been powered off
                if vm_result[1] == SUCCESS_OK or vm_result[1] == ERR_NOT_FOUND:
                    remove_from_db.append(vm_result[0])        

        if len(remove_from_db) > 0:
            logger.info("Removing vms %s from db", remove_from_db)
            self.domain_mgr.delete_instance_leases(remove_from_db)

    def run(self):
        # Delete the cleanup
        tenant_leases = self.domain_mgr.get_all_tenant_leases()
        for t_lease in tenant_leases:
            self._delete_or_poweroff_vms_for_tenant(t_lease)

        # Sleep again for sleep_seconds
        spawn_after(self.sleep_seconds, self.run)
