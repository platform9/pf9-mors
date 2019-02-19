import apprise
# create an Apprise instance
apobj = apprise.Apprise()
from keystoneauth1.exceptions.auth import AuthorizationFailure
from keystoneauth1.exceptions.auth_plugins import MissingAuthPlugin
from keystoneauth1.identity import v3
from keystoneauth1 import session


# Add all of the notification services by their server url.
# A sample email notification
apobj.add('mailto://myemail:mypass@gmail.com')




class ClemencyHandler:
    def __init__(self, conf):
        self.clemency_notify_handler = apprise.Apprise()
        self.clemency_notify_handler.add('json://localhost:46601/mors-notify?-X-Auth-Token=gAAAAABcZy081c9xYA6flfMBVwxweUb1pkXTbsIaSWKkf2qbmYzVO_PjlEuQ2VS9sb-nOYHzmG6ySPhF5hcmjCd6SkmlBUoUV8FH6Hp7664wGsfX7Ux_tWsmIrbnDVzftNTXoP34i0fGm5qsmHVsU0seVzdmKE9T_MpNMA_SByvfN1_ASZwgmfI')
        # self.conf = conf
        # self.DEFAULT_WEBHOOK_URL = self.conf.get("DEFAULT", "default_webhook_url", None)
        # self.default_message = ""
        # self.clemency_url = cu.get_url()
        # pass

    def notify_all(self, list_of_vms=None):
        # owner_email = ""
        # msg = ""
        # body = {
        #         'email': owner_email,
        #         'msg': msg
        #     }
        #
        all_users =
        for
        import pdb; pdb.set_trace()
        self.clemency_notify_handler.notify(
            title='my notification title',
            body='what a great notification service!',
        )
