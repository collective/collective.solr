require([
    'jquery',
    'mockup-patterns-base',
    'pat-registry'
], function($, Base, Registry) {
    'use strict';
    var Search = Base.extend({
        name: 'Search',
        trigger: '.search-block',
        defaults: {},
        init: function() {
            var self = this;
            debugger
            self.id = self.$el.attr('name');

        },
    });
    return Search;
});
