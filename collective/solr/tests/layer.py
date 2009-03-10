from Testing.ZopeTestCase import app, close, installPackage
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.layer import PloneSite
from transaction import commit


class SolrLayer(PloneSite):
    """ layer for solr integration tests """

    @classmethod
    def setUp(cls):
        # load zcml
        fiveconfigure.debug_mode = True
        from collective import indexing, solr
        zcml.load_config('configure.zcml', indexing)
        zcml.load_config('configure.zcml', solr)
        fiveconfigure.debug_mode = False
        # install package, import profile...
        installPackage('collective.solr', quiet=True)
        root = app()
        profile = 'profile-collective.solr:search'
        tool = getToolByName(root.plone, 'portal_setup')
        tool.runAllImportStepsFromProfile(profile, purge_old=False)
        # and commit the changes
        commit()
        close(root)

    @classmethod
    def tearDown(cls):
        pass


class SolrFacetsLayer(SolrLayer):
    """ layer for solr integration tests with facet support """

    @classmethod
    def setUp(cls):
        # import facets profile...
        root = app()
        profile = 'profile-collective.solr:facets'
        tool = getToolByName(root.plone, 'portal_setup')
        tool.runAllImportStepsFromProfile(profile, purge_old=False)
        # and commit the changes
        commit()
        close(root)

    @classmethod
    def tearDown(cls):
        pass

