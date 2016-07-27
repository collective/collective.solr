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
            'listCreators': ['foo', 'bar'],
            'Creator': 'Flare Creator',
            'Title': 'Flare Title',
            'Description': 'Flare Description',
            'Subject': 'Flare Subject',
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

    def test_getURL(self):
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

    def test_listCreators(self):
        self.assertEqual(self.flare.listCreators(), ['foo', 'bar'])

    def test_Creator(self):
        self.assertEqual(self.flare.Creator(), 'Flare Creator')

    def test_Subject(self):
        self.assertEqual(self.flare.Subject(), 'Flare Subject')

    def X_test_Publisher(self):
        self.assertRaises(NotImplementedError, self.flare.Publisher())

    def X_test_listContributors(self):
        self.assertRaises(NotImplementedError, self.flare.listContributors())

    def X_test_Contributors(self):
        self.assertRaises(NotImplementedError, self.flare.Contributors())

    # def Date(self, zone=None):
    #     self.assertEqual(self.flare.Date
    #
    # def CreationDate(self, zone=None):
    #     self.assertEqual(self.flare.created
    #
    # def EffectiveDate(self, zone=None):
    #     # Work around an incompatibility of Archetypes/DateTime
    #     # in effective. See #13362
    #     self.assertEqual(self.getObject().EffectiveDate()
    #
    # def ExpirationDate(self, zone=None):
    #     self.assertEqual(self.flare.expires
    #
    # def ModificationDate(self, zone=None):
    #     self.assertEqual(self.flare.modified

    def test_Format(self):
        self.assertRaises(NotImplementedError, self.flare.Format)

    def test_Identifier(self):
        self.assertEqual(self.flare.Identifier(), '/plone/news')

    def Language(self):
        self.Language

    def X_test_Rights(self):
        self.assertRaises(NotImplementedError, self.flare.Rights)

    def test_Title(self):
        self.assertEqual(self.flare.Title(), 'Flare Title')

    def test_Description(self):
        self.assertEqual(self.flare.Description(), 'Flare Description')

    # def Type(self):
    #     self.assertEqual(self.flare.Type
    #
    # def ContentTypeClass(self):
    #     self.assertEqual("contenttype-" +
    #
    #         self.PortalType())
    #
    # def PortalType(self):
    #     self.assertEqual(self.flare.portal_type
    #
    # def Author(self):
    #     self.assertEqual(self.getUserData(self.Creator())
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
    #     self.assertEqual(userdata

    def X_test_CroppedDescription(self):
        self.assertEqual(self.flare.CroppedDescription(), 'Flare Description')
