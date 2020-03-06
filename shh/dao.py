from collections import namedtuple
from datetime import timezone


Secret = namedtuple('Secret', ['secret_id',
                               'description',
                               'secret',
                               'create_dt',
                               'expire_dt'])


def build_insert_stmt(table, columns):
    columns_stmt = ', '.join(f'`{c}`' for c in columns)
    values_stmt = ', '.join(f'%({c})s' for c in columns)
    return f'INSERT INTO `{table}` ({columns_stmt}) VALUES ({values_stmt});'


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
        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                sql = (
                    'CREATE TABLE IF NOT EXISTS `secret` ('
                    '   `secret_id` VARCHAR(100) BINARY NOT NULL,'
                    '   `description` VARCHAR(100),'
                    '   `secret` VARBINARY(8000) NOT NULL,'
                    '   `create_dt` DATETIME NOT NULL,'
                    '   `expire_dt` DATETIME NOT NULL,'
                    '   PRIMARY KEY (`secret_id`),'
                    '   KEY `idx_secret_expire_dt` (`expire_dt`)'
                    ') '
                    'CHARACTER SET `utf8mb4`;'
                )
                cursor.execute(sql)

            conn.commit()

        finally:
            conn.close()

    def insert_secret(self, secret):
        secret_dict = secret_to_db_format(secret)
        sql = build_insert_stmt('secret', secret._fields)

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, secret_dict)

            conn.commit()

        finally:
            conn.close()

    def get_secret(self, secret_id):
        sql = 'SELECT * FROM `secret`'
        sql += ' WHERE `secret_id`=%(secret_id)s'
        sql += ';'

        sql_params = {'secret_id': secret_id}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)
                secret_dicts = cursor.fetchall()
                assert len(secret_dicts) in (0, 1)

        finally:
            conn.close()

        if secret_dicts:
            return secret_from_db_format(secret_dicts[0])
        else:
            return None

    def delete_secret(self, secret_id):
        sql = 'DELETE FROM `secret`'
        sql += ' WHERE `secret_id`=%(secret_id)s'
        sql += ';'

        sql_params = {'secret_id': secret_id}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)
                assert cursor.rowcount == 1

            conn.commit()

        finally:
            conn.close()

    def delete_expired_secrets(self, now_dt):
        sql = 'DELETE FROM `secret`'
        sql += ' WHERE `expire_dt`<%(now_dt)s'
        sql += ';'

        sql_params = {'now_dt': now_dt}

        conn = self.connection_pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, sql_params)

            conn.commit()

        finally:
            conn.close()

        return cursor.rowcount
