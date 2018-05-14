import logging
import json
import requests
import random
from collections import namedtuple

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_NOTIFICATION_TEXT = "Your VM %s is about to be DELETED at %s :partyparrot:"

Result = namedtuple('Result', ['ok', 'message', 'instance'])


def get_emoticon():
    str = ""
    for _ in range(0, random.randint(0, 10)):
        str += ":partyparrot:"
    return str

class SlackWebHooksHandler:
    def __init__(self, conf):
        self.conf = conf
        self.DEFAULT_SLACK_URL = self.conf.get("DEFAULT", "slack_url", None)

    def _notify_one(self, vm):
        slack_url = vm.get('url', self.DEFAULT_SLACK_URL)
        if not slack_url:
            return "Not notifying, no URL found"
        # body = vm.get('body', DEFAULT_NOTIFICATION_TEXT)
        payload = {
            'text': DEFAULT_NOTIFICATION_TEXT % (vm['instance_uuid'], vm['expiry']),
            'attachments': [
                {
                    "color": "#FF0000",
                    "title": "Lease Expiring",
                    "text": "I will find it and I will delete it\n %s" % get_emoticon(),
                },
                # {
                #     "color": "#008000",
                #     "title": "Lease Expiring",
                #     "text": "I will save the VM",
                # }
            ]
        }
        try:
            requests.post(slack_url, verify=True, data=json.dumps(payload))
            message = "Successfully notified for %s" % vm['instance_uuid']
            return Result(True, message, vm['instance_uuid'])

        except Exception as exc:
            message = "Could not notify. failed: %s" % exc
            return Result(False, message, vm['instance_uuid'])

    def post(self, list_of_vms):
        result = list()
        if isinstance(list_of_vms, list):
            for vm in list_of_vms:
                result.append(self._notify_one(vm))
        else:
            result.append(self._notify_one(list_of_vms))
        return result

    def add_url(self):
        pass
