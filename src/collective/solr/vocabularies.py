import six
from collective.solr import SolrMessageFactory
from collective.solr.interfaces import (
    IFacetTitleVocabularyFactory,
    ISolrConnectionManager,
)
from plone.registry.interfaces import IRegistry
from zope.component import getUtility, queryUtility
from zope.interface import implementer
from zope.schema.interfaces import IBaseVocabulary, IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary


@implementer(IVocabularyFactory)
class SolrIndexes(object):
    """vocabulary provider yielding all available solr indexes"""

    def __call__(self, context):
        items = []
        manager = queryUtility(ISolrConnectionManager)
        if manager is not None:
            schema = manager.getSchema()
            if schema is not None:
                for name, info in sorted(schema.items()):
                    if "indexed" in info and info.get("indexed", False):
                        items.append(name)
        if not items:
            registry = getUtility(IRegistry)
            items = registry["collective.solr.filter_queries"]
        return SimpleVocabulary([SimpleTerm(item) for item in items])


@implementer(IBaseVocabulary)
class I18NFacetTitles(object):
    """Vocabulary that wraps any term into message ids in the solr translation
    domain. This is generally the default behaviour for facet titles.
    """

    def __contains__(self, term):
        return True

    def getTerm(self, term):
        value = term
        title = SolrMessageFactory(term)
        if isinstance(term, six.text_type):
            # Terms must be byte strings
            term = term.encode("utf8")
        return SimpleTerm(value, term, title)


@implementer(IFacetTitleVocabularyFactory)
class I18NFacetTitlesVocabularyFactory(object):
    def __call__(self, context):
        return I18NFacetTitles()
