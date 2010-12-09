from zope.component import queryUtility
from AccessControl import getSecurityManager
from DateTime import DateTime

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.queryparser import quote
from collective.solr.utils import isSimpleTerm


ranges = {
    'min': '[%s TO *]',
    'max': '[* TO %s]',
    'min:max': '[%s TO %s]',
}

sort_aliases = {
    'sortable_title': 'Title',
}

query_args = ('range',
              'operator',
              'depth',
)

ignored = 'use_solr', '-C'


def convert(value):
    """ convert values, which need a special format, i.e. dates """
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (v.year(),
            v.month(), v.day(), v.hour(), v.minute(), v.second())
    elif isinstance(value, basestring):
        value = quote(value)
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
        elif hasattr(value, 'query'):       # unify object parameters
            keywords[key] = value.query
            extra = dict()
            for arg in query_args:
                arg_val = getattr(value, arg, None)
                if arg_val is not None:
                    extra[arg] = arg_val
            extras[key] = extra
        elif key in ignored:
            del keywords[key]
    config = queryUtility(ISolrConnectionConfig)
    for key, value in keywords.items():
        args = extras.get(key, {})
        if key == 'SearchableText':
            if isSimpleTerm(value):         # use prefix/wildcard search
                value = '(%s* OR %s)' % (value.lower(), value)
        if key == 'path':       # must not be `elif` to handle wildcards
            path = keywords['parentPaths'] = value
            del keywords[key]
            if 'depth' in args:
                depth = int(args['depth'])
                if depth >= 0:
                    if not isinstance(value, (list, tuple)):
                        path = [path]
                    tmpl = '(+physicalDepth:[%d TO %d] AND +parentPaths:%s)'
                    params = keywords['parentPaths'] = set()
                    for p in path:
                        base = len(p.split('/'))
                        params.add(tmpl % (base, base + depth, p))
                del args['depth']
        elif key == 'effectiveRange':
            if isinstance(value, DateTime):
                steps = config.effective_steps
                if steps > 1:
                    value = DateTime(value.timeTime() // steps * steps)
            value = convert(value)
            del keywords[key]
            keywords['effective'] = '[* TO %s]' % value
            keywords['expires'] = '[%s TO *]' % value
        elif key == 'show_inactive':
            del keywords[key]           # marker for `effectiveRange`
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
                keywords[key] = '(%s)' % value
            del args['operator']
        elif key == 'allowedRolesAndUsers' and config.exclude_user:
            token = 'user:' + getSecurityManager().getUser().getId()
            if token in value:
                value.remove(token)
        elif isinstance(value, basestring) and value.endswith('*'):
            keywords[key] = '%s' % value.lower()
        else:
            keywords[key] = convert(value)
        assert not args, 'unsupported usage: %r' % args


def extractQueryParameters(args):
    """ extract parameters related to sorting and limiting search results
        from a given set of arguments, also removing them """
    def get(name):
        for prefix in 'sort_', 'sort-':
            key = '%s%s' % (prefix, name)
            value = args.get(key, None)
            if value is not None:
                del args[key]
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
        if key in ('fq', 'fl', 'facet'):
            params[key] = value
            del args[key]
        elif key.startswith('facet.') or key.startswith('facet_'):
            name = lambda facet: facet.split(':', 1)[0]
            if isinstance(value, list):
                value = map(name, value)
            elif isinstance(value, tuple):
                value = tuple(map(name, value))
            else:
                value = name(value)
            params[key.replace('_', '.', 1)] = value
            del args[key]
        elif key == 'b_start':
            params['start'] = int(value)
            del args[key]
        elif key == 'b_size':
            params['rows'] = int(value)
            del args[key]
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
    if 'facet.field' in args and not 'facet' in args:
        args['facet'] = 'true'
    return args


def optimizeQueryParameters(query, params):
    """ optimize query parameters by using filter queries for
        configured indexes """
    config = queryUtility(ISolrConnectionConfig)
    fq = []
    if config is not None:
        for idxs in config.filter_queries:
            idxs = set(idxs.split(' '))
            if idxs.issubset(query.keys()):
                fq.append(' '.join([query.pop(idx) for idx in idxs]))
    if 'fq' in params:
        if isinstance(params['fq'], list):
            params['fq'].extend(fq)
        else:
            params['fq'] = [params['fq']] + fq
    elif fq:
        params['fq'] = fq
    if not query:
        query['*'] = '*:*'      # catch all if no regular query is left...
