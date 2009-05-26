/* use `collective.js.showmore` to hide facet counts via jquery */
(function($) {
$(function() {
    $('#portal-searchfacets dl').showMore({
        expression: 'dt:gt(4), dd:gt(4)',
        grace_count: 2
    });
});
})(jQuery);