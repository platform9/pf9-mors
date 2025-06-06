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

    @db_connect(transaction=False)
    def get_all_tenant_leases(self, conn):
        return conn.execute(self.tenant_lease.select()).fetchall()

    @db_connect(transaction=False)
    def get_tenant_lease(self, conn, tenant_uuid):
        return conn.execute(self.tenant_lease.select(self.tenant_lease.c.tenant_uuid == tenant_uuid)).first()

    @db_connect(transaction=True)
    def add_tenant_lease(self, conn, tenant_uuid, expiry_mins, action, created_by, created_at):
        logger.debug("Adding tenant lease %s %d %s %s %s", tenant_uuid, expiry_mins, action, str(created_at), created_by)
        conn.execute(self.tenant_lease.insert(), tenant_uuid=tenant_uuid, expiry_mins=expiry_mins,
                     action=action, created_at=created_at, created_by=created_by)

    @db_connect(transaction=True)
    def update_tenant_lease(self, conn, tenant_uuid, expiry_mins, action, updated_by, updated_at):
        logger.debug("Updating tenant lease %s %d %s %s %s", tenant_uuid, expiry_mins, action, str(updated_at), updated_by)
        conn.execute(self.tenant_lease.update().where(
            self.tenant_lease.c.tenant_uuid == tenant_uuid).
                     values(expiry_mins=expiry_mins, action=action,
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
    def add_instance_lease(self, conn, instance_uuid, tenant_uuid, expiry, action, created_by, created_at):
        logger.debug("Adding instance lease %s %s %s %s %s", instance_uuid, tenant_uuid, expiry, action, created_by)
        conn.execute(self.instance_lease.insert(), instance_uuid=instance_uuid, tenant_uuid=tenant_uuid,
                     expiry=expiry, action=action,
                     created_at=created_at, created_by=created_by)

    @db_connect(transaction=True)
    def update_instance_lease(self, conn, instance_uuid, tenant_uuid, expiry, action, updated_by, updated_at):
        logger.debug("Updating instance lease %s %s %s %s %s", instance_uuid, tenant_uuid, expiry, action, updated_by)
        conn.execute(self.instance_lease.update().where(
            self.instance_lease.c.instance_uuid == instance_uuid).values
                     (tenant_uuid=tenant_uuid, expiry=expiry, action=action,
                      updated_at=updated_at, updated_by=updated_by))

    @db_connect(transaction=True)
    def delete_instance_leases(self, conn, instance_uuids):
        # Delete 10 at a time, should we soft delete
        logger.debug("Deleting instance leases %s", str(instance_uuids))
        conn.execute(self.instance_lease.delete().where(self.instance_lease.c.instance_uuid.in_(instance_uuids)))
