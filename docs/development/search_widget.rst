Search widget:
--------------

The search widget in the @@search view is implemented using React. It provides
the default Plone search behavior. It uses the search REST API provided by
the plone.restapi package.

The sources and distribution files can be found in the static directory. The
Webpack build files are also provided in case you need to improve, customize or
extend the default features of the widget.

You can setup the widget development environment by::

  $ cd src/collective/solr/static/
  $ npm install

Then also given a collective.solr development instance running in port 8080 and
solr running::

  $ npm start

Then you can access to the URL http://localhost:3000

Once you've finished developing, you should create a bundle by::

  $ npm run build
