Replication
***********

At this point Solr doesn't yet allow for a full fault tolerance setup.
You can read more about the `Solr Cloud`_ effort which aims to provide this.

But we can setup a simple master/slave replication using Solr's built-in `Solr Replication`_ support,
which is a first step in the right direction.

  .. _Solr Cloud: http://wiki.apache.org/solr/SolrCloud
  .. _Solr Replication: http://wiki.apache.org/solr/SolrReplication

In order to use this, you can setup a Solr master server and give it some extra config::

    [solr-instance]
    additional-solrconfig =
      <requestHandler name="/replication" class="solr.ReplicationHandler" >
        <lst name="master">
          <str name="replicateAfter">commit</str>
          <str name="replicateAfter">startup</str>
          <str name="replicateAfter">optimize</str>
        </lst>
      </requestHandler>

Then you can point one or multiple slave servers to the master.
Assuming the master runs on `solr-master.domain.com` at port `8983`, we could write::

    [solr-instance]
    additional-solrconfig =
      <requestHandler name="/replication" class="solr.ReplicationHandler" >
        <lst name="slave">
          <str name="masterUrl">http://solr-master.domain.com:8983/solr/replication</str>
          <str name="pollInterval">00:00:30</str>
        </lst>
      </requestHandler>

A poll interval of 30 seconds should be fast enough without creating too much overhead.

At this point `collective.solr` does not yet have support for connecting to multiple servers and using the slaves as a fallback for querying.
As there's no master-master setup yet, fault tolerance for index changes cannot be provided.
