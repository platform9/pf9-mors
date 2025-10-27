from sqlalchemy import Table, Column, MetaData, DateTime, Boolean
from sqlalchemy import inspect
from sqlalchemy import sql


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    inspector = inspect(migrate_engine)

    # Ensure instance_lease table exists (expected from earlier migrations)
    table_names = set(inspector.get_table_names())
    if 'instance_lease' not in table_names:
        return

    # Reflect table
    try:
        il = Table('instance_lease', meta, autoload_with=migrate_engine)
    except TypeError:
        # Fallback for older SQLAlchemy
        il = Table('instance_lease', meta, autoload=True)
    il_cols = {c['name'] for c in inspector.get_columns('instance_lease')}

    # Add missing columns idempotently
    if 'processed' not in il_cols:
        Column('processed', Boolean, server_default=sql.false()).create(il)
    if 'processed_at' not in il_cols:
        Column('processed_at', DateTime).create(il)


def downgrade(migrate_engine):
    # No-op: we avoid dropping columns in downgrade to prevent destructive changes
    pass
