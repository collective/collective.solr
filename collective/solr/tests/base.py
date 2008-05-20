# integration and functional tests
# see http://plone.org/documentation/tutorial/testing/writing-a-plonetestcase-unit-integration-test
# for more information about the following setup

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup


@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    import collective.indexing
    zcml.load_config('configure.zcml', collective.indexing)
    import collective.solr
    zcml.load_config('configure.zcml', collective.solr)
    fiveconfigure.debug_mode = False

setup_product()
ptc.setupPloneSite(extension_profiles=(
    'collective.indexing:default',
    'collective.solr:default',
    'collective.solr:search',
))


class SolrTestCase(ptc.PloneTestCase):
    """ test case for solr integration tests """

    pass

