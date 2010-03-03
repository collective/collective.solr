from Testing.ZopeTestCase import installPackage, installProduct
from Products.Five import zcml
from Products.Five import fiveconfigure
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer


class SolrLayer(BasePTCLayer):
    """ layer for solr integration tests """

    def afterSetUp(self):
        # load zcml
        fiveconfigure.debug_mode = True
        from collective import indexing, solr
        zcml.load_config('configure.zcml', indexing)
        zcml.load_config('configure.zcml', solr)
        fiveconfigure.debug_mode = False
        # install package, import profile...
        installPackage('collective.indexing', quiet=True)
        installPackage('collective.solr', quiet=True)
        # finally load the testing profile
        self.addProfile('collective.solr:search')

layer = solr = SolrLayer(bases=[ptc_layer])


class BlobLinguaLayer(BasePTCLayer):
    """ layer for integration tests with LinguaPlone """

    def afterSetUp(self):
        # load zcml
        fiveconfigure.debug_mode = True
        from Products import LinguaPlone
        zcml.load_config('configure.zcml', LinguaPlone)
        fiveconfigure.debug_mode = False
        installProduct('LinguaPlone', quiet=True)
        self.addProfile('LinguaPlone:default')

lingua = SolrLayer(bases=[layer])
