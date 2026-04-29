#!/bin/bash

set -ex

cat /root/templates/pf9-mors.ini | envsubst > /etc/pf9/pf9-mors.ini
cat /root/templates/pf9-mors-api-paste.ini | envsubst > /etc/pf9/pf9-mors-api-paste.ini

python /opt/pf9/pf9-mors/bin/mors_manage.py --command db_sync

exec python /opt/pf9/pf9-mors/bin/pf9_mors.py
