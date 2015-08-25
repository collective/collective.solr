/*jshint strict: true, undef: true, unused: true*/
/*global $,jQuery*/
/* use `collective.js.showmore` to hide facet counts via jquery */

/*(function ($) {
  "use strict";
  $('#portal-searchfacets dl').showMore({
    expression: 'dt:gt(4), dd:gt(4)',
    grace_count: 2
  });
}(jQuery));*/


$(document).ready(function() {
    var x = new SolrTypeaheadSearch();
});


var SolrTypeaheadSearch = function(){
    var self = this;

    //Init typeahead plugin
    self.solrAutocompleteSearch = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {
            url: '@@solr-autocomplete?format=json&term=%QUERY',
            wildcard: '%QUERY'
        }
    });

    $('#solr-autocomplete .typeahead').typeahead(null, {
        name: 'autocomplete-search',
        display: 'value',
        source: self.solrAutocompleteSearch
    }).on('typeahead:selected', function(e){
        self.query();
    });

    $('#SearchableText').keypress(function (e) {
        var key = e.which;
        if(key == 13) {
            $('#solr-submit').focus();
            self.query();
        }
    });



    // Executes query to Solr
    self.query = function(url){
        var SearchableText = $('#SearchableText').val();
        if (!url)
            url = self.buildURL(null);
        $.getJSON(url, self.renderSearchResult);
    };

    // Builds url for query
    self.buildURL = function(startIndex){
        var SearchableText = $('#SearchableText').val();
        var url = '@@search?format=json&SearchableText=' + SearchableText;

        if (startIndex)
            url += '&b_start:int=' + startIndex;

        return url;
    };

    $('#solr-submit').click(function(event) {
        self.query();
    });

    // Renders search page based on results
    self.renderSearchResult = function(items) {
        $(".searchResults").html(self.getResultsListHTML(items));
        $('#search-results-number').html(items.totalItems);
        $( "#solr-suggestion").html(self.getSuggestionsHTML(items));
        $('.listingBar').html(self.getBatchingBarHTML(items));

        // After render events binding
        $('.suggestion').click(function(event){
            var searchText = "";
            $(this).find("span").each(function(){
                searchText += $(this).text();
            });
            $('#SearchableText').val(searchText);
            self.query();
        });

        $('.solr-batching').click(function(event){
           event.preventDefault();
           var url = $(this).attr('href');
           self.query(url);
        });
    };

    // Creates batching bar HTML
    self.getBatchingBarHTML = function(items) {
        var outputHTML = "";

        var prevPageStart = items.startIndex - items.itemsPerPage;
        var nextPageStart = items.startIndex + items.itemsPerPage;
        var countOfBatches = Math.ceil(items.totalItems / items.itemsPerPage) + 1;
        var currentPageIndex = Math.ceil(items.startIndex / items.itemsPerPage) + 1;


        if (prevPageStart >= 0) {
          outputHTML += '<a class="previous solr-batching" ' +
                            "href='" +
                            self.buildURL(prevPageStart) +
                            "'> Previous " +
                             + items.itemsPerPage +
                        ' items</a>';
        }

        if (nextPageStart < items.totalItems) {
          outputHTML += '<a class="next solr-batching" ' +
                           "href='" +
                            self.buildURL(nextPageStart) +
                            "'> Next " +
                             + items.itemsPerPage +
                        ' items</a>';
        }

        for (var i = 1 ; i < countOfBatches ; i++){
            var pageStartIndex = (i - 1) * items.itemsPerPage;

            if(i == currentPageIndex)
                outputHTML += '[<span>'+ i +'</span>]';
            else
                outputHTML += "<a class='solr-batching' href='"
                   + '@@search?b_start:int=' + pageStartIndex +
                   '&format=json&SearchableText=' + $('#SearchableText').val() + "'>" + i + "</a>";
        }

        return outputHTML;
    };

    // Creates suggestions html
    self.getSuggestionsHTML = function(items){
        var SearchableText = $('#SearchableText').val();

        var outputHTML = "";

        if (items.suggestions) {
            for (var key in items.suggestions)
                var queryWithNoSuggestion = SearchableText.toLowerCase().split(key);
                var suggestionData = items.suggestions[key];

                if (suggestionData &&
                    suggestionData["suggestion"].length > 0 &&
                    queryWithNoSuggestion.length > 1) {

                    var suggestion = suggestionData["suggestion"][0];
                    outputHTML += "<span class='suggestion-title'>Meinten Sie: </span>" +
                        "<span class='suggestion'>" +
                          "<span class='pref'>" + queryWithNoSuggestion[0] + "</span>" +
                          "<span class='sugg'>" + suggestion + "</span>" +
                          "<span class='suff'>" + queryWithNoSuggestion[1] + "</span>" +
                        "</span>";
                }
        };
        return outputHTML;
    };

    // Creates results list HTML
    self.getResultsListHTML = function(items){
        var outputHTML = "";
        console.log(items);
        for (item_key in items.member){
          var item = items.member[item_key];
          var searchResult =
                "<dt class='contenttype-" + item.portal_type.toLowerCase().replace(" ", "-") + "'>" +
                  "<a href='" + item.url + "' class='state-None'>" + item.title + "</a>" +
                "</dt>" +
                "<dd>" +
                  "<span class='discreet'>" +
                    "<span class='documentAuthor'>erstellt von " +
                      "<a href='" + item.author_url + "'>" + item.author + "</a>" +
                    "</span>" +
                    "<span>" +
                      "<span class='documentPublished'> - " +
                        "<span>Veröffentlicht </span>" +
                          item.publish_date +
                        "</span>" +
                        "<span class='documentModified'> - " +
                          "<span>zuletzt verändert: </span>" +
                          item.last_modified +
                        "</span>" +
                    "</span>" +
                  "</span>" +
                  "<div>" + item.description + "</div>" +
                "</dd>";
              outputHTML += searchResult;
          }
        return outputHTML;
    };

};