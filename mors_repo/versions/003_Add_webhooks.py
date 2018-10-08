# Copyright Platform9 Systems Inc. 2018
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, VARCHAR

meta = MetaData()

wehbooks = Table(
    'webhooks', meta,
    Column('url', VARCHAR(500), primary_key=True),
    Column('tenant_uuid', String(40)),
    Column('instance_uuid', String(40)),
    Column('method', String(10), default="POST"),
    Column('retry_attempts', Integer, default=1),
    Column('body', String(500)),
    Column('content_type', String(50)),
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('created_by', String(40)),
    Column('updated_by', String(40))
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    wehbooks.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    wehbooks.drop()
