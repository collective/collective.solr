from plone.restapi.services import Service
from AccessControl.SecurityManagement import getSecurityManager
from Products.CMFPlone.utils import base_hasattr
from zope.component import getUtility
from collective.solr.interfaces import ISearch

SPECIAL_CHARS = [
    "+",
    "-",
    "&&",
    "||",
    "!",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    '"',
    "~",
    "*",
    "?",
    ":",
    "/",
]


def escape(term):
    for char in SPECIAL_CHARS:
        term = term.replace(char, "\\" + char)
    return term


class SolrSearchGet(Service):
    def reply(self):
        search = getUtility(ISearch)
        query = self.request.form.get("q")
        if not query:
            query = "*:*"
        # return poor man's serializer for now
        return [
            {
                "id": obj.get("id"),
                "UID": obj.get("UID"),
                "Type": obj.get("Type"),
                "Title": obj.get("Title"),
                "review_state": obj.get("review_state"),
                "allowedRolesAndUsers": obj.get("allowedRolesAndUsers"),
            }
            for obj in search(query=query, fq=self.security_filter())
        ]
        # serializer = queryMultiAdapter(
        #     (self.context, self.request), LazyCatalogResultSerializer
        # )
        # return serializer()

    def security_filter(self):
        user = getSecurityManager().getUser()
        roles = user.getRoles()
        if "Anonymous" in roles:
            return u"allowedRolesAndUsers:Anonymous"
        roles = list(roles)
        roles.append("Anonymous")
        if base_hasattr(user, "getGroups"):
            groups = [u"user:%s" % x for x in user.getGroups()]
            if groups:
                roles = roles + groups
        roles.append(u"user:%s" % user.getId())
        # Roles with spaces need to be quoted
        roles = [u'"%s"' % escape(r) if " " in r else escape(r) for r in roles]
        return u"allowedRolesAndUsers:(%s)" % u" OR ".join(roles)
