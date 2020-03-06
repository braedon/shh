import re
import rfc3339
from bottle import HTTPError


class ParamParseError(HTTPError):
    pass


class InvalidParamError(ParamParseError):
    default_status = 400

    def __init__(self, param, value, message=None, **options):
        self.param = param
        self.value = value
        body = 'Invalid {}'.format(param.replace('_', ' '))
        if message:
            body += ': {}'.format(message)
        if body[-1] != '.':
            body += '.'
        super(InvalidParamError, self).__init__(body=body, **options)


class RequiredParamError(ParamParseError):
    default_status = 400

    def __init__(self, param, message=None, **options):
        self.param = param
        body = 'Missing {}'.format(param.replace('_', ' '))
        if message:
            body += ': {}'.format(message)
        if body[-1] != '.':
            body += '.'
        super(RequiredParamError, self).__init__(body=body, **options)


class UnsetType(object):
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance


Unset = UnsetType()


def param_parser(*keys, default=Unset, empty=Unset, required=False):
    """
    Decorator that coverts a parsing function into a full param parser.

    The parsing functions take two strings - the param key and value - and return the parsed
    (and validated, if applicable) value. InvalidParamError should be raised if parsing(/validation)
    fails.

    The returned param parser function takes a dict of params, and attempts to find and parse a
    value for one of the `keys` listed. Each key is tried in turn, with the first key present in the
    params dict used (regardless of its value). If none of the keys are found `default` is returned.

    If a key is found, and its value is an empty string, `empty` is returned. If its value is not
    empty the parser function is called on the key and value, and the resulting value is returned.

    If the value is found to be `Unset` (for any reason) and the param is `required`,
    RequiredParamError is raised. If it is `Unset` because none of the `keys` are found, the first
    key as used as the required param.
    """

    def decorator(parse_func):

        def wrapper(params):
            for k in keys:
                if k in params:
                    v = params[k]

                    if v == '':
                        if required and empty is Unset:
                            raise RequiredParamError(k)
                        return empty

                    else:
                        parsed_value = parse_func(k, v)
                        if required and parsed_value is Unset:
                            raise RequiredParamError(k)
                        return parsed_value

            if required and keys and default is Unset:
                raise RequiredParamError(keys[0])
            return default

        return wrapper

    return decorator


def string_param(*keys, multi=False, enum=None,
                 default=Unset, empty=Unset, required=False):

    @param_parser(*keys, default=default, empty=empty, required=required)
    def parse(k, v):
        if multi:
            v = v.split(',')
            v = tuple(v)
            if enum is not None and any(i not in enum for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated values from {}'.format(','.join(enum)))

        else:
            if enum is not None and v not in enum:
                raise InvalidParamError(k, v, 'Must be a value from {}'.format(','.join(enum)))

        return v

    return parse


def boolean_param(*keys, enum=None,
                  default=Unset, empty=Unset, required=False):

    @param_parser(*keys, default=default, empty=empty, required=required)
    def parse(k, v):
        if isinstance(v, (str,)) and v.lower() in ('true', 't', 'yes', 'y'):
            return True

        if isinstance(v, (str,)) and v.lower() in ('false', 'f', 'no', 'n'):
            return False

        # Allows "boolean" params to also have extra options beyond True and False.
        if enum is not None:
            if v.lower() not in enum:
                raise InvalidParamError(k, v, 'Must be true, false, or a value from {}'.format(','.join(enum)))

            return v

        raise InvalidParamError(k, v, 'Must be "true" or "false"')

    return parse


def integer_param(*keys, multi=False, positive=False, enum=None,
                  default=Unset, empty=Unset, required=False):

    @param_parser(*keys, default=default, empty=empty, required=required)
    def parse(k, v):
        if multi:
            v = v.split(',')
            if not all(i.isdecimal() for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated integers')
            v = tuple(int(i) for i in v)
            if positive and any(i < 0 for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated positive integers')
            if enum is not None and any(i not in enum for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated values from {}'.format(','.join(enum)))

        else:
            if not v.isdecimal():
                raise InvalidParamError(k, v, 'Must be an integer')
            v = int(v)
            if positive and v < 0:
                raise InvalidParamError(k, v, 'Must be positive')
            if enum is not None and v not in enum:
                raise InvalidParamError(k, v, 'Must be a value from {}'.format(','.join(enum)))

        return v

    return parse


def float_param(*keys, multi=False, positive=False, enum=None,
                default=Unset, empty=Unset, required=False):

    @param_parser(*keys, default=default, empty=empty, required=required)
    def parse(k, v):
        def is_float(val):
            return re.match(r'^\d+(\.\d+)?$', val) is not None

        if multi:
            v = v.split(',')
            if not all(is_float(i) for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated decimals')
            v = tuple(float(i) for i in v)
            if positive and any(i < 0 for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated positive decimals')
            if enum is not None and any(i not in enum for i in v):
                raise InvalidParamError(k, v, 'Must be comma separated values from {}'.format(','.join(enum)))

        else:
            if not is_float(v):
                raise InvalidParamError(k, v, 'Must be a decimal')
            v = float(v)
            if positive and v < 0:
                raise InvalidParamError(k, v, 'Must be positive')
            if enum is not None and v not in enum:
                raise InvalidParamError(k, v, 'Must be a value from {}'.format(','.join(enum)))

        return v

    return parse


def datetime_param(*keys,
                   default=Unset, empty=Unset, required=False):

    @param_parser(*keys, default=default, empty=empty, required=required)
    def parse(k, v):
        try:
            # Attempt to convert valid date as datetime
            rfc3339.parse_date(v)
            v = v + 'T00:00:00Z'
        except ValueError:
            pass

        try:
            dt = rfc3339.parse_datetime(v)
            return dt
        except ValueError:
            raise InvalidParamError(k, v, 'Must be a valid datetime')

    return parse


def parse_params(params, **parsers):
    """
    Parse a number of params out of a params dict, returning the parsed params as dict.

    The `params` string -> string dict usually holds HTTP query params, or form params.

    Each of the `parsers` keyword parameters maps a key in the returned dict to a param parser
    function. Each parser is run on the `params` in turn, and the produced value (if not `Unset`)
    added to the returned dict under the parser's keyword. Note that the parser keywords may be
    unrelated to the param keys their parser targets.
    """
    parsed_params = {}

    for out_key, parser in parsers.items():
        v = parser(params)
        if v is not Unset:
            parsed_params[out_key] = v

    return parsed_params


def parse_param(params, parser):
    """
    Parse a single param out of a params dict.

    The `params` string -> string dictionary usually holds HTTP query params, or form params.

    The `parser` is a param parser function that is run on the `params`, and the produced value
    returned (or `None` if `Unset` is produced).
    """
    v = parser(params)
    if v is not Unset:
        return v
    else:
        return None
