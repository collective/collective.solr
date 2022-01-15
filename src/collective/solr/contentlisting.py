from Acquisition import aq_base
from plone import api
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.layout.icons.interfaces import IContentIcon
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.browser.ploneview import Plone as PloneView
from zope.component import getMultiAdapter, getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer

missing = object()


@implementer(IContentListingObject)
class FlareContentListingObject(object):
    def __init__(self, flare):
        self.flare = flare

    def getId(self):
        return self.flare.getId

    def getObject(self):
        return self.flare.getObject()

    def getDataOrigin(self):
        return self.flare.getObject()

    def getPath(self):
        return self.flare.getPath()

    def getURL(self, relative=False):
        return self.flare.getURL(relative)

    def uuid(self):
        if "UID" in self.flare:
            return self.flare.UID
        else:
            return IUUID(self.getObject())

    def getIcon(self):
        return getMultiAdapter(
            (self.getObject(), getRequest(), self.flare), interface=IContentIcon
        )()

    def getSize(self):
        return self.flare.getObjSize

    def review_state(self):
        return self.flare.review_state

    def listCreators(self):
        return self.flare.listCreators

    def Creator(self):
        return self.flare.Creator

    def Subject(self):
        return self.flare.Subject

    def Publisher(self):
        raise NotImplementedError

    def listContributors(self):
        raise NotImplementedError

    def Contributors(self):
        return self.listContributors()

    def Date(self, zone=None):
        return self.flare.Date

    def CreationDate(self, zone=None):
        return self.flare.created

    def EffectiveDate(self, zone=None):
        # Work around an incompatibility of Archetypes/DateTime
        # in effective. See #13362
        return self.getObject().EffectiveDate()

    def ExpirationDate(self, zone=None):
        return self.flare.expires

    def ModificationDate(self, zone=None):
        return self.flare.modified

    def Format(self):
        raise NotImplementedError

    def Identifier(self):
        return self.getURL()

    def Language(self):
        return self.flare.Language

    def Rights(self):
        raise NotImplementedError

    def Title(self):
        return self.flare.Title

    def Description(self):
        return self.flare.Description

    def Type(self):
        return self.flare.Type

    def ContentTypeClass(self):
        return "contenttype-" + getUtility(IIDNormalizer).normalize(self.PortalType())

    def PortalType(self):
        return self.flare.portal_type

    def Author(self):
        return self.getUserData(self.Creator())

    def getUserData(self, username):
        request = getRequest()
        _usercache = request.get("usercache", None)
        if _usercache is None:
            request.set("usercache", {})
            _usercache = {}
        userdata = _usercache.get(username, None)
        if userdata is None:
            membershiptool = api.portal.get_tool("portal_membership")
            userdata = membershiptool.getMemberInfo(self.Creator())
            if not userdata:
                userdata = {
                    "username": username,
                    "description": "",
                    "language": "",
                    # TODO
                    # string:${navigation_root_url}/author/${item_creator}
                    "home_page": "/HOMEPAGEURL",
                    "location": "",
                    "fullname": username,
                }
            request.usercache[username] = userdata
        return userdata

    def CroppedDescription(self):
        registry = getUtility(IRegistry)
        length = registry.get("plone.search_results_description_length")
        plone_view = PloneView(None, None)
        if not length or not isinstance(length, int):
            # fallback if registry key is None
            length = 160
        return plone_view.cropText(self.flare.Description, length)

    @property
    def UID(self):
        # Alias for when this is used like a brain
        return self.flare.UID

    @property
    def modified(self):
        # Alias for when this is used like a brain
        return self.ModificationDate()

    @property
    def portal_type(self):
        # Alias for when this is used like a brain
        return self.PortalType()

    def MimeTypeIcon(self):
        raise NotImplementedError

    def __getattr__(self, name):
        """We'll override getattr so that we can defer name lookups to the real
        underlying objects without knowing the names of all attributes.

        Adapted from plone.app.contentlisting.catalog.CatalogContentListingObject
        """
        if name.startswith("_"):
            raise AttributeError(name)
        flare_value = self.flare.get(name, missing)
        if flare_value is not missing:
            return flare_value
        object_value = getattr(aq_base(self.getObject()), name, missing)
        if object_value is not missing:
            return object_value
        raise AttributeError(name)
