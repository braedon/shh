import logging
import requests
import rfc3339
import time

from bottle import Bottle, request, response, static_file, template, redirect
from datetime import timedelta
from jwt.exceptions import InvalidTokenError
from urllib.parse import urlparse, urljoin

from utils.param_parse import parse_params, string_param

from .dao import Secret
from .misc import abort, html_default_error_hander, generate_id, security_headers
from .session import SessionHandler


log = logging.getLogger(__name__)


DEFAULT_CONTINUE_URL = '/'

VALID_TTLS = {
    '1h': (timedelta(hours=1), '1 hour'),
    '30m': (timedelta(minutes=30), '30 minutes'),
    '15m': (timedelta(minutes=15), '15 minutes'),
    '5m': (timedelta(minutes=5), '5 minutes'),
}


def construct_app(dao, token_decoder,
                  service_protocol, service_hostname,
                  service_port, service_path,
                  oidc_name, oidc_auth_endpoint, oidc_token_endpoint,
                  oidc_client_id, oidc_client_secret,
                  testing_mode,
                  **kwargs):

    session_handler = SessionHandler(token_decoder, testing_mode=testing_mode)

    app = Bottle()
    app.default_error_handler = html_default_error_hander
    app.install(security_headers)

    service_address = f'{service_protocol}://{service_hostname}'
    if service_port:
        service_address += f':{service_port}'
    if service_path:
        service_address += service_path

    oidc_redirect_uri = urljoin(service_address, '/oidc/callback')

    def check_continue_url(continue_url):
        try:
            parsed_continue_url = urlparse(continue_url)
        except ValueError:
            log.warning('Received invalid continue url: %(continue_url)s',
                        {'continue_url': continue_url})
            abort(400)

        if parsed_continue_url.scheme or parsed_continue_url.netloc:
            # Absolute url - check it's for this service'
            if not continue_url.startswith(service_address):
                log.warning('Received continue url for another service: %(continue_url)s',
                            {'continue_url': continue_url})
                abort(400)

    @app.get('/status')
    def status():
        return 'OK'

    @app.get('/')
    @session_handler.maybe_session()
    def index():
        if request.session:
            user_id = request.session['user_id']
            csrf = request.session['csrf']
        else:
            user_id = csrf = None

        return template('index',
                        user_id=user_id,
                        csrf=csrf)

    @app.get('/main.css')
    def css():
        return static_file('main.css', root='static')

    @app.get('/robots.txt')
    def robots():
        return static_file('robots.txt', root='static')

    # Favicon stuff generated at:
    # https://favicon.io/favicon-generator/?t=S%21&ff=Raleway&fs=110&fc=%23444&b=rounded&bc=%23F9F9F9
    @app.get('/favicon.ico')
    def icon():
        return static_file('favicon.ico', root='static')

    @app.get('/site.webmanifest')
    def manifest():
        return static_file('site.webmanifest', root='static')

    @app.get('/<filename>.png')
    def root_pngs(filename):
        return static_file(f'{filename}.png', root='static')

    @app.get('/<filename>.js')
    def scripts(filename):
        return static_file(f'{filename}.js', root='static')

    @app.get('/login')
    def get_login():
        params = parse_params(request.query.decode(),
                              continue_url=string_param('continue'))
        continue_url = params.get('continue_url')
        if continue_url:
            check_continue_url(continue_url)

        state = generate_id()
        nonce = generate_id()

        # NOTE: The state field works as Login CSRF protection.
        session_handler.set_oidc_data(state, nonce, continue_url or DEFAULT_CONTINUE_URL)

        return template('login',
                        oidc_name=oidc_name,
                        oidc_auth_endpoint=oidc_auth_endpoint,
                        oidc_client_id=oidc_client_id,
                        oidc_redirect_uri=oidc_redirect_uri,
                        state=state,
                        nonce=nonce)

    @app.get('/oidc/callback')
    def get_oidc_callback():

        # NOTE: Generally raise 500 for unexpected issues with the oidc flow, caused either by our
        #       oidc state management or the oidc provider response. All traffic to this endpoint
        #       should be via the oidc flow, and the provider should be working to spec. If not,
        #       something is likely wrong with the flow implementation, so 500 is appropriate.

        # Check state and error before anything else, to make sure nothing's fishy
        params = parse_params(request.query.decode(),
                              state=string_param('state'),
                              error=string_param('error'),
                              error_description=string_param('error_description'))

        # Use 500 rather than "nicer" error if state is missing.
        state = params.get('state')
        if not state:
            log.warning('Received OIDC callback with no state.')
            abort(500)

        oidc_data = session_handler.get_oidc_data()
        if not oidc_data:
            log.warning('Received OIDC callback with no OIDC data cookie.')
            abort(500)

        # If states are present, but don't match, the user may have started two flows in parallel,
        # completing the first when we're expecting the second. Redirect them back to the login
        # screen to be nice.
        if state != oidc_data['state']:
            log.warning('Received OIDC callback with mismatching state.')
            redirect('/login')

        error = params.get('error')
        if error:
            # If they rejected the OIDC scopes, send them back home. Up to them to initiate again.
            # TODO: Should we show them a message explaining this somehow?
            if error == 'access_denied':
                redirect('/')
            # Any other error...
            else:
                error_description = params.get('error_description')
                log_msg = 'Received OIDC callback with error %(error)s'
                log_params = {'error': error}
                if error_description:
                    log_msg += ': %(error_description)s'
                    log_params['error_description'] = error_description
                log.warning(log_msg, log_params)
                abort(500)

        # If there wasn't an error, there should be a code
        params = parse_params(request.query.decode(),
                              code=string_param('code'))
        code = params.get('code')
        # Once again, use 500 rather than a "nicer" error if code is missing
        if not code:
            log.warning('Received OIDC callback with no code.')
            abort(500)

        # Check continue_url before attempting to call the OIDC provider, just in case.
        continue_url = oidc_data['continue_url']
        # NOTE: we check this again, since the oidc_data cookie isn't signed so could be changed
        #       by the user.
        check_continue_url(continue_url)

        r = requests.post(oidc_token_endpoint, timeout=10,
                          auth=(oidc_client_id, oidc_client_secret),
                          data={'grant_type': 'authorization_code',
                                'client_id': oidc_client_id,
                                'redirect_uri': oidc_redirect_uri,
                                'code': code})

        # Only supported response status code.
        if r.status_code == 200:
            pass
        else:
            log.warning('OIDC token endpoint returned unexpected status code %(status_code)s.',
                        {'status_code': r.status_code})
            r.raise_for_status()
            raise NotImplementedError(f'Unsupported status code {r.status_code}.')

        try:
            id_token = r.json()['id_token']
            id_token_jwt = token_decoder.decode_id_token(id_token)
        except (ValueError, KeyError, InvalidTokenError) as e:
            log.warning('OIDC token endpoint returned invalid response: %(error)s', {'error': e})
            abort(500)

        if 'nonce' not in id_token_jwt:
            log.warning('OIDC token endpoint didn\'t return nonce in token.')
            abort(500)

        if id_token_jwt['nonce'] != oidc_data['nonce']:
            log.warning('OIDC token endpoint returned incorrect nonce in token.')
            abort(500)

        session_handler.set_session(id_token)
        session_handler.clear_oidc_data()
        redirect(continue_url)

    # NOTE: The logout endpoint doesn't require CSRF protection, as the session isn't used to
    #       authenticate the user - the session, if it exists, is cleared instead.
    # TODO: Make POST
    @app.get('/logout')
    @session_handler.maybe_session(check_csrf=False, maybe_refresh=False)
    def logout():
        params = parse_params(request.query.decode(),
                              continue_url=string_param('continue'))
        continue_url = params.get('continue_url')
        if continue_url:
            check_continue_url(continue_url)

        if request.session is not None:
            session_handler.clear_session()

        redirect(continue_url or DEFAULT_CONTINUE_URL)

    @app.post('/secrets')
    @session_handler.maybe_session()
    def submit_secret():
        if request.session:
            user_id = request.session['user_id']
        else:
            user_id = None

        params = parse_params(request.forms.decode(),
                              description=string_param('description'),
                              secret=string_param('secret', required=True),
                              ttl=string_param('ttl', required=True, enum=VALID_TTLS.keys()))
        description = params.get('description')
        secret = params['secret']
        ttl = params['ttl']

        if description and len(description) > 100:
            abort(400, 'The description can\'t be longer than 100 characters.')

        if len(secret) > 2000:
            abort(400, 'The secret can\'t be longer than 2,000 characters.')

        now_dt = rfc3339.now()
        secret_id = generate_id()
        secret = Secret(secret_id=secret_id,
                        user_id=user_id,
                        description=description,
                        secret=secret,
                        create_dt=now_dt,
                        expire_dt=now_dt + VALID_TTLS[ttl][0])
        dao.insert_secret(secret)

        response.status = 202
        response.set_header('Location', f'{service_path}/secrets/{secret_id}')
        return template('submit_result',
                        service_address=service_address,
                        user_id=user_id,
                        secret_id=secret_id,
                        ttl=VALID_TTLS[ttl][1])

    @app.get('/secrets')
    @session_handler.require_session()
    def get_secrets():
        now_dt = rfc3339.now()
        user_id = request.session['user_id']

        secrets = dao.find_secrets(user_id, now_dt)

        return template('secrets',
                        service_address=service_address,
                        secrets=secrets)

    @app.get('/secrets/<secret_id>')
    def get_secret(secret_id):
        secret = dao.get_secret(secret_id)

        if secret is None:
            abort(404, 'Oops, that secret can\'t be found.')

        dao.delete_secret(secret_id)

        return template('secret',
                        description=secret.description,
                        secret=secret.secret)

    return app


def run_worker(dao, **kwargs):

    while True:
        now_dt = rfc3339.now()
        deleted_secrets = dao.delete_expired_secrets(now_dt)
        if deleted_secrets:
            log.info('Deleted %(deleted_secrets)s secrets.',
                     {'deleted_secrets': deleted_secrets})
        time.sleep(60)
