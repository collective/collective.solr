# -*- coding: utf-8 -*-
from zope.component import queryUtility
from zope.interface import implements
from zope.schema.interfaces import IBaseVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from collective.solr import SolrMessageFactory
from collective.solr.interfaces import IFacetTitleVocabularyFactory
from collective.solr.interfaces import ISolrConnectionManager

from zope.component import getUtility
from plone.registry.interfaces import IRegistry


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
            registry = getUtility(IRegistry)
            items = registry['collective.solr.filter_queries']
        return SimpleVocabulary([SimpleTerm(item) for item in items])


class I18NFacetTitles(object):
    """Vocabulary that wraps any term into message ids in the solr translation
    domain. This is generally the default behaviour for facet titles.
    """
    implements(IBaseVocabulary)

    def __contains__(self, term):
        return True

    def getTerm(self, term):
        value = term
        title = SolrMessageFactory(term)
        if isinstance(term, unicode):
            # Terms must be byte strings
            term = term.encode('utf8')
        return SimpleTerm(value, term, title)


class I18NFacetTitlesVocabularyFactory(object):
    implements(IFacetTitleVocabularyFactory)

    def __call__(self, context):
        return I18NFacetTitles()
