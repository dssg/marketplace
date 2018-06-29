

def get_field_value(object, path):
    if isinstance(path, str):
        return getattr(object, path)
    elif not path:
        return object
    else:
        first, *rest = path
        return get_field_value(getattr(object, first), rest)

def validate_consistent_keys(object, *items):
    for (field_path, field_value) in items:
        print(get_field_value(object, field_path))
        if not get_field_value(object, field_path) == field_value:
            raise KeyError('Detected primary key inconsistency')
    return True
