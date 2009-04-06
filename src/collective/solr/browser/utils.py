from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig
from urllib import urlencode
from copy import deepcopy


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
    params = request.copy()   # request needs to be a dict, i.e. request.form
    params['facet.field'] = list(facetParameters(context, request))
    fq = params.get('fq', None)
    if isinstance(fq, basestring):
        params['fq'] = [fq]
    for field, values in fields.items():
        counts = []
        second = lambda a, b: cmp(b[1], a[1])
        for name, count in sorted(values.items(), cmp=second):
            p = deepcopy(params)
            fqs = p.setdefault('fq', []).append('%s:%s' % (field, name))
            if field in p.get('facet.field', []):
                p['facet.field'].remove(field)
            counts.append(dict(name=name, count=count,
                query=urlencode(p, doseq=True)))
        if counts:
            info.append(dict(title=field, counts=counts))
    byTitle = lambda a, b: cmp(a['title'], b['title'])
    return sorted(info, cmp=byTitle)
