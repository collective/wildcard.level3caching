_custom_invalidators = {}


def addCustomInvalidator(portal_type, func):
    if portal_type not in _custom_invalidators:
        _custom_invalidators[portal_type] = []
    _custom_invalidators[portal_type].append(func)


def runCustomInvalidators(object, parent, site_path):
    if not hasattr(object, 'portal_type'):
        return []
    portal_type = object.portal_type
    if portal_type not in _custom_invalidators:
        return []
    paths = []
    for func in _custom_invalidators[portal_type]:
        paths.extend(func(object, parent, site_path))
    return paths
