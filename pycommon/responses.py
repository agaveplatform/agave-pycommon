"""
Utilities for generating responses across the API.
"""
import os
import json
from django.http import HttpResponseBadRequest, HttpResponse
from util import camelize, underscoreize
__author__ = 'deardooley'


def format_response(response_data, msg=None, query_dict={}):
    """Converts content to json while respecting config options. Responses will be pretty printed
    and filtered based on the query parameters
    :param response_data: dict|list
    :param msg: str
    :param query_dict: Dict
    :return: str|None
    """

    content = filter_fields(response_data, query_dict)
    content = success_dict(content, msg, query_dict)
    content = filter_naked_content(content, query_dict)
    content = filter_camel_case(content, query_dict)
    content = filter_pretty_print(content, query_dict)


    return content

def filter_camel_case(content, query_dict={}):
    """Ensures the response field names are consistently formatted in snake case if camel_case=false is
    present in the url query parameters. Otherwise the default camel case will be forced.

       :param response_data: dict|list
       :param query_dict: Dict
       :return: dict|None
    """
    camel = "true"
    if query_dict.has_key("camelCase"):
        camel = query_dict.get("camelCase", "true")
    elif query_dict.has_key("camel_case"):
        camel = query_dict.get("camel_case", "true")

    if camel.lower() == "false":
        return underscoreize(content)
    else:
        return camelize(content)

def filter_naked_content(content, query_dict={}):
    """Strips the response of all but the result object when naked=true is present in the url query string.
    :param response_data: dict|list
    :param query_dict: Dict
    :return: dict|None
    """
    naked = query_dict.get("naked", "false")
    if naked.lower() == "true":
        return content['result']
    else:
        return content

def filter_fields(content, query_dict={}):
    """Strips the response of all but the fields specified in the filter url query parameter. The value
    should be a comma separated list of fields given in json dot notation.

    This implementation only handles single level field names. Dot notation is not yet supported

    :param response_data: dict|list
    :param query_dict: dict
    :return: dict|None
    """
    filter = query_dict.get("filter")

    # return only the matching fields if a filter was given
    if filter:
        # create equivalent sized empty object
        if isinstance(content, list):
            filter_resp = []
            for i in range(len(content)):
                filter_resp.append({})
        else:
            filter_resp = {}

        # filter field is comma separated
        filter_fields = filter.split(',')

        # for each field name given in the filter, copy that key/value to the new response content
        for field_path in filter_fields:
            # if the content is a list, it must be applied to every entry
            if isinstance(content, list):
                i = 0
                for item in content:
                    filter_resp[i][field_path] = item[field_path]
                    i = i+1
            else:
                filter_resp[field_path] = content[field_path]
        return filter_resp

    else:

        return content


def filter_pretty_print(content, query_dict={}):
    """Pretty prints the content with 2 spaces if pretty=true is present in the url query parameters.

    :param response_data: dict|list
    :param query_dict: dict
    :return: str
    """
    indent = None
    separators = (',', ':')

    pretty_print = query_dict.get("pretty", "false")
    if pretty_print.lower() == "true":
        indent = 2
        separators = (', ', ': ')

    return json.dumps(content, indent=indent, separators=separators)


def error_response(msg=None):
    """
    Returns a 400 response in the proper JSON format.
    :param msg: str
    :return: HttpResponseBadRequest
    """
    response_data = {"Status": "Error",
                     "Message": msg,
                     "result": {}}
    return HttpResponseBadRequest(json.dumps(response_data),
                                  content_type="application/json")


def error_dict(content={}, msg=None, query_dict={}):
    """
    Enforces the '3 stanza' standard for error responses.

    :param content: dict|list
    :param msg: str
    :param query_dict: dict
    :return: HttpResponseBadRequest
    """
    naked = query_dict.get("naked", "false")
    if naked.lower() == "true":
        return content

    return {"status": "error",
            "message": msg,
            "result": content,
            "version": os.environ.get("AGAVE_VERSION", "2.2.6"),
            }


def success_dict(content={}, msg=None, query_dict={}):
    """
    Enforces the '3 stanza' standard for success responses.
    :param content: dict|list
    :param msg: str
    :param query_dict: dict
    :return: dict
    """

    return {"status": "success",
            "message": msg,
            "result": content,
            "version": os.environ.get("AGAVE_VERSION", "2.2.24"),
            }


def success_response(content={}, msg=None):
    """
    Returns a 200 response in the proper JSON format.

    :param content: dict|list
    :param msg: str
    :return: HttpResponseBadRequest
    """
    response_data = {"status": "Success",
                     "message": msg,
                     "result": content
                     }
    return HttpResponse(format_response(content),
                        content_type="application/json")
