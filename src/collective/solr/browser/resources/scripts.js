/*jshint strict: true, undef: true, unused: true*/
/*global $,jQuery*/
/* use `collective.js.showmore` to hide facet counts via jquery */
(function ($) {
  "use strict";
  $('#portal-searchfacets dl').showMore({
    expression: 'dt:gt(4), dd:gt(4)',
    grace_count: 2
  });
}(jQuery));
