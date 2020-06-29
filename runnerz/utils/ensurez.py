

def ensure_type(value, types, message=None):
    if not isinstance(value, types):
        message = message or 'value: %s must be types: %s' % (value, types)
        raise TypeError(message)