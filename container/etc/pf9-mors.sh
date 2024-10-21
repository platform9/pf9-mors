#!/bin/bash

set -ex

python /opt/pf9/pf9-mors/bin/mors_manage.py --command db_sync

exec python /opt/pf9/pf9-mors/bin/pf9_mors.py >> /var/log/pf9/pf9-mors.log 2>&1
