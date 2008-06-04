from zope.component import getUtility
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase

from collective.solr.interfaces import ISolrConnectionConfig


class SolrConfigXMLAdapter(XMLAdapterBase):

    _LOGGER_ID = 'collective.solr'

    def _exportNode(self):
        """ export the object as a DOM node """
        node = self._extractProperties()
        self._logger.info('settings exported.')
        return node

    def _importNode(self, node):
        """ import the object from the DOM node """
        if self.environ.shouldPurge():
            self._purgeProperties()
        self._initProperties(node)
        self._logger.info('settings imported.')

    def _purgeProperties(self):
        self.context.active = False
        self.context.host = ''
        self.context.port = 0
        self.context.base = ''

    def _initProperties(self, node):
        for child in node.childNodes:
            if child.nodeName == 'active':
                value = self._convertToBoolean(child.getAttribute('value'))
                self.context.active = value
            elif child.nodeName == 'port':
                value = int(child.getAttribute('value'))
            elif child.nodeName in ('host', 'base'):
                self.context.active = value

    def _createNode(self, name, value):
        node = self._doc.createElement(name)
        node.setAttribute('value', value)
        return node

    def _extractProperties(self):
        node = self._doc.createElement('object')
        node.setAttribute('name', 'solr')
        conn = self._doc.createElement('connection')
        node.appendChild(conn)
        conn.appendChild(self._createNode('active', str(bool(self.context.active))))
        conn.appendChild(self._createNode('host', self.context.host))
        conn.appendChild(self._createNode('port', str(self.context.port)))
        conn.appendChild(self._createNode('base', self.context.base))
        return node


def importSolrSettings(context):
    """ import settings for solr integration from an XML file """
    site = context.getSite()
    utility = getUtility(ISolrConnectionConfig, context=site)
    importObjects(utility, '', context)


def exportSolrSettings(context):
    """ export settings for solr integration as an XML file """
    site = context.getSite()
    utility = getUtility(ISolrConnectionConfig, context=site)
    if utility is None:
        logger = context.getLogger('collective.solr')
        logger.info('Nothing to export.')
        return
    exportObjects(utility, '', context)

