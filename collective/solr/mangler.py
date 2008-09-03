from DateTime import DateTime
from collective.solr.search import quote


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
    elif isinstance(value, basestring):
        value = quote(value)
    elif isinstance(value, bool):
        value = str(value).lower()
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
            path = keywords['parentPaths'] = value
            del keywords[key]
            if args.has_key('depth'):
                depth = len(path.split('/')) + int(args['depth'])
                keywords['physicalDepth'] = '"[* TO %d]"' % depth
                del args['depth']
        elif key == 'effectiveRange':
            value = convert(value)
            del keywords[key]
            keywords['effective'] = '"[* TO %s]"' % value
            keywords['expires'] = '"[%s TO *]"' % value
        elif args.has_key('range'):
            if not isinstance(value, (list, tuple)):
                value = [ value ]
            payload = map(convert, value)
            keywords[key] = ranges[args['range']] % tuple(payload)
            del args['range']
        elif args.has_key('operator'):
            if isinstance(value, (list, tuple)) and len(value) > 1:
                sep = ' %s ' % args['operator'].upper()
                value = sep.join(map(str, map(convert, value)))
                keywords[key] = '"(%s)"' % value
            del args['operator']
        else:
            keywords[key] = convert(value)
        assert not args, 'unsupported usage: %r' % args


def extractQueryParameters(args):
    """ extract parameters related to sorting and limiting search results
        from a given set of arguments """
    def get(name):
        for prefix in 'sort_', 'sort-':
            value = args.get('%s%s' % (prefix, name), None)
            if value is not None:
                return value
        return None
    params = {}
    index = get('on')
    if index:
        reverse = get('order') or ''
        reverse = reverse.lower() in ('reverse', 'descending')
        order = reverse and 'desc' or 'asc'
        params['sort'] = '%s %s' % (index, order)
    limit = get('limit')
    if limit:
        params['rows'] = int(limit)
    return params

