__author__ = 'deardooley'

import logging
import beanstalkc
import json
from django.conf import settings
from util import deprecated

def create_generic_notification(uuid, event, owner, body=None, tenant=None):
    """
    Formats a profile notification 'event' for the given 'profile' and
    attributs it to the 'owner'.
    """
    if not uuid:
        if not body.uuid:
            raise Exception("No uuid provided")

    if not event:
        raise Exception("No event provided")

    if not owner:
        raise Exception("No username to attribute the event provided")

    if not tenant:
        tenant = settings.TENANT_ID

    message_data = {"uuid": uuid, "event": event, "owner": owner, "tenant": tenant, "context": body}

    _push_notification_to_queue(message_data)


@deprecated
def create_notification(username, event, owner, body=None, tenant=None):
    """
    Formats a profile notification 'event' for the given 'username,'
    attributed to the 'owner'. body should always be the user profile

    """
    uuid = build_profile_uuid(username)

    if not body:
        body = { "username": username, "uuid": uuid }

    message_data = {"uuid": uuid, "event": event, "owner": owner, "tenant": settings.TENANT_ID, "context": body}

    create_generic_notification(uuid, event, owner, body, tenant)


def _push_notification_to_queue(message_data):
    """
    Serializes the data dict and pushes it onto the message queue  
    """
    if message_data:
        beanstalk = beanstalkc.Connection(host=settings.BEANSTALK_SERVER, port=settings.BEANSTALK_PORT)
        beanstalk.use(settings.BEANSTALK_TUBE)
        data = json.dumps(message_data)
        beanstalk.put(data)
        logging.debug("Message " + data + " placed on queue")
    else:
        logging.debug("Skipping pushing empty notification onto queue");

def build_profile_uuid(username):
    return settings.TENANT_UUID + "-" + username + "-" + settings.BEANSTALK_SRV_CODE
