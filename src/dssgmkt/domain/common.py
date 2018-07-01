

def get_field_value(object, path):
    if isinstance(path, str):
        return getattr(object, path)
    elif not path:
        return object
    else:
        first, *rest = path
        return get_field_value(getattr(object, first), rest)

def validate_consistent_keys(object, error_message='Detected primary key inconsistency', *items):
    for (field_path, field_value) in items:
        if not get_field_value(object, field_path) == field_value:
            raise KeyError(error_message)
    return True
