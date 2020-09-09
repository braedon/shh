#!/usr/bin/python3
from gevent import monkey; monkey.patch_all()

import bottle
import click
import gevent
import logging
import pymysql
import shh
import sys
import time

from DBUtils.PooledDB import PooledDB
from gevent.pool import Pool
from pymysql import Connection

from utils import log_exceptions, nice_shutdown
from utils.logging import configure_logging, wsgi_log_middleware

from shh import construct_app, run_worker
from shh.dao import ShhDao, create_db
from shh.session import TokenDecoder

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help']
}

log = logging.getLogger(__name__)

# Use an unbounded pool to track gevent greenlets so we can
# wait for them to finish on shutdown.
gevent_pool = Pool()


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


@click.command()
@click.option('--mysql-host', default='localhost',
              help='MySQL server host. (default=localhost)')
@click.option('--mysql-port', default=3306,
              help='MySQL server port. (default=3306)')
@click.option('--mysql-user', default='shh',
              help='MySQL server user. (default=shh)')
@click.option('--mysql-password', default='',
              help='MySQL server password. (default=None)')
@click.option('--mysql-database', default='shh',
              help='MySQL server database. (default=shh)')
@click.option('--json', '-j', default=False, is_flag=True,
              help='Log in json.')
@click.option('--verbose', '-v', default=False, is_flag=True,
              help='Log debug messages.')
