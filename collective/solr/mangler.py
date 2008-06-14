from DateTime import DateTime


ranges = {
    'min': '"[%s TO *]"',
    'max': '"[* TO %s]"',
    'min:max': '"[%s TO %s]"',
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
    extras = {}
    for key, value in keywords.items():
        if key.endswith('_usage'):          # convert old-style parameters
            category, spec = value.split(':', 1)
            extras[key[:-6]] = { category: spec }
            del keywords[key]
        elif isinstance(value, dict):       # unify parameters
            keywords[key] = value['query']
            del value['query']
            extras[key] = value
    for key, value in keywords.items():
        args = extras.get(key, {})
        if key == 'path':
            path = keywords['parentPaths'] = keywords[key]
            del keywords[key]
            if args.has_key('depth'):
                depth = len(path.split('/')) + int(args['depth'])
                keywords['physicalDepth'] = '"[* TO %d]"' % depth
                del args['depth']
        elif args.has_key('range'):
            payload = map(convert, value)
            keywords[key] = ranges[args['range']] % tuple(payload)
            del args['range']
        assert not args, 'unsupported usage: %r' % args

