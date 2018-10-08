import logging
import json
import requests

from collections import namedtuple

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_NOTIFICATION_TEXT = "Your virtual machine %s is marked for deletion at %s"

Result = namedtuple('Result', ['ok', 'message', 'instance'])


class WebHooksHandler:
    def __init__(self, conf):
        self.conf = conf
        self.DEFAULT_WEBHOOK_URL = self.conf.get("DEFAULT", "default_webhook_url", None)

    def _notify_one(self, vm):
        notify_url = vm.get('url', self.DEFAULT_WEBHOOK_URL)
        if not notify_url:
            logger.warning("Not notifying, no valid URL found")
            return "Not notifying, no valid URL found"
        # body = vm.get('body', DEFAULT_NOTIFICATION_TEXT)
        payload = {
            'text': DEFAULT_NOTIFICATION_TEXT % (vm['instance_uuid'], vm['expiry']),
            'attachments': [
                {
                    "color": "#FF0000",
                    "title": "Lease Expiring",
                    "text": "I will find it and I will delete it\n "
                },
            ]
        }

        try:
            requests.post(notify_url, verify=True, data=json.dumps(payload))
            message = "Successfully notified for %s" % vm['instance_uuid']
            return Result(True, message, vm['instance_uuid'])

        except Exception as exc:
            message = "Could not notify. failed: %s" % exc
            return Result(False, message, vm['instance_uuid'])

    def post(self, list_of_vms):
        import pdb;pdb.set_trace()

        result = list()
        if isinstance(list_of_vms, list):
            for vm in list_of_vms:
                result.append(self._notify_one(vm))
        else:
            result.append(self._notify_one(list_of_vms))
        return result

    def add_url(self):
        pass
