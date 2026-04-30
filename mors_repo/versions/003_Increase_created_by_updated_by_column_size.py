# Copyright Platform9 Systems Inc. 2016
from sqlalchemy import MetaData, Table, String


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    for table_name in ('tenant_lease', 'instance_lease'):
        table = Table(table_name, meta, autoload=True)
        table.c.created_by.alter(type=String(64))
        table.c.updated_by.alter(type=String(64))


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    for table_name in ('tenant_lease', 'instance_lease'):
        table = Table(table_name, meta, autoload=True)
        table.c.created_by.alter(type=String(40))
        table.c.updated_by.alter(type=String(40))
