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
import functools
import logging

from sqlalchemy import Table, MetaData
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


def db_connect(transaction=False):
    """
    Generates a decorator that get connection from a pool and returns
    it to the pool when the internal function is done
    :param transaction: (boolean) should this function create and end transaction.
    """

    def _db_connect(fun):
        if hasattr(fun, '__name__'):
            fun.__name__ = 'method_decorator(%s)' % fun.__name__
        else:
            fun.__name__ = 'method_decorator(%s)' % fun.__class__.__name__

        @functools.wraps(fun)
        def newfun(self, *args, **kwargs):
            trans = None
            conn = self.engine.connect()
            if transaction:
                trans = conn.begin()
            try:
                ret = fun(self, conn, *args, **kwargs)
                if transaction:
                    trans.commit()
                return ret
            except Exception:
                if transaction:
                    trans.rollback()
                logger.exception("Error during transaction ")
                raise
            finally:
                conn.close()

        return newfun

    return _db_connect


class DbPersistence:
    def __init__(self, db_conn_string):
        self.engine = create_engine(db_conn_string, poolclass=QueuePool)
        self.metadata = MetaData(bind=self.engine)
        self.tenant_lease = Table('tenant_lease', self.metadata, autoload=True)
        self.instance_lease = Table('instance_lease', self.metadata, autoload=True)
        self.webhooks = Table('webhooks', self.metadata, autoload=True)

    @db_connect(transaction=False)
    def get_all_tenant_leases(self, conn):
        return conn.execute(self.tenant_lease.select()).fetchall()

    @db_connect(transaction=False)
    def get_tenant_lease(self, conn, tenant_uuid):
        return conn.execute(self.tenant_lease.select(self.tenant_lease.c.tenant_uuid == tenant_uuid)).first()

    @db_connect(transaction=True)
    def add_tenant_lease(self, conn, tenant_uuid, expiry_mins, created_by, created_at):
        logger.debug("Adding tenant lease %s %d %s %s", tenant_uuid, expiry_mins, str(created_at), created_by)
        conn.execute(self.tenant_lease.insert(), tenant_uuid=tenant_uuid, expiry_mins=expiry_mins,
                     created_at=created_at, created_by=created_by)

    @db_connect(transaction=True)
    def update_tenant_lease(self, conn, tenant_uuid, expiry_mins, updated_by, updated_at):
        logger.debug("Updating tenant lease %s %d %s %s", tenant_uuid, expiry_mins, str(updated_at), updated_by)
        conn.execute(self.tenant_lease.update().where(
            self.tenant_lease.c.tenant_uuid == tenant_uuid).
                     values(expiry_mins=expiry_mins,
                            updated_at=updated_at, updated_by=updated_by))

    @db_connect(transaction=True)
    def delete_tenant_lease(self, conn, tenant_uuid):
        # Should we just soft delete ?
        logger.debug("Deleting tenant lease %s", tenant_uuid)
        conn.execute(self.tenant_lease.delete().where(self.tenant_lease.c.tenant_uuid == tenant_uuid))
        conn.execute(self.instance_lease.delete().where(self.instance_lease.c.tenant_uuid == tenant_uuid))

    @db_connect(transaction=False)
    def get_instance_leases_by_tenant(self, conn, tenant_uuid):
        return conn.execute(self.instance_lease.select(
                self.instance_lease.c.tenant_uuid == tenant_uuid)).fetchall()

    @db_connect(transaction=False)
    def get_instance_lease(self, conn, instance_uuid):
        return conn.execute(self.instance_lease.select((
                        self.instance_lease.c.instance_uuid == instance_uuid))).first()

    @db_connect(transaction=True)
    def add_instance_lease(self, conn, instance_uuid, tenant_uuid, expiry, created_by, created_at):
        logger.debug("Adding instance lease %s %s %s %s", instance_uuid, tenant_uuid, expiry, created_by)
        conn.execute(self.instance_lease.insert(), instance_uuid=instance_uuid, tenant_uuid=tenant_uuid,
                     expiry=expiry,
                     created_at=created_at, created_by=created_by)

    @db_connect(transaction=True)
    def update_instance_lease(self, conn, instance_uuid, tenant_uuid, expiry, updated_by, updated_at):
        logger.debug("Updating instance lease %s %s %s %s", instance_uuid, tenant_uuid, expiry, updated_by)
        conn.execute(self.instance_lease.update().where(
            self.instance_lease.c.instance_uuid == instance_uuid).values
                     (tenant_uuid=tenant_uuid, expiry=expiry,
                      updated_at=updated_at, updated_by=updated_by, notified=False))

    @db_connect(transaction=True)
    def delete_instance_leases(self, conn, instance_uuids):
        # Delete 10 at a time, should we soft delete
        logger.debug("Deleting instance leases %s", str(instance_uuids))
        conn.execute(self.instance_lease.delete().where(self.instance_lease.c.instance_uuid.in_(instance_uuids)))

    @db_connect(transaction=True)
    def stop_notifications(self, conn, instance_uuid):
        logger.debug("Stopping notifications for %s", str(instance_uuid))
        conn.execute(self.instance_lease.update().where(
            self.instance_lease.c.instance_uuid.in_(instance_uuid)).values(notified=True))

    @db_connect(transaction=True)
    def add_webhook(self, conn, url, method, retry_attempts, body, content_type, res_id, res_type="tenant"):
        import pdb;pdb.set_trace()
        logger.debug("Adding webhook %s", url)
        # if not res_type:
        conn.execute(self.webhooks.insert(), url=url, method=method,
                     retry_attempts=retry_attempts, body=body,
                     content_type=content_type)
        # else:
        import pdb;pdb.set_trace()
        if res_type == "tenant":
            conn.execute(self.tenant_lease.update().where(
                self.tenant_lease.c.tenant_uuid == res_id).
                         values(webhook=url))
        elif res_type == "instance":
            conn.execute(self.instance_lease.update().where(
                self.instance_lease.c.instance_uuid == res_id).
                         values(webhook=url))

    @db_connect(transaction=False)
    def get_webhook(self, conn):
            return conn.execute(self.webhooks.select()).fetchall()

    @db_connect(transaction=True)
    def delete_webhook(self, conn, url):
        logger.debug("Deleting webhook %s", url)
        # add logic to delete from instance and tenant table
        conn.execute(self.webhooks.delete().where(self.webhooks.c.url == url))

    @db_connect(transaction=False)
    def get_webhook_for_resource(self, conn, res_id, res_type='tenant'):
        if res_type == "instance":
            return conn.execute(self.webhooks.select(self.instance_lease.c.instance_uuid == res_id and
                                                     self.webhooks.c.webhook == self.instance_lease.c.webhook)).first()
        return conn.execute(self.webhooks.select(self.tenant_lease.c.tenant_uuid == res_id
                                                 and self.webhooks.c.webhook == self.tenant_lease.c.webhook)).first()
