Configuring collective.solr
---------------------------

Solr-Connection Configuration
*****************************

ZCML Configuration (prefered)
.............................

The connections settings for Solr can be configured in ZCML and thus in buildout.
This makes it easier when copying databases between multiple Zope instances with different Solr servers.
Example::

    zcml-additional =
        <configure xmlns:solr="http://namespaces.plone.org/solr">
            <solr:connection host="localhost" port="8983" base="/solr/plone"/>
       </configure>

TTW Configuration
.................

TTW Configuration of Solr-Settings
**********************************

