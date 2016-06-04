Indexing
********

Solr is not transactional aware or supports any kind of rollback or undo.
We therefor only sent data to Solr at the end of any successful request.
This is done via collective.indexing,
a transaction manager and an end request transaction hook.
This means you won't see any changes done to content inside a request when doing Solr searches later on in the same request.
Inside tests you need to either commit real transactions or otherwise flush the Solr connection.
There's no transaction concept,
so one request doing a search might get some results in its beginning,
than a different request might add new information to Solr.
If the first request is still running and does the same search again it might get different results taking the changes from the second request into account.

Solr is not a real time search engine.
While there's work under way to make Solr capable of delivering real time results,
there's currently always a certain delay up to some minutes from the time data is sent to Solr to when it is available in searches.

Search results are returned in Solr by distinct search threads.
These search threads hold a great number of caches which are crucial for Solr to perform.
When index or unindex operations are sent to Solr,
it will keep those in memory until a commit is executed on its own search index.
When a commit occurs, all search threads and thus all caches are thrown away and new threads are created reflecting the data after the commit.
While there's a certain amount of cache data that is copied to the new search threads,
this data has to be validated against the new index which takes some time.
The `useColdSearcher` and `maxWarmingSearchers` options of the Solr recipe relate to this aspect.
While cache data is copied over and validated for a new search thread, the searcher is `warming up`.
If the warming up is not yet completed the searcher is considered to be `cold`.

In order to get real good performance out of Solr,
we need to minimize the number of commits against the Solr index.
We can achieve this by turning off `auto-commit` and instead use `commitWithin`.
So we don't sent a `commit` to Solr at the end of each index/unindex request on the Plone side.
Instead we tell Solr to commit the data to its index at most after a certain time interval.
Values of 15 minutes to 1 minute work well for this interval.
The larger you can make this interval,
the better the performance of Solr will be,
at the cost of search results lagging behind a bit.
In this setup we also need to configure the `autoCommitMaxTime` option of the Solr server,
as `commitWithin` only works for index but not unindex operations.
Otherwise a large number of unindex operations without any index operations occurring could not be reflected in the index for a long time.

As a result of all the above,
the Solr index and the Plone site will always have slightly diverging contents.
If you use Solr to do searches you need to be aware of this,
as you might get results for objects that no longer exist.
So any `brain/getObject` call on the Plone side needs to have error handling code around it as the object might not be there anymore and traversing to it can throw an exception.

When adding new or deleting old content or changing the workflow state of it,
you will also not see those actions reflected in searches right away,
but only after a delay of at most the `commitWithin` interval.
After a `commitWithin` operation is sent to Solr,
any other operations happening during that time window will be executed after the first interval is over.
So with a 15 minute interval,
if document A is indexed at 5:15,
B at 5:20 and C at 5:35,
both A & B will be committed at 5:30 and C at 5:50.
