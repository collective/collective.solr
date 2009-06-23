from zope.interface import implements
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager


class SolrIndexes(object):
    """ vocabulary provider yielding all available solr indexes """
    implements(IVocabularyFactory)

    def __call__(self, context):
        items = []
        manager = queryUtility(ISolrConnectionManager)
        if manager is not None:
            schema = manager.getSchema()
            if schema is not None:
                for name, info in sorted(schema.items()):
                    if 'indexed' in info and info.get('indexed', False):
                        items.append(name)
        if not items:
            config = queryUtility(ISolrConnectionConfig)
            if config is not None:
                items = config.filter_queries
        return SimpleVocabulary([SimpleTerm(item) for item in items])
