Java Settings
*************

Make sure you are using a `server` version of Java in production.
The output of::

  $ java -version

should include `Java HotSpot(TM) Server VM` or `Java HotSpot(TM) 64-Bit Server VM`.
You can force the Java VM into server mode by calling it with the `-server` command.
Do not try to run Solr with versions of OpenJDK or other non-official Java versions.
They tend to not work well or at all.

Depending on the size of your Solr index, you need to configure the Java VM to have enough memory.
Good starting values are `-Xms128M -Xmx256M`, as a rule of thumb keep `Xmx` double the size of `Xms`.

You can configure these settings via the `java_opts` value in the `collective.recipe.solrinstance` recipe section like::

  java_opts =
    -server
    -Xms128M
    -Xmx256M
