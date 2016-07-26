from unittest import TestCase

from plone.app.contentlisting.interfaces import IContentListingObject
from plone.uuid.interfaces import IUUID
from zope.interface.verify import verifyClass

from collective.solr.contentlisting import FlareContentListingObject
from collective.solr.flare import PloneFlare
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING


class ContentListingTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.flare = FlareContentListingObject(PloneFlare({
            'getId': 'foobar',
            'path_string': '/plone/news',
            'UID': 'test-uid',
            'getObjSize': 42,
            'review_state': 'published',
            }))

    def testInterfaceComplete(self):
        self.assertTrue(
            verifyClass(IContentListingObject, FlareContentListingObject))

    def test_getId(self):
        self.assertEqual(self.flare.getId(), 'foobar')

    def test_getObject(self):
        self.assertEqual(self.flare.getObject(), self.layer['portal']['news'])

    def test_getDataOrigin(self):
        self.assertEqual(self.flare.getObject(), self.layer['portal']['news'])

    def test_getPath(self):
        self.assertEqual(self.flare.getPath(), '/plone/news')

    def test_getURL(self, relative=False):
        self.assertEqual(self.flare.getURL(False), '/plone/news')
        self.assertEqual(self.flare.getURL(True), '/plone/news')

    def test_uuid_key(self):
        self.assertEqual(self.flare.uuid(), 'test-uid')

    def test_uuid_object(self):
        del self.flare.flare['UID']
        self.assertEqual(self.flare.uuid(),
                         IUUID(self.layer['portal']['news']))

    def test_getSize(self):
        self.assertEqual(self.flare.getSize(), 42)

    def test_review_state(self):
        self.assertEqual(self.flare.review_state(), 'published')

    # def listCreators(self):
    #     return self.flare.listCreators
    #
    # def Creator(self):
    #     return self.flare.Creator
    #
    # def Subject(self):
    #     return self.flare.Subject
    #
    # def Publisher(self):
    #     return NotImplementedError
    #
    # def listContributors(self):
    #     return NotImplementedError
    #
    # def Contributors(self):
    #     return self.listContributors()
    #
    # def Date(self, zone=None):
    #     return self.flare.Date
    #
    # def CreationDate(self, zone=None):
    #     return self.flare.created
    #
    # def EffectiveDate(self, zone=None):
    #     # Work around an incompatibility of Archetypes/DateTime
    #     # in effective. See #13362
    #     return self.getObject().EffectiveDate()
    #
    # def ExpirationDate(self, zone=None):
    #     return self.flare.expires
    #
    # def ModificationDate(self, zone=None):
    #     return self.flare.modified
    #
    # def Format(self):
    #     raise NotImplementedError
    #
    # def Identifier(self):
    #     return self.getURL()
    #
    # def Language(self):
    #     self.Language
    #
    # def Rights(self):
    #     return NotImplementedError
    #
    # def Title(self):
    #     return self.flare.Title
    #
    # def Description(self):
    #     return self.flare.Description
    #
    # def Type(self):
    #     return self.flare.Type
    #
    # def ContentTypeClass(self):
    #     return "contenttype-" + getUtility(IIDNormalizer).normalize(
    #         self.PortalType())
    #
    # def PortalType(self):
    #     return self.flare.portal_type
    #
    # def Author(self):
    #     return self.getUserData(self.Creator())
    #
    # def getUserData(self, username):
    #     request = getRequest()
    #     _usercache = request.get('usercache', None)
    #     if _usercache is None:
    #         self.request.set('usercache', {})
    #         _usercache = {}
    #     userdata = _usercache.get(username, None)
    #     if userdata is None:
    #         membershiptool = api.portal.get_tool('portal_membership')
    #         userdata = membershiptool.getMemberInfo(self.Creator())
    #         if not userdata:
    #             userdata = {
    #                 'username': username,
    #                 'description': '',
    #                 'language': '',
    #                 # TODO
    #                 # string:${navigation_root_url}/author/${item_creator}
    #                 'home_page': '/HOMEPAGEURL',
    #                 'location': '',
    #                 'fullname': username
    #             }
    #         self.request.usercache[username] = userdata
    #     return userdata
    #
    # # Temporary to workaround a bug in current plone.app.search<=1.1.0
    # def portal_type(self):
    #     return self.PortalType()
    #
    # def CroppedDescription(self):
    #     return self.flare.Description
