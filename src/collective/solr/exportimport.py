# -*- coding: utf-8 -*-
from persistent.interfaces import IPersistent
from zope.component import queryUtility
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
        self.context.async = False
        self.context.auto_commit = True
        self.context.commit_within = 0
        self.context.index_timeout = 0
        self.context.search_timeout = 0
        self.context.max_results = 10000000
        self.context.required = []
        self.context.search_pattern = ''
        self.context.facets = []
        self.context.filter_queries = []
        self.context.slow_query_threshold = 0
        self.context.effective_steps = 1
        self.context.exclude_user = False
        self.context.highlight_fields = []
        self.context.highlight_formatter_pre = ''
        self.context.highlight_formatter_post = ''
        self.context.highlight_fragsize = 0
        self.context.levenshtein_distance = 0
        self.context.atomic_updates = True

    def _initProperties(self, node):
        elems = node.getElementsByTagName('connection')
        if elems:
            assert len(elems) == 1
            conn = elems[0]
            for child in conn.childNodes:
                if child.nodeName == 'active':
                    value = str(child.getAttribute('value'))
                    self.context.active = self._convertToBoolean(value)
                elif child.nodeName == 'port':
                    value = int(str(child.getAttribute('value')))
                    self.context.port = value
                elif child.nodeName == 'host':
                    self.context.host = str(child.getAttribute('value'))
                elif child.nodeName == 'base':
                    self.context.base = str(child.getAttribute('value'))
        elems = node.getElementsByTagName('settings')
        if elems:
            assert len(elems) == 1
            settings = elems[0]
            for child in settings.childNodes:
                if child.nodeName == 'async':
                    value = str(child.getAttribute('value'))
                    self.context.async = self._convertToBoolean(value)
                elif child.nodeName == 'auto-commit':
                    value = str(child.getAttribute('value'))
                    self.context.auto_commit = self._convertToBoolean(value)
                elif child.nodeName == 'commit-within':
                    value = int(child.getAttribute('value'))
                    self.context.commit_within = value
                elif child.nodeName == 'index-timeout':
                    value = float(str(child.getAttribute('value')))
                    self.context.index_timeout = value
                elif child.nodeName == 'search-timeout':
                    value = float(str(child.getAttribute('value')))
                    self.context.search_timeout = value
                elif child.nodeName == 'max-results':
                    value = int(str(child.getAttribute('value')))
                    self.context.max_results = value
                elif child.nodeName == 'required-query-parameters':
                    value = []
                    for elem in child.getElementsByTagName('parameter'):
                        value.append(elem.getAttribute('name'))
                    self.context.required = tuple(map(str, value))
                elif child.nodeName == 'search-pattern':
                    value = str(child.getAttribute('value'))
                    self.context.search_pattern = value
                elif child.nodeName == 'search-facets':
                    value = []
                    for elem in child.getElementsByTagName('parameter'):
                        value.append(elem.getAttribute('name'))
                    self.context.facets = tuple(map(str, value))
                elif child.nodeName == 'filter-query-parameters':
                    value = []
                    for elem in child.getElementsByTagName('parameter'):
                        value.append(elem.getAttribute('name'))
                    self.context.filter_queries = tuple(map(str, value))
                elif child.nodeName == 'slow-query-threshold':
                    value = int(str(child.getAttribute('value')))
                    self.context.slow_query_threshold = value
                elif child.nodeName == 'effective-steps':
                    value = int(str(child.getAttribute('value')))
                    self.context.effective_steps = value
                elif child.nodeName == 'exclude-user':
                    value = str(child.getAttribute('value'))
                    self.context.exclude_user = self._convertToBoolean(value)
                elif child.nodeName == 'highlight_fields':
                    value = []
                    for elem in child.getElementsByTagName('parameter'):
                        value.append(elem.getAttribute('name'))
                    self.context.highlight_fields = tuple(map(str, value))
                elif child.nodeName == 'highlight_formatter_pre':
                    value = str(child.getAttribute('value'))
                    self.context.highlight_formatter_pre = value
                elif child.nodeName == 'highlight_formatter_post':
                    value = str(child.getAttribute('value'))
                    self.context.highlight_formatter_post = value
                elif child.nodeName == 'highlight_fragsize':
                    value = int(str(child.getAttribute('value')))
                    self.context.highlight_fragsize = value
                elif child.nodeName == 'field-list':
                    value = []
                    for elem in child.getElementsByTagName('parameter'):
                        value.append(elem.getAttribute('name'))
                    self.context.field_list = tuple(map(str, value))
                elif child.nodeName == 'levenshtein_distance':
                    value = float(str(child.getAttribute('value')))
                    self.context.levenshtein_distance = value
                elif child.nodeName == 'atomic_updates':
                    value = str(child.getAttribute('value'))
                    self.context.atomic_updates = self._convertToBoolean(value)

    def _createNode(self, name, value):
        node = self._doc.createElement(name)
        node.setAttribute('value', value)
        return node

    def _extractProperties(self):
        node = self._doc.createElement('object')
        node.setAttribute('name', 'solr')
        conn = self._doc.createElement('connection')
        create = self._createNode
        node.appendChild(conn)
        conn.appendChild(create('active', str(bool(self.context.active))))
        conn.appendChild(create('host', self.context.host))
        conn.appendChild(create('port', str(self.context.port)))
        conn.appendChild(create('base', self.context.base))
        settings = self._doc.createElement('settings')
        node.appendChild(settings)
        append = settings.appendChild
        append(create('async', str(bool(self.context.async))))
        append(create('auto-commit', str(bool(self.context.auto_commit))))
        append(create('commit-within', str(self.context.commit_within)))
        append(create('index-timeout', str(self.context.index_timeout)))
        append(create('search-timeout', str(self.context.search_timeout)))
        append(create('max-results', str(self.context.max_results)))
        required = self._doc.createElement('required-query-parameters')
        append(required)
        for name in self.context.required:
            param = self._doc.createElement('parameter')
            param.setAttribute('name', name)
            required.appendChild(param)
        append(create('search-pattern', self.context.search_pattern))
        facets = self._doc.createElement('search-facets')
        append(facets)
        for name in self.context.facets:
            param = self._doc.createElement('parameter')
            param.setAttribute('name', name)
            facets.appendChild(param)
        filter_queries = self._doc.createElement('filter-query-parameters')
        append(filter_queries)
        for name in self.context.filter_queries:
            param = self._doc.createElement('parameter')
            param.setAttribute('name', name)
            filter_queries.appendChild(param)
        append(
            create(
                'slow-query-threshold',
                str(self.context.slow_query_threshold)
            )
        )
        append(create('effective-steps', str(self.context.effective_steps)))
        append(create('exclude-user', str(bool(self.context.exclude_user))))
        highlight_fields = self._doc.createElement('highlight_fields')
        append(highlight_fields)
        for name in self.context.highlight_fields:
            param = self._doc.createElement('parameter')
            param.setAttribute('name', name)
            highlight_fields.appendChild(param)
        append(
            create(
                'highlight_formatter_pre',
                self.context.highlight_formatter_pre
            )
        )
        append(
            create(
                'highlight_formatter_post',
                self.context.highlight_formatter_post
            )
        )
        append(
            create(
                'highlight_fragsize',
                str(self.context.highlight_fragsize)
            )
        )
        field_list = self._doc.createElement('field-list')
        append(field_list)
        append(
            create(
                'levenshtein_distance',
                str(self.context.levenshtein_distance)
            )
        )
        append(create('atomic_updates',
               str(bool(self.context.atomic_updates))))

        for name in self.context.field_list:
            param = self._doc.createElement('parameter')
            param.setAttribute('name', name)
            facets.appendChild(param)
        return node


def importSolrSettings(context):
    """ import settings for solr integration from an XML file """
    site = context.getSite()
    utility = queryUtility(ISolrConnectionConfig, context=site)
    if utility is None:
        logger = context.getLogger('collective.solr')
        logger.info('Nothing to import.')
        return
    if IPersistent.providedBy(utility):
        importObjects(utility, '', context)


def exportSolrSettings(context):
    """ export settings for solr integration as an XML file """
    site = context.getSite()
    utility = queryUtility(ISolrConnectionConfig, context=site)
    if utility is None:
        logger = context.getLogger('collective.solr')
        logger.info('Nothing to export.')
        return
    if IPersistent.providedBy(utility):
        exportObjects(utility, '', context)
