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
    var solrAutocompleteSearch = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {
            url: '@@solr-autocomplete?format=json&term=%QUERY',
            wildcard: '%QUERY'
        }
    });

    var x = new SolrTypeaheadSearchBatching(solrAutocompleteSearch);
    var z = new SolrTypeaheadSearchIScroll(solrAutocompleteSearch);
    var y = new SolrTypeahedSearchViewlet(solrAutocompleteSearch);
});


var LOADING_SPINNER = '<div class="spinner"><div class="bounce1"></div>' +
    '<div class="bounce2"></div><div class="bounce3"></div></div>';

var SolrTypeahedSearchViewlet = function(solrAutocompleteSearch){
    var self = this;
    self.solrAutocompleteSearch = solrAutocompleteSearch;

    $('#SearchableTextViewlet').typeahead(null, {
        name: 'autocomplete-search-viewlet',
        display: 'value',
        source: self.solrAutocompleteSearch
    }).on('typeahead:selected', function(e){
        $('#to-solr-page')[0].click();
    });

    $('#to-solr-page').click(function(){
       var curHref = $(this).attr("href");
       var SearchableText = $('#SearchableTextViewlet').val();
       $(this).attr('href', curHref + SearchableText);
    });

    $('#SearchableTextViewlet').keypress(function (e) {
        var key = e.which;
        if(key == 13) {
            $('#to-solr-page')[0].click();
        }
    });

};


var SolrTypeaheadSearchBatching = function(solrAutocompleteSearch){
    var self = this;

    //Init typeahead plugin
    self.solrAutocompleteSearch = solrAutocompleteSearch;

    $('#SearchableText').typeahead(null, {
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

    self.initinalize = function(){
        var urlQuery = $('#solr-url-query').text();
        if (urlQuery){
            $('#SearchableText').typeahead('val', urlQuery);
            self.query();
        }
    };

    // Executes query to Solr
    self.query = function(url){
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

            if (i == currentPageIndex) {
                outputHTML += '[<span>' + i + '</span>]';
                continue;
            }

            if (i == 2 && currentPageIndex - 3 >= 2) {
                outputHTML += "<span>  ...  </span>";
                continue;
            }
            if (i == countOfBatches - 2 && currentPageIndex + 3 <= countOfBatches - 2) {
                outputHTML += "<span>  ...  </span>";
                continue;
            }

            if (i == 1 || i == countOfBatches - 1 || (i - 3 < currentPageIndex && i + 3 > currentPageIndex))
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
                    suggestionData["suggestion"].length > 0) {
                    var suggestion = suggestionData["suggestion"][0];
                    if (queryWithNoSuggestion.length == 2) {
                        outputHTML += "<span class='suggestion-title'>Meinten Sie: </span>" +
                            "<span class='suggestion'>" +
                            "<span class='pref'>" + queryWithNoSuggestion[0] + "</span>" +
                            "<span class='sugg'>" + suggestion + "</span>" +
                            "<span class='suff'>" + queryWithNoSuggestion[1] + "</span>" +
                            "</span>";
                    }
                    else
                        outputHTML +="<span class='suggestion-title'>Meinten Sie: </span>" +
                            "<span class='suggestion'>" +
                            "<span class='sugg'>" + suggestion + "</span>" +
                            "</span>";
                }
        };
        return outputHTML;
    };

    // Creates results list HTML
    self.getResultsListHTML = function(items){
        var outputHTML = "";
        for (item_key in items.member){
          var item = items.member[item_key];
          var searchResult =
                "<dt class='contenttype-" + item.portal_type.toLowerCase().replace(" ", "-") + "'>" +
                  "<a href='" + item.url + "' class='state-None'>" + item.title + "</a>" +
                "</dt>" +
                "<dd>" +
                  "<span class='discreet'>" +
                    "<span class='documentAuthor'>erstellt von " +
                      "<a href='" + item.author_url + "'>" + item.creator + "</a>" +
                    "</span>" +
                    "<span>" +
                      "<span class='documentPublished'> - " +
                        "<span>Veröffentlicht </span>" +
                          item.effective +
                        "</span>" +
                        "<span class='documentModified'> - " +
                          "<span>zuletzt verändert: </span>" +
                          item.modified +
                        "</span>" +
                    "</span>" +
                  "</span>" +
                  "<div>" + item.description + "</div>" +
                "</dd>";
              outputHTML += searchResult;
          }
        return outputHTML;
    };

    self.initinalize();

};


