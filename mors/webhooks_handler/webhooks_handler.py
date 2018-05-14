import logging

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class WebHooksHandler:
    def __init__(self, conf):
        self.conf = conf
        pass

    def _notify_one(self, vm):
        pass

    def post(self, list_of_vms):
        pass

    def add_url(self):
        pass
