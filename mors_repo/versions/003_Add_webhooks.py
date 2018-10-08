# Copyright Platform9 Systems Inc. 2018
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, VARCHAR, ForeignKey

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    tenant_lease = Table('tenant_lease', meta, autoload=True)
    instance_lease = Table('instance_lease', meta, autoload=True)

    wehbooks = Table(
        'webhooks', meta,
        Column('id', Integer, autoincrement=True, primary_key=True),
        Column('url', VARCHAR(500)),
        Column('tenant_uuid', String(40), ForeignKey(tenant_lease.c.tenant_uuid)),
        Column('instance_uuid', String(40), ForeignKey(instance_lease.c.instance_uuid)),
        Column('method', String(10), default="POST"),
        Column('retry_attempts', Integer, default=1),
        Column('body', String(500)),
        Column('content_type', String(50)),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('created_by', String(40)),
        Column('updated_by', String(40))
    )
    wehbooks.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    tenant_lease = Table('tenant_lease', meta, autoload=True)
    instance_lease = Table('instance_lease', meta, autoload=True)
    wehbooks = Table(
        'webhooks', meta,
        Column('id', Integer, autoincrement=True, primary_key=True),
        Column('url', VARCHAR(500)),
        Column('tenant_uuid', String(40), ForeignKey(tenant_lease.c.tenant_uuid)),
        Column('instance_uuid', String(40), ForeignKey(instance_lease.c.instance_uuid)),
        Column('method', String(10), default="POST"),
        Column('retry_attempts', Integer, default=1),
        Column('body', String(500)),
        Column('content_type', String(50)),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('created_by', String(40)),
        Column('updated_by', String(40))
    )
    wehbooks.drop()
