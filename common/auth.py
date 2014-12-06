"""
Module containing default authentication implementation (JWT) and hook for customizations. Provides two implementations:
noauth which is effectively a no-op and jwt which checks a JSON Web Token for specific roles.

"""

__author__ = 'jstubbs'

from base64 import b64decode
from Crypto.PublicKey import RSA
import functools
import logging

from django.conf import settings
import jwt as pyjwt
from rest_framework.response import Response
from rest_framework import status

from responses import error_dict

logger = logging.getLogger(__name__)

def decode_jwt(jwt_header):
    """
    Verifies the signature on the JWT against a public key.
    """
    # first, convert the public_key string to an RSA Key object:
    with open(settings.PUB_KEY, 'r') as f:
        public_key = f.read().replace('\n','')
    keyDER = b64decode(public_key)
    keyPub = RSA.importKey(keyDER)
    # verify the signature and return the base64-decoded message if verification passes
    return pyjwt.decode(jwt_header, keyPub)

def noauth(view, self, request, *args, **kwargs):
    """
    Pass-through to be used in testing or when services are locked down by other means (e.g. firewall).
    """
    return view(self, request, *args, **kwargs)

def jwt(view, self, request, *args, **kwargs):
    """
    Check the request for a JWT, verifies the signature and parses user
    information from it.
    """
    if not settings.CHECK_JWT:
        return view(self, request, *args, **kwargs)
    request.service_admin = False
    jwt_header = request.META.get(settings.JWT_HEADER)
    if not jwt_header:
        return Response(error_dict(msg="JWT missing."), status=status.HTTP_400_BAD_REQUEST)
    try:
        profile_data = decode_jwt(jwt_header)
        logger.info("profile_data: " + str(profile_data))
        request.username = profile_data.get('http://wso2.org/claims/enduser')
        if len(request.username.split('/')) == 2:
            request.username = request.username.split('/')[1]
        logger.info("username: " + str(request.username))
        if len(request.username.split('@')) == 2:
            request.username = request.username.split('@')[0]
        logger.info("username: " + str(request.username))
        roles = profile_data.get('http://wso2.org/claims/role')
        logger.info("roles: " + str(roles))
        if roles and settings.USER_ADMIN_ROLE in roles:
            request.service_admin = True
        logger.info('admin: ' + str(request.service_admin))
    except Exception as e:
        return Response(error_dict(msg=e.message), status=status.HTTP_400_BAD_REQUEST)

    return view(self, request, *args, **kwargs)

def authenticated(view):
    """
    View decorator dispatching authentication check to callable configured in settings.py.
    """
    # @wraps is a shortcut to partial; cf. http://docs.python.org/2/library/functools.html
    # preserves the name and docstring of the the decorated function.
    @functools.wraps(view)
    def _decorator(self, request, *args, **kwargs):
        try:
            auth_func = settings.auth_func
        except Exception:
        # defaults to using the jwt decorator
            auth_func = jwt
        # make the call
        try:
            rsp = auth_func(view, self, request, *args, **kwargs)
            return rsp
        except Exception as e:
            return Response(error_dict(msg=e.message), status=status.HTTP_400_BAD_REQUEST)

    return _decorator
