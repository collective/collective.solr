Installation
------------

Installing collective.solr for a Plone buildout / project
*********************************************************


The following buildout configuration may be used to get started quickly::

  [buildout]
  extends =
    buildout.cfg
    https://raw.githubusercontent.com/collective/collective.solr/master/solr.cfg
    https://raw.githubusercontent.com/collective/collective.solr/master/solr-4.10.x.cfg

  [instance]
  eggs += collective.solr

After saving this to let's say ``solr.cfg`` the buildout can be run and the `Solr`_ server and `Plone`_ instance started::

  $ python bootstrap.py
  $ bin/buildout -c solr.cfg
  ...
  $ bin/solr-instance start
  $ bin/instance start

Next you should activate the ``collective.solr (site search)`` add-on in the add-on control panel of Plone.
After activation you should review the settings in the new ``Solr Settings`` control panel.
To index all your content in Solr you can call the provided maintenance view::

  http://localhost:8080/plone/@@solr-maintenance/reindex

Creating the initial index can take some considerable time.
A typical indexing rate for a Plone site running of a local disk is 20 index operations per second.
While Solr scales to orders of magnitude more than that, the limiting factor is database access time in Plone.

If you have an existing site with a large volume of content,
you can create an initial Solr index on a staging server or development machine,
then rsync it over to the live machine, enable Solr and call `@@solr-maintenance/sync`.
The sync will usually take just a couple of minutes for catching up with changes in the live database.
You can also use this approach when making changes to the index structure or changing the settings of existing fields.

Note that the example ``solr.cfg`` is bound to change.
Always copy the file to your local buildout.
In general you should never rely on extending buildout config files from servers that aren't under your control.


.. _Solr: http://lucene.apache.org/solr/
.. _Plone: https://plone.org
