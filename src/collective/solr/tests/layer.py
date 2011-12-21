from Products.CMFPlone.utils import _createObjectByType
from Testing.ZopeTestCase import installPackage, installProduct
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml

from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer


class SolrLayer(BasePTCLayer):
    """ layer for solr integration tests """

    def afterSetUp(self):
        from collective import indexing, solr
        zcml.load_config('configure.zcml', indexing)
        zcml.load_config('configure.zcml', solr)
        installPackage('collective.indexing', quiet=True)
        installPackage('collective.solr', quiet=True)
        self.addProfile('collective.solr:search')
        
layer = solr = SolrLayer(bases=[ptc_layer])


class BlobLinguaLayer(BasePTCLayer):
    """ layer for integration tests with LinguaPlone """

    def afterSetUp(self):
        from Products import LinguaPlone
        zcml.load_config('configure.zcml', LinguaPlone)
        installProduct('LinguaPlone', quiet=True)
        self.addProfile('LinguaPlone:default')

lingua = SolrLayer(bases=[layer])
