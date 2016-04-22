from collective.solr.flare import PloneFlare
from collective.solr.parser import SolrResponse
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.catalog import LazyCatalogResultSerializer
from plone.restapi.serializer.catalog import BrainSerializer
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(SolrResponse, Interface)
class LazySolrCatalogResultSerializer(LazyCatalogResultSerializer):
    """ The LazyCatalog adapter for the plone.restapi JSON serialization """


@implementer(ISerializeToJson)
@adapter(PloneFlare, Interface)
class SolrFlareSerializer(BrainSerializer):
    """ The SolrFlare adapter for the plone.restapi JSON serialization """
