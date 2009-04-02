from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig
from urllib import urlencode


def facetParameters(context, request):
    """ determine facet fields to be queried for """
    marker = []
    fields = request.get('facet.field', marker)
    if isinstance(fields, basestring):
        fields = [fields]
    if fields is marker:
        fields = getattr(context, 'facet_fields', marker)
    if fields is marker:
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            fields = config.facets
    return fields


def convertFacets(fields, context=None, request={}):
    """ convert facet info to a form easy to process in templates """
    info = []
    params = dict(request.items())  # request is dict-like, but has no `copy`
    params['facet.field'] = list(facetParameters(context, request))
    for field, values in fields.items():
        counts = []
        second = lambda a, b: cmp(b[1], a[1])
        for name, count in sorted(values.items(), cmp=second):
            p = params.copy()
            p['fq'] = '%s:%s' % (field, name)
            if field in p.get('facet.field', []):
                p['facet.field'] = list(p['facet.field'])   # make a copy first
                p['facet.field'].remove(field)
            counts.append(dict(name=name, count=count,
                query=urlencode(p, doseq=True)))
        info.append(dict(title=field, counts=counts))
    byTitle = lambda a, b: cmp(a['title'], b['title'])
    return sorted(info, cmp=byTitle)
