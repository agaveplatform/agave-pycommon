__author__ = 'deardooley'

"""
Utilities for generating responses across the API.
"""
import json
from django.http import HttpResponseBadRequest, HttpResponse
from django.conf import settings
import util


def error_response(msg=None):
    """
    Returns a 400 response in the proper JSON format.
    """
    response_data = {"status": "error",
                     "message": msg,
                     "result":{}}

    return HttpResponseBadRequest(json.dumps(response_data),
                                  content_type="application/json")

def error_dict(result={}, msg=None, query_dict={}):
    """
    Enforces the '3 stanza' standard for error responses.
    """
    naked = query_dict.get("naked", "false")
    if naked.lower() == "true":
        return result

    snake = query_dict.get("snake", "true")
    if snake.lower() == "false":
        result = util.camelize(result)

    return {"status": "error",
            "message": msg,
            "result": result,
            "version": settings.TENANT_ID
    }

def success_dict(result={}, msg=None, query_dict={}):
    """
    Enforces the '3 stanza' standard for success responses.
    """
    naked = query_dict.get("naked", "false")
    if naked.lower() == "true":
        return result

    snake = query_dict.get("snake", "true")
    if snake.lower() == "false":
        result = util.camelize(result)

    return {"status": "success",
            "message": msg,
            "result": result,
            "version": settings.TENANT_ID,
    }

def success_response(result={}, msg=None):
    """
    Returns a 200 response in the proper JSON format.
    """
    response_data = {"status":"Success",
                     "message":msg,
                     "result": {},
                     }

    return  HttpResponse(json.dumps(response_data),
                         content_type="application/json")