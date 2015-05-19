Installation, Setup and Usage of Solr Integration
=================================================


Installation
------------

Installing collective.solr for a Plone buildout / project
*********************************************************



Installing Solr
***************





Setup Solr
----------

Solr Schema
***********


Solr Field Types
................





.. include:: autocomplete.rst



Solr Base Schema for Plone
**************************






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
            <solr:connection host="localhost" port="8983" base="/solr"/>
       </configure>

TTW Configuration
.................




TTW Configuration of Solr-Settings
**********************************




Considerations for a production Setup
-------------------------------------

.. include:: java_settings.rst

.. include:: monitoring.rst

.. include:: replication.rst

.. include:: solrcloud.rst

