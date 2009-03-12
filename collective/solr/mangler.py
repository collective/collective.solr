from DateTime import DateTime
from collective.solr.search import quote


ranges = {
    'min': '"[%s TO *]"',
    'max': '"[* TO %s]"',
    'min:max': '"[%s TO %s]"',
}

sort_aliases = {
    'sortable_title': 'Title',
}

query_args = ('range',
              'operator',
              'depth',
)


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
            extras[key[:-6]] = {category: spec}
            del keywords[key]
        elif isinstance(value, dict):       # unify dict parameters
            keywords[key] = value['query']
            del value['query']
            extras[key] = value
        elif hasattr(value, 'query'):     # unify object parameters
            keywords[key] = value.query
            extra = dict()
            for arg in query_args:
                arg_val = getattr(value, arg, None)
                if arg_val is not None:
                    extra[arg] = arg_val
            extras[key] = extra

    for key, value in keywords.items():
        args = extras.get(key, {})
        if key == 'path':
            path = keywords['parentPaths'] = value
            del keywords[key]
            if 'depth' in args:
                depth = len(path.split('/')) + int(args['depth'])
                keywords['physicalDepth'] = '"[* TO %d]"' % depth
                del args['depth']
        elif key == 'effectiveRange':
            value = convert(value)
            del keywords[key]
            keywords['effective'] = '"[* TO %s]"' % value
            keywords['expires'] = '"[%s TO *]"' % value
        elif 'range' in args:
            if not isinstance(value, (list, tuple)):
                value = [value]
            payload = map(convert, value)
            keywords[key] = ranges[args['range']] % tuple(payload)
            del args['range']
        elif 'operator' in args:
            if isinstance(value, (list, tuple)) and len(value) > 1:
                sep = ' %s ' % args['operator'].upper()
                value = sep.join(map(str, map(convert, value)))
                keywords[key] = '"(%s)"' % value
            del args['operator']
        elif isinstance(value, basestring) and value.endswith('*'):
            keywords[key] = '"%s"' % value.lower()  # quote wildcard searches
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
    for key, value in args.items():
        if key == 'facet' or key.startswith('facet.'):
            params[key] = value
        elif key.startswith('facet_'):
            params[key.replace('_', '.', 1)] = value
    return params


def cleanupQueryParameters(args, schema):
    """ validate and possibly clean up the given query parameters using
        the given solr schema """
    sort = args.get('sort', None)
    if sort is not None:
        field, order = sort.split(' ', 1)
        if not field in schema:
            field = sort_aliases.get(field, None)
        fld = schema.get(field, None)
        if fld is not None and fld.indexed:
            args['sort'] = '%s %s' % (field, order)
        else:
            del args['sort']
    return args