var SolrTypeaheadSearchIScroll = function(solrAutocompleteSearch){
    var self = this;

    //Init typeahead plugin
    self.solrAutocompleteSearch = solrAutocompleteSearch;

    $('#SearchableTextIScroll').typeahead(null, {
        name: 'autocomplete-search-iscroll',
        display: 'value',
        source: self.solrAutocompleteSearch
    }).on('typeahead:selected', function(e){
        self.query(null, true);
    });

    $('#SearchableTextIScroll').keypress(function (e) {
        var key = e.which;
        if(key == 13) {
            $('#solr-submit').focus();
            self.query(null, true);
        }
    });

    self.initinalize = function(){
        var urlQuery = $('#solr-url-query').text();
        if (urlQuery){
            $('#SearchableTextIScroll').typeahead('val', urlQuery);
            self.query(null, true);
        }
    };

    // Executes query to Solr
    self.query = function(url, isNewQuery){
        $('#iscroll-next-container').html(LOADING_SPINNER);

        if (!url)
            url = self.buildURL(null);
        $.getJSON(url).then(function(data){
            self.renderSearchResult(data, isNewQuery)
        });
    };

    // Builds url for query
    self.buildURL = function(startIndex){
        var SearchableText = $('#SearchableTextIScroll').val();
        var url = '@@search?format=json&SearchableText=' + SearchableText;

        if (startIndex)
            url += '&b_start:int=' + startIndex;

        return url;
    };

    $('#solr-submit-iscroll').click(function(event) {
        self.query(null, true);
    });

    // Renders search page based on results
    self.renderSearchResult = function(items, isNewQuery) {
        if (isNewQuery)
            $(".searchResults").html("");
        $(".searchResults").append(self.getResultsListHTML(items));

        if ($(document).height() < $(window).height()){
            var nextPageStart = items.startIndex + items.itemsPerPage;
            if (nextPageStart < items.totalItems)
                self.query(self.buildURL(nextPageStart), false);
        }

        $(window).off("scroll").scroll(function(){
            if($(window).scrollTop() == $(document).height() - $(window).height()) {
                var nextPageStart = items.startIndex + items.itemsPerPage;
                if (nextPageStart < items.totalItems)
                    self.query(self.buildURL(nextPageStart), false);
            }
        });

        $('#iscroll-next-container').html(self.getNextButtonHTML(items));

        $('#iscroll-next').click(function(event){
           event.preventDefault();
           var url = $(this).attr('href');
           self.query(url, false);
        });

        $('#iscroll-to-top').click(function(event){
           event.preventDefault();
           $("html, body").animate({ scrollTop: 0 }, 400);
        });

        if (!isNewQuery)
            return;


        $('#search-results-number').html(items.totalItems);
        $( "#solr-suggestion").html(self.getSuggestionsHTML(items));

        // After render events binding
        $('.suggestion').click(function(event){
            var searchText = "";
            $(this).find("span").each(function(){
                searchText += $(this).text();
            });
            $('#SearchableTextIScroll').val(searchText);
            self.query(null, true);
        });

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
                    suggestionData["suggestion"].length > 0) {
                    var suggestion = suggestionData["suggestion"][0];
                    if (queryWithNoSuggestion.length == 2) {
                        outputHTML += "<span class='suggestion-title'>Meinten Sie: </span>" +
                            "<span class='suggestion'>" +
                            "<span class='pref'>" + queryWithNoSuggestion[0] + "</span>" +
                            "<span class='sugg'>" + suggestion + "</span>" +
                            "<span class='suff'>" + queryWithNoSuggestion[1] + "</span>" +
                            "</span>";
                    }
                    else
                        outputHTML +="<span class='suggestion-title'>Meinten Sie: </span>" +
                            "<span class='suggestion'>" +
                            "<span class='sugg'>" + suggestion + "</span>" +
                            "</span>";
                }
        };
        return outputHTML;
    };

    // Creates results list HTML
    self.getResultsListHTML = function(items){
        var outputHTML = "";
        for (item_key in items.member){
          var item = items.member[item_key];
          var searchResult =
                "<dt class='contenttype-" + item.portal_type.toLowerCase().replace(" ", "-") + "'>" +
                  "<a href='" + item.url + "' class='state-None'>" + item.title + "</a>" +
                "</dt>" +
                "<dd>" +
                  "<span class='discreet'>" +
                    "<span class='documentAuthor'>erstellt von " +
                      "<a href='" + item.author_url + "'>" + item.creator + "</a>" +
                    "</span>" +
                    "<span>" +
                      "<span class='documentPublished'> - " +
                        "<span>Veröffentlicht </span>" +
                          item.effective +
                        "</span>" +
                        "<span class='documentModified'> - " +
                          "<span>zuletzt verändert: </span>" +
                          item.modified +
                        "</span>" +
                    "</span>" +
                  "</span>" +
                  "<div>" + item.description + "</div>" +
                "</dd>";
              outputHTML += searchResult;
          }
        return outputHTML;
    };

    self.getNextButtonHTML = function(items){
        var outputHTML = "";
        if (items.startIndex + items.itemsPerPage < items.totalItems)
            outputHTML += "<a id='iscroll-next' href='" +
                self.buildURL(items.startIndex + items.itemsPerPage) +
                "'>Next 10 items</a>"
        else if ($(document).height() > $(window).height())
            outputHTML += "<a id='iscroll-to-top' href='#'>To The Top</a>";


        return outputHTML;
    };

    self.initinalize();

};