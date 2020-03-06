from collections import namedtuple
from datetime import timezone

from utils.fluent import InsertInto, Param, Select, Table, Wildcard


Secret = namedtuple('Secret', ['secret_id',
                               'user_id',
                               'description',
                               'secret',
                               'create_dt',
                               'expire_dt'])
SECRET_TABLE = Table('secret', columns=Secret._fields)


def secret_to_db_format(secret):
    db_format_secret = secret._asdict()

    db_format_secret['secret'] = secret.secret.encode('utf-8')

    return db_format_secret


def secret_from_db_format(db_format_secret):
    # Filter DB fields to only those in our namedtuple, in case the DB has more.
    db_format_secret = {k: v
                        for k, v in db_format_secret.items()
                        if k in Secret._fields}

    db_format_secret['create_dt'] = db_format_secret['create_dt'].replace(tzinfo=timezone.utc)
    db_format_secret['expire_dt'] = db_format_secret['expire_dt'].replace(tzinfo=timezone.utc)

    db_format_secret['secret'] = db_format_secret['secret'].decode('utf-8')

    return Secret(**db_format_secret)


def create_db(conn, db_name):
    sql = (
        f'CREATE DATABASE IF NOT EXISTS `{db_name}` '
        'CHARACTER SET `utf8mb4`'
        ';'
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()

    finally:
        conn.close()


class ShhDao(object):

    def __init__(self, connection_pool):
        self.connection_pool = connection_pool

    def create_secret_table(self):
        sql = (
            'CREATE TABLE IF NOT EXISTS `secret` ('
            '  `secret_id` VARCHAR(100) BINARY NOT NULL, '
            '  `user_id` VARCHAR(100) BINARY NULL, '
            '  `description` VARCHAR(100) NULL, '
            '  `secret` VARBINARY(8000) NOT NULL, '
            '  `create_dt` DATETIME NOT NULL, '
            '  `expire_dt` DATETIME NOT NULL, '
            '  PRIMARY KEY (`secret_id`), '
            '  KEY `idx_secret_expire_dt` (`expire_dt`)'
            ') '
            'CHARACTER SET `utf8mb4`;'
        )

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)

            conn.commit()

        finally:
            conn.close()

    def insert_secret(self, secret):
        sql = InsertInto(SECRET_TABLE).columns(*SECRET_TABLE).to_sql()
        sql_params = secret_to_db_format(secret)

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)

            conn.commit()

        finally:
            conn.close()

    def get_secret(self, secret_id):
        q = Select(Wildcard) \
            .from_table(SECRET_TABLE) \
            .where(SECRET_TABLE['secret_id'] == Param('secret_id'))
        sql = q.to_sql()
        sql_params = {'secret_id': secret_id}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)
                assert cursor.rowcount in (0, 1)
                secret_dict = cursor.fetchone()

        finally:
            conn.close()

        if secret_dict is not None:
            return secret_from_db_format(secret_dict)
        else:
            return None

    def delete_secret(self, secret_id):
        sql = (
            'DELETE FROM `secret` '
            'WHERE `secret_id`=%(secret_id)s'
            ';'
        )

        sql_params = {'secret_id': secret_id}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)
                assert cursor.rowcount in (0, 1)

            conn.commit()

        finally:
            conn.close()

        return bool(cursor.rowcount)

    def delete_expired_secrets(self, now_dt):
        sql = (
            'DELETE FROM `secret` '
            'WHERE `expire_dt`<%(now_dt)s'
            ';'
        )

        sql_params = {'now_dt': now_dt}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)

            conn.commit()

        finally:
            conn.close()

        return cursor.rowcount
