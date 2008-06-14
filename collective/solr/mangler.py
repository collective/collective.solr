from DateTime import DateTime


usages = {
    'range': {
        'min': '"[%s TO *]"',
        'max': '"[* TO %s]"',
        'min:max': '"[%s TO %s]"',
    },
}


def convert(value):
    """ convert values, which need a special format, i.e. dates """
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (v.year(),
            v.month(), v.day(), v.hour(), v.minute(), v.second())
    return value


def mangleQuery(keywords):
    """ translate / mangle query parameters to replace zope specifics
        with equivalent constructs for solr """
    if keywords.has_key('path'):
        path = value = keywords['path']
        if isinstance(value, dict):
            path = value['query']
            if value.has_key('depth'):
                depth = len(path.split('/')) + int(value['depth'])
                keywords['physicalDepth'] = '"[* TO %d]"' % depth
        keywords['parentPaths'] = path
        del keywords['path']
    for key, value in keywords.items():
        if key.endswith('_usage'):
            category, spec = value.split(':', 1)
            mapping = usages.get(category, None)
            if mapping is not None:
                name = key[:-6]
                payload = map(convert, keywords[name])
                keywords[name] = mapping[spec] % tuple(payload)
                del keywords[key]
            else:
                raise AttributeError, 'unsupported usage: %r' % key