@log_exceptions(exit_on_exception=True)
def init(**options):

    configure_logging(json=options['json'], verbose=options['verbose'])

    connection = Connection(host=options['mysql_host'],
                            port=options['mysql_port'],
                            user=options['mysql_user'],
                            password=options['mysql_password'],
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)

    create_db(connection, options['mysql_database'])

    connection_pool = PooledDB(creator=pymysql,
                               mincached=1,
                               maxcached=10,
                               # max connections currently in use - doesn't
                               # include cached connections
                               maxconnections=50,
                               blocking=True,
                               host=options['mysql_host'],
                               port=options['mysql_port'],
                               user=options['mysql_user'],
                               password=options['mysql_password'],
                               database=options['mysql_database'],
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
    shh_dao = ShhDao(connection_pool)

    shh_dao.create_secret_table()


@click.command()
@click.option('--service-protocol', type=click.Choice(('https', 'http')),
              default='https',
              help='The protocol for the public service. (default=https)')
@click.option('--service-hostname', default='localhost',
              help='The hostname for the public service. (default=localhost)')
@click.option('--service-port', default='',
              help='The port for the public service, if non standard.')
@click.option('--service-path', default='',
              help='The path prefix for the public service, if any.'
                   'Should start with a "/", but not end with one.')
@click.option('--oidc-name', default='Alias',
              help='Name of the OpenID Connect provider to use for login.')
@click.option('--oidc-iss', required=True,
              help='Issuer string of the OpenID Connect provider.')
@click.option('--oidc-about-url', required=True,
              help='URL of an about page for the OpenID Connect provider.')
@click.option('--oidc-auth-endpoint', required=True,
              help='URL of the authenticaiton endpoint of the OpenID Connect provider.')
@click.option('--oidc-token-endpoint', required=True,
              help='URL of the token endpoint of the OpenID Connect provider.')
@click.option('--oidc-public-key-file', default='id_rsa.pub', type=click.File(mode='rb'),
              help='Path to RSA256 public key file for the OpenID Connect provider. '
                   '(default=id_rsa.pub)')
@click.option('--oidc-client-id', required=True,
              help='Client ID issued by the OpenID Connect provider.')
@click.option('--oidc-client-secret', required=True,
              help='Client secret issued by the OpenID Connect provider.')
@click.option('--mysql-host', default='localhost',
              help='MySQL server host. (default=localhost)')
@click.option('--mysql-port', default=3306,
              help='MySQL server port. (default=3306)')
@click.option('--mysql-user', default='shh',
              help='MySQL server user. (default=shh)')
@click.option('--mysql-password', default='',
              help='MySQL server password. (default=None)')
@click.option('--mysql-database', default='shh',
              help='MySQL server database. (default=shh)')
@click.option('--testing-mode', default=False, is_flag=True,
              help='Relax security to simplify testing, e.g. allow http cookies')
@click.option('--port', '-p', default=8080,
              help='Port to serve on. (default=8080)')
@click.option('--shutdown-sleep', default=10,
              help='How many seconds to sleep during graceful shutdown. (default=10)')
@click.option('--shutdown-wait', default=10,
              help='How many seconds to wait for active connections to close during graceful '
                   'shutdown (after sleeping). (default=10)')
@click.option('--json', '-j', default=False, is_flag=True,
              help='Log in json.')
@click.option('--verbose', '-v', default=False, is_flag=True,
              help='Log debug messages.')
@log_exceptions(exit_on_exception=True)
def server(**options):

    def shutdown():
        shh.SERVER_READY = False

        def wait():
            # Sleep for a few seconds to allow for race conditions between sending
            # the SIGTERM and load balancers stopping sending traffic here.
            log.info('Shutdown: Sleeping %(sleep_s)s seconds.',
                     {'sleep_s': options['shutdown_sleep']})
            time.sleep(options['shutdown_sleep'])

            log.info('Shutdown: Waiting up to %(wait_s)s seconds for connections to close.',
                     {'wait_s': options['shutdown_sleep']})
            gevent_pool.join(timeout=options['shutdown_wait'])

            log.info('Shutdown: Exiting.')
            sys.exit()

        # Run in greenlet, as we can't block in a signal hander.
        gevent.spawn(wait)

    configure_logging(json=options['json'], verbose=options['verbose'])

    connection_pool = PooledDB(creator=pymysql,
                               mincached=1,
                               maxcached=10,
                               # max connections currently in use - doesn't
                               # include cached connections
                               maxconnections=50,
                               blocking=True,
                               host=options['mysql_host'],
                               port=options['mysql_port'],
                               user=options['mysql_user'],
                               password=options['mysql_password'],
                               database=options['mysql_database'],
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
    shh_dao = ShhDao(connection_pool)

    with options['oidc_public_key_file'] as file:
        public_key = file.read()
    token_decoder = TokenDecoder(public_key, options['oidc_iss'], options['oidc_client_id'])

    app = construct_app(shh_dao, token_decoder, **options)
    app = wsgi_log_middleware(app)

    with nice_shutdown(shutdown):
        bottle.run(app,
                   host='0.0.0.0', port=options['port'],
                   server='gevent', spawn=gevent_pool,
                   # Disable default request logging - we're using middleware
                   quiet=True, error_log=None)


@click.command()
@click.option('--mysql-host', default='localhost',
              help='MySQL server host. (default=localhost)')
@click.option('--mysql-port', default=3306,
              help='MySQL server port. (default=3306)')
@click.option('--mysql-user', default='shh',
              help='MySQL server user. (default=shh)')
@click.option('--mysql-password', default='',
              help='MySQL server password. (default=None)')
@click.option('--mysql-database', default='shh',
              help='MySQL server database. (default=shh)')
@click.option('--json', '-j', default=False, is_flag=True,
              help='Log in json.')
@click.option('--verbose', '-v', default=False, is_flag=True,
              help='Log debug messages.')
@log_exceptions(exit_on_exception=True)
def worker(**options):

    configure_logging(json=options['json'], verbose=options['verbose'])

    connection_pool = PooledDB(creator=pymysql,
                               mincached=1,
                               maxcached=1,
                               # max connections currently in use - doesn't
                               # include cached connections
                               maxconnections=1,
                               blocking=True,
                               host=options['mysql_host'],
                               port=options['mysql_port'],
                               user=options['mysql_user'],
                               password=options['mysql_password'],
                               database=options['mysql_database'],
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
    shh_dao = ShhDao(connection_pool)

    with nice_shutdown():
        run_worker(shh_dao, **options)


main.add_command(init)
main.add_command(server)
main.add_command(worker)


if __name__ == '__main__':
    main(auto_envvar_prefix='SHH_OPT')
