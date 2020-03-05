import binascii
import functools
import jwt
import logging

from base64 import urlsafe_b64encode, urlsafe_b64decode
from bottle import abort, request, response, redirect
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from urllib.parse import urlencode

from .misc import set_headers

log = logging.getLogger(__name__)


OIDC_COOKIE = 'shh_oidc'
OIDC_MAX_AGE = 60 * 10  # 10 minutes
SESSION_COOKIE = 'shh_session'
SESSION_MAX_AGE = 60 * 60 * 24  # 24 hours
# Headers to prevent responses that use a session from being cached.
CACHE_HEADERS = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-store',
}


class TokenDecoder(object):

    def __init__(self, oidc_public_key, oidc_iss, oidc_client_id):
        self.oidc_public_key = oidc_public_key
        self.oidc_iss = oidc_iss
        self.oidc_client_id = oidc_client_id

    def decode_id_token(self, token):
        payload = jwt.decode(token, self.oidc_public_key,
                             algorithms='RS256',
                             issuer=self.oidc_iss,
                             audience=self.oidc_client_id)
        return payload


class SessionHandler(object):

    def __init__(self, token_decoder, login_endpoint='login', testing_mode=False):

        self.token_decoder = token_decoder
        self.login_endpoint = login_endpoint
        self.testing_mode = testing_mode
        # Add prefix to cookies to improve security.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#Cookie_prefixes
        self.oidc_cookie = OIDC_COOKIE if self.testing_mode else f'__Host-{OIDC_COOKIE}'
        self.session_cookie = SESSION_COOKIE if self.testing_mode else f'__Host-{SESSION_COOKIE}'

    def redirect_to_login(self, continue_url=None, client_id=None):
        continue_url = continue_url or request.url
        url_params = {'continue': continue_url}
        if client_id:
            url_params['client_id'] = client_id
        redirect(f'/{self.login_endpoint}?{urlencode(url_params)}')

    def set_oidc_state(self, state, nonce, continue_url):
        oidc_state = f'{state}:{nonce}:{continue_url}'
        encoded_oidc_state = urlsafe_b64encode(oidc_state.encode('utf-8')).decode('utf-8')
        # TODO: Set `same_site=True` once Bottle supports it
        response.set_cookie(self.oidc_cookie, encoded_oidc_state,
                            path='/oidc/callback',
                            max_age=OIDC_MAX_AGE, httponly=True,
                            secure=False if self.testing_mode else True)

    def clear_oidc_state(self):
        response.delete_cookie(self.oidc_cookie, path='/oidc/callback')

    def get_oidc_state(self):
        encoded_oidc_state = request.get_cookie(self.oidc_cookie)
        if not encoded_oidc_state:
            return None

        try:
            oidc_state = urlsafe_b64decode(encoded_oidc_state.encode('utf-8')).decode('utf-8')
            state, nonce, continue_url = oidc_state.split(':', 2)
        except (binascii.Error, ValueError) as e:
            log.warning('Received invalid oidc state cookie: %(error)s', {'error': e})
            return None

        return {'state': state,
                'nonce': nonce,
                'continue_url': continue_url}

    def set_session(self, id_token):
        # TODO: Set `same_site=True` once Bottle supports it
        response.set_cookie(self.session_cookie, id_token,
                            path='/',
                            max_age=SESSION_MAX_AGE, httponly=True,
                            secure=False if self.testing_mode else True)

    def clear_session(self):
        response.delete_cookie(self.session_cookie, path='/')

    def _get_session(self):
        id_token = request.get_cookie(self.session_cookie)
        if not id_token:
            return None

        try:
            session_jwt = self.token_decoder.decode_id_token(id_token)

        # If there's anything wrong with the session token, pretend there is none, so we can
        # generate a new one.
        except ExpiredSignatureError:
            return None
        except InvalidTokenError as e:
            log.warning('Received invalid session token: %(error)s', {'error': e})
            return None

        return {'user_id': session_jwt['sub'],
                # Use id token id as the CSRF token.
                'csrf': session_jwt['jti']}

    def _check_csrf(self, session):
        if request.method == 'POST':
            request_csrf = request.forms.get('csrf')
            if not request_csrf or request_csrf != session['csrf']:
                abort(403, text=None)

    def require_session(self, check_csrf=True):

        def decorator(f):

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                session = self._get_session()
                if not session:
                    self.redirect_to_login()

                if check_csrf:
                    self._check_csrf(session)

                request.session = session
                r = f(*args, **kwargs)
                set_headers(r, CACHE_HEADERS)
                return r

            return wrapper

        return decorator

    def maybe_session(self, check_csrf=True):

        def decorator(f):

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                session = self._get_session()
                if not session:
                    request.session = None
                    r = f(*args, **kwargs)
                    set_headers(r, CACHE_HEADERS)
                    return r

                if check_csrf:
                    self._check_csrf(session)

                request.session = session
                r = f(*args, **kwargs)
                set_headers(r, CACHE_HEADERS)
                return r

            return wrapper

        return decorator
