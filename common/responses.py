"""
Utilities for generating responses across the API.
"""
import json
from django.http import HttpResponseBadRequest, HttpResponse

__author__ = 'jstubbs'

def error_response(msg=None):
    """
    Returns a 400 response in the proper JSON format.
    """
    response_data = {"Status": "Error",
                     "Message": msg,
                     "result":{}}
    return HttpResponseBadRequest(json.dumps(response_data),
                                  content_type="application/json")

def error_dict(result={}, msg=None):
    """
    Enforces the '3 stanza' standard for error responses.
    """
    return {"status": "error",
            "message": msg,
            "result": result,
            "version": "2.0.0-SNAPSHOT-rc3fad",
    }

def success_dict(result={}, msg=None, query_dict={}):
    """
    Enforces the '3 stanza' standard for success responses.
    """
    naked = query_dict.get("naked", "false")
    if naked.lower() == "true":
        return result

    return {"status": "success",
            "message": msg,
            "result": result,
            "version": "2.0.0-SNAPSHOT-rc3fad",
    }

def success_response(result={}, msg=None):
    """
    Returns a 200 response in the proper JSON format.
    """
    response_data = {"status":"Success",
                     "message":msg,
                     "result":result
                     }
    return  HttpResponse(json.dumps(response_data),
                         content_type="application/json")
