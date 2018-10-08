from webhooks_handler import WebHooksHandler
# from slack_webhooks_handler import SlackWebHooksHandler


def get_webhooks_handler(conf, webhook_type=None):
    # if webhook_type.lower() == 'slack':
    #     return SlackWebHooksHandler(conf)
    # if conf.get("DEFAULT", "webhooks_handler", default=None) == "test":
    #     pass
        # return FakeWebHooksHandler(conf)
    return WebHooksHandler(conf)
