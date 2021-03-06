"""
Module containing default authentication implementation (JWT) and hook for customizations. Provides two implementations:
noauth which is effectively a no-op and jwt which checks a JSON Web Token for specific roles.

"""
__author__ = 'jstubbs'

from jwt import InvalidSignatureError, InvalidTokenError, PyJWTError, InvalidAlgorithmError

import base64
from Crypto.PublicKey import RSA
import functools
import logging
from django.conf import settings

import jwt
from jwt.contrib.algorithms.pycrypto import RSAAlgorithm

from rest_framework.response import Response
from rest_framework import status
import requests

from responses import error_dict
from error import Error

logger = logging.getLogger(__name__)

# use the pycrypto compatibility for legacy format support
jwt.unregister_algorithm('RS256')
jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))

def decode_jwt(jwt_header, verify=False):
    """
    Verifies the signature on the JWT against a public key.
    """
    try:
        with open(settings.PUB_KEY, "rb") as f:
            logger.info("Reading JWT public key from disk at \"{}\".".format(settings.PUB_KEY))
            pubkey = f.read()
            if pubkey:
                # ensure we can read the file with or without the cert wrapper text
                pubkeylines = pubkey.splitlines()
                if pubkeylines[0].startswith('-----BEGIN') and  pubkeylines[len(pubkeylines) - 1].startswith('-----END'):
                    b64data = '\n'.join(pubkey.splitlines()[1:-1]).replace('\n', '')
                else:
                    b64data = '\n'.join(pubkey.splitlines()).replace('\n', '')
        f.close()
    except OSError as err:
        raise Error("Unable to read JWT public key file from disk at \"{}\".".format(settings.PUB_KEY))

    # the pub key is just a base64 encoded DER key at this point
    derdata = base64.b64decode(b64data)
    # import the DER key as an RSA public key
    pubkey = RSA.importKey(derdata)
    # pass the key to pyjwt to parsing
    return jwt.decode(jwt_header, pubkey, algorithms='RS256')


def authenticate_user_to_store(username, password):
    """
    Authenticates a WSO2 user against in API Store and returns the cookies
    set on the session.
    Required: username, password.
    """
    url = settings.APIM_STORE_SERVICES_BASE_URL + settings.STORE_AUTH_URL
    data = {'action':'login',
            'username':username,
            'password':password}
    try:
        r = requests.post(url, data, verify=False)
    except Exception as e:
        raise Error(str(e))
    if not r.status_code == 200:
        raise Error("Unable to authenticate user; status code: "
                    + str(r.status_code) + "msg:" + str(r.content))
    if r.json().get("error"):
        logger.info("content:" + str(r.json()))
        if r.json().get("message"):
            raise Error(r.json().get("message").strip())
        raise Error("Invalid username/password combination.")
    return r.cookies

def apim_auth(request):
    """
    Pulls the authorization header from the request and uses it to authenticate the user
    to the WSO2 API Store.
    """
    # if 'HTTP_AUTHORIZATION' in request.META:
    auth = request.META['HTTP_AUTHORIZATION'].split()
    if len(auth) == 2:
        # NOTE: We are only support basic authentication for now.
        if auth[0].lower() == "basic":
            username, password = base64.b64decode(auth[1]).split(':')
            cookies = authenticate_user_to_store(username, password)
            return username, cookies

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    raise Error("Invalid Authorization header format.")




# ---------------
# Auth Functions
# ---------------

# The following functions can be used for the auth_func setting in your Django project.

def noauth(view, self, request, *args, **kwargs):
    """
    Pass-through to be used in testing or when services are locked down by other means (e.g. firewall).
    """
    return view(self, request, *args, **kwargs)

def basicauth(view, self, request, *args, **kwargs):
    """
    Use basic auth against WSO2 API Manager.
    """
    if not 'HTTP_AUTHORIZATION' in request.META:
        return Response(error_dict(msg="Authorization header missing or invalid."),
                status=status.HTTP_401_UNAUTHORIZED,
                headers={'WWW-Authenticate': 'Basic realm="Agave Platform"'})
    try:
        username, cookies = apim_auth(request)
        request.wso2_username = username
        request.wso2_cookies = cookies
    except Error as e:
        return Response(error_dict(msg=e.message), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.info("Uncaught exception in authenticated decorator: " + str(e))
        return Response(error_dict(msg="Unable to authenticate user."), status=status.HTTP_400_BAD_REQUEST)
    return view(self, request, *args, **kwargs)

def jwtauth(view, self, request, *args, **kwargs):
    """
    Check the request for a JWT, verifies the signature and parses user
    information from it.
    """
    request.username = None
    request.service_admin = False
    jwt_header = request.META.get(settings.JWT_HEADER)
    if not jwt_header:
        return Response(error_dict(msg="JWT missing."), status=status.HTTP_400_BAD_REQUEST)
    try:
        profile_data = decode_jwt(jwt_header, settings.CHECK_JWT)
        request.jwt = profile_data
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
    except InvalidAlgorithmError as e:
        return Response(error_dict(msg="Unsupported algorithm used to sign the JWT. error: " + e.message), status=status.HTTP_401_UNAUTHORIZED)
    except InvalidSignatureError as e:
        return Response(error_dict(msg="Invalid signature found for jwt. error: " + e.message), status=status.HTTP_401_UNAUTHORIZED)
    except PyJWTError as e:
        return Response(error_dict(msg="Invalid JWT found. error: " + e.message), status=status.HTTP_401_UNAUTHORIZED)
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
        auth_func = None
        try:
            if settings.AUTH_FUNC == 'basicauth':
                auth_func = basicauth
            elif settings.AUTH_FUNC == 'noauth':
                auth_func = noauth
        except Exception:
            pass
        # defaults to using the jwt decorator
        if not auth_func:
            auth_func = jwtauth
        # make the call
        try:
            rsp = auth_func(view, self, request, *args, **kwargs)
            return rsp
        except Exception as e:
            return Response(error_dict(msg=e.message), status=status.HTTP_400_BAD_REQUEST)

    return _decorator
