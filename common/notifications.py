__author__ = 'jstubbs'

import beanstalkc
import json
from django.conf import settings


def create_notification(username, event, owner):
    """
    Creates an Agave notification in the beanstalk queue.
    """
    beanstalk = beanstalkc.Connection(host=settings.BEANSTALK_SERVER, port=settings.BEANSTALK_PORT)
    beanstalk.use(settings.BEANSTALK_TUBE)
    uuid = build_profile_uuid(username)
    d = {"uuid": uuid, "event": event, "owner": owner}
    data = json.dumps(d)
    beanstalk.put(data)
    #msg = job.Job(data=data, conn=connection)
    #msg.Queue()

def build_profile_uuid(username):
    return settings.TENANT_UUID + "-" + username + "-" + settings.BEANSTALK_SRV_CODE
