from unittest import TestCase, TestSuite, makeSuite, main

from collective.solr.search import quote


class QueryTests(TestCase):

    def testQuoting(self):
        self.assertEqual(quote('foo'), 'foo')
        self.assertEqual(quote('foo '), '"foo "')
        self.assertEqual(quote('foo bar'), '"foo bar"')
        self.assertEqual(quote('foo bar what?'), '"foo bar what\?"')
        self.assertEqual(quote('[]'), '"\[\]"')
        self.assertEqual(quote('()'), '"\(\)"')
        self.assertEqual(quote('{}'), '"\{\}"')
        self.assertEqual(quote('""'), '"\\"\\""')
        self.assertEqual(quote('\\'), '"\\"')
        self.assertEqual(quote('-+&|!^~*?:'), '"\\-\\+\\&\\|\\!\\^\\~\\*\\?\\:"')


def test_suite():
    return TestSuite((
        makeSuite(QueryTests),
    ))

if __name__ == '__main__':
    main(defaultTest='test_suite')

