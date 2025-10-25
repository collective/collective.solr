from collective.solr.interfaces import IZCMLSolrConnectionConfig
from collective.solr.manager import ZCMLSolrConnectionConfig
from zope import schema
from zope.component.zcml import utility
from zope.interface import Interface


class ISolrConnectionConfigDirective(Interface):
    """Directive which registers a Solr connection config"""

    host = schema.ASCIILine(
        title="Host",
        description="The host name of the Solr instance to be used.",
        required=True,
    )

    port = schema.Int(
        title="Port",
        description="The port of the Solr instance to be used.",
        required=True,
    )

    base = schema.ASCIILine(
        title="Base",
        description="The base prefix of the Solr instance to be used.",
        required=True,
    )


def solrConnectionConfigDirective(_context, host, port, base):

    utility(
        _context,
        provides=IZCMLSolrConnectionConfig,
        component=ZCMLSolrConnectionConfig(host, port, base),
    )
