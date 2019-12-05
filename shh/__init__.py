import logging
import rfc3339
import secrets
import time

from bottle import Bottle, request, response, static_file, abort, template
from datetime import timedelta

from .dao import Secret


log = logging.getLogger(__name__)

VALID_TTLS = {
    '1h': (timedelta(hours=1), '1 hour'),
    '30m': (timedelta(minutes=30), '30 minutes'),
    '15m': (timedelta(minutes=15), '15 minutes'),
    '5m': (timedelta(minutes=5), '5 minutes'),
}


def generate_id():
    return secrets.token_urlsafe(8)


def custom_default_error_hander(res):
    if res.status_code == 404:
        body = template('error_404', error=res)
    else:
        body = template('error', error=res)

    return body


def construct_app(dao, **kwargs):
    app = Bottle()
    app.default_error_handler = custom_default_error_hander

    @app.get('/status')
    def status():
        return 'OK'

    @app.get('/')
    def index():
        return static_file('index.html', root='static')

    @app.get('/main.css')
    def css():
        return static_file('main.css', root='static')

    @app.post('/secrets')
    def submit_secret():
        secret = request.forms.secret
        ttl = request.forms.ttl

        if not (secret and ttl):
            abort(400, 'Please specify both a secret and a ttl.')

        if ttl not in VALID_TTLS:
            abort(400, 'Please specify a ttl of 5m, 15m, 30m, or 1h.')

        if len(secret) > 2000:
            abort(400, 'The secret can\'t be longer than 2,000 characters.')

        now_dt = rfc3339.now()
        secret_id = generate_id()
        secret = Secret(secret_id=secret_id,
                        create_dt=now_dt,
                        expire_dt=now_dt + VALID_TTLS[ttl][0],
                        secret=secret)
        dao.insert_secret(secret)

        response.status = 202
        response.set_header('Location', f'/secrets/{secret_id}')
        return template('submit_result',
                        secret_id=secret_id,
                        ttl=VALID_TTLS[ttl][1])

    @app.get('/secrets/<secret_id>')
    def get_secret(secret_id):
        secret = dao.get_secret(secret_id)

        if secret is None:
            abort(404, 'Oops, that secret can\'t be found.')

        dao.delete_secret(secret_id)

        return template('secret', secret=secret.secret)

    return app


def run_worker(dao, **kwargs):

    while True:
        now_dt = rfc3339.now()
        deleted_secrets = dao.delete_expired_secrets(now_dt)
        if deleted_secrets:
            log.info('Deleted %(deleted_secrets)s secrets.',
                     {'deleted_secrets': deleted_secrets})
        time.sleep(60)
