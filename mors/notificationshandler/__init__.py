# from email_handler import EmailHandler
from clemency_handler import ClemencyHandler


def get_notifications_handler(conf, notification_type='email'):
    if notification_type == 'email':
        return ClemencyHandler(conf)
        # return EmailHandler(conf)
