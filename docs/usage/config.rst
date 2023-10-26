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

Configuration Using Environment Variables
.........................................

The connection settings as well as the login and password for basic authentication can be defined using environment variables.
This is helpful to maintain Plone instances with Docker and different SolR servers.
Example::

    environment-vars +=
      COLLECTIVE_SOLR_HOST localhost
      COLLECTIVE_SOLR_PORT 8983
      COLLECTIVE_SOLR_BASE /solr/plone
      COLLECTIVE_SOLR_LOGIN solr_login
      COLLECTIVE_SOLR_PASSWORD solr_password
      COLLECTIVE_SOLR_HTTPS_CONNECTION true
      COLLECTIVE_SOLR_IGNORE_CERTIFICATE_CHECK false

Configuration priority
......................

There is a priority between configuration methods (ZCML, environment variables and TTW)

    1. ZCML
    2. Environment Variables
    3. TTW Configuration

Since parameters are limited for ZCML and Environement Variables methods, the three methods can be combined as long as you remember the priority above.

Here is a list of parameters and methods

============================    ===============  ========  =========================  =======
**Parameter**                   **Example**      **ZCML**  **Environment Variables**  **TTW**
============================    ===============  ========  =========================  =======
**Port**                        8983             YES       YES                        YES
**Base**                        /solr/plone      YES       YES                        YES
**Login**                       login            NO        YES                        YES
**Password**                    password         NO        YES                        YES
**Https connection**            true             NO        YES                        YES
**Ignore certificate check**    false            NO        YES                        YES
**Other parameters**                             NO        NO                         YES
============================    ===============  ========  =========================  =======


TTW Configuration
.................

TTW Configuration of Solr-Settings
**********************************

