Monitoring
**********

Java has a general monitoring framework called JMX.
You can use this to get a huge number of details about the Java process in general and Solr in particular.
Some hints are at http://wiki.apache.org/solr/SolrJmx.
The default `collective.recipe.solrinstance` config uses `<jmx />`,
so we can use command line arguments to configure it.
Our example `buildout/solr.cfg` includes all the relevant values in its `java_opts` variable.

To view all the available metrics,
start Solr and then the `jconsole` command included in the Java SDK and connect to the local process named `start.jar`.
Solr specific information is available from the MBeans tab under the `solr` section.
For example you'll find `avgTimePerRequest` within `search/org.apache.solr.handler.component.SearchHandler` under `Attributes`.

If you want to integrate with munin, you can install the JMX plugin at:
http://exchange.munin-monitoring.org/plugins/jmx/details

Follow its install instructions and tweak the included examples to query the information you want to track.
To track the average time per search request,
add a file called `solr_avg_query_time.conf` into `/usr/share/munin/plugins` with the following contents::

    graph_title Average Query Time
    graph_vlabel ms
    graph_category Solr

    solr_average_query_time.label time per request
    solr_average_query_time.jmxObjectName solr/:type=search,id=org.apache.solr.handler.component.SearchHandler
    solr_average_query_time.jmxAttributeName avgTimePerRequest

Then add a symlink to add the plugin::

    $ ln -s /usr/share/munin/plugins/jmx_ /etc/munin/plugins/jmx_solr_avg_query_time

Point the jmx plugin to the Solr process, by opening `/etc/munin/plugin-conf.d/munin-node.conf` and adding something like::

    [jmx_*]
    env.jmxurl service:jmx:rmi:///jndi/rmi://127.0.0.1:8984/jmxrmi

The host and port need to match those passed via `java_opts` to Solr.
To check if the plugins are working do::

    $ export jmxurl="service:jmx:rmi:///jndi/rmi://127.0.0.1:8984/jmxrmi"
    $ cd /etc/munin/plugins

And call the plugin you configured directly, like for example::

    $ ./solr_avg_query_time
    solr_average_query_time.value NaN

We include a number of useful configurations inside the package, in the `collective/solr/munin_config` directory.
You can copy all of them into the `/usr/share/munin/plugins` directory and create the symlinks for all of them.
