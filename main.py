#!/usr/bin/python3
from gevent import monkey; monkey.patch_all()

import bottle
import click
import logging
import pymysql
import time

from DBUtils.PooledDB import PooledDB
from gevent.pool import Pool
from pymysql import Connection

from shh import construct_app, run_worker
from shh.dao import ShhDao, create_db

from utils import log_exceptions, nice_shutdown, graceful_cleanup
from utils.logging import configure_logging, wsgi_log_middleware

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
@nice_shutdown()
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
@click.option('--port', '-p', default=8080,
              help='Port to serve on. (default=8080)')
@click.option('--json', '-j', default=False, is_flag=True,
              help='Log in json.')
@click.option('--verbose', '-v', default=False, is_flag=True,
              help='Log debug messages.')
@log_exceptions(exit_on_exception=True)
@nice_shutdown()
def server(**options):

    def graceful_shutdown():
        log.info('Starting graceful shutdown.')
        # Sleep for a few seconds to allow for race conditions between sending
        # the SIGTERM and load balancers stopping sending traffic here and
        time.sleep(5)
        # Allow any running requests to complete before exiting.
        # Socket is still open, so assumes no new traffic is reaching us.
        gevent_pool.join()

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

    app = construct_app(shh_dao, **options)
    app = wsgi_log_middleware(app)

    with graceful_cleanup(graceful_shutdown):
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
@nice_shutdown()
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
    shh_dao.create_secret_table()

    run_worker(shh_dao, **options)


main.add_command(init)
main.add_command(server)
main.add_command(worker)


if __name__ == '__main__':
    main(auto_envvar_prefix='SHH_OPT')
