import secrets

from bottle import template

ID_LENGTH = 16


# TODO: Should we generate a GUID v4 (fully random) instead?
def generate_id():
    return secrets.token_urlsafe(ID_LENGTH)


def html_default_error_hander(res):
    if res.status_code == 404:
        body = template('error_404', error=res)
    else:
        body = template('error', error=res)

    return body
