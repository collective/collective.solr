from unittest import TestCase

import transaction
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.utils import activate
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.utils import safe_unicode


class TestDublincoreSubjectField(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        subjects = [safe_unicode("\xc3\xbcber Keyword"), safe_unicode("Second one")]

        self.content = api.content.create(
            container=api.portal.get(),
            type="Document",
            title="test document",
            subject=subjects,
        )

    def test_successfully_reindex_umlauts(self):
        activate()
        self.content.reindexObject()
        # This failed before with a UnicodeDecodeError
        transaction.commit()
