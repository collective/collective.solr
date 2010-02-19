from Testing.ZopeTestCase import installPackage
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


layer = SolrLayer(bases=[ptc_layer])
