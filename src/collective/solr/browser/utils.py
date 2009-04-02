from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig


def facetParameters(context, request):
    """ determine facet fields to be queried for """
    marker = []
    fields = request.get('facet.field', marker)
    if fields is marker:
        fields = getattr(context, 'facet_fields', marker)
    if fields is marker:
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            fields = config.facets
    return fields


def convertFacets(fields):
    """ convert facet info to a form easy to process in templates """
    info = []
    for field, values in fields.items():
        counts = []
        second = lambda a, b: cmp(b[1], a[1])
        for name, count in sorted(values.items(), cmp=second):
            counts.append(dict(name=name, count=count))
        info.append(dict(title=field, counts=counts))
    byTitle = lambda a, b: cmp(a['title'], b['title'])
    return sorted(info, cmp=byTitle)
