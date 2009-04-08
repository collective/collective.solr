/* use `collective.js.showmore` to hide facet counts via jquery */

jq(function() {
    jq('#portal-searchfacets dl').showMore({
        expression: 'dt:gt(4), dd:gt(4)'
    });
});
