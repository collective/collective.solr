# -*- coding: utf-8 -*-


class SolrException(Exception):
   """Base class where all other exceptions from collective.solr derive from"""


class SolrInactiveException(SolrException):
    """ an exception indicating the solr integration is not activated """
