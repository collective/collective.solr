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
    });

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

    self.query = function(){
        var SearchableText = $('#SearchableText').val();
        var url = '@@search?format=json&SearchableText=' + SearchableText;
        $.getJSON(url, self.renderSearchResult);
    };


    $('#solr-submit').click(function(event) {
        self.query();
    });

    self.renderBatchingBar = function(items) {
        var outputHTML = "";
        position = 0;
        if (items.previousPage) {
          outputHTML += '<a class="previous" ' +
                            "href='" + items.previousPage + "'> Previous " +
                             + items.itemsPerPage +
                        ' items</a>';
        }

        if (items.nextPage) {
          outputHTML += '<a class="next" ' +
                            "href='" + items.nextPage + "'> Next " +
                             + items.itemsPerPage +
                        ' items</a>';
        }

        var countOfBatches = Math.ceil(items.totalItems / items.itemsPerPage);

        for(var i = 1 ; i < countOfBatches ; i++){
            if(i * items.itemsPerPage == position + items.itemsPerPage){
                outputHTML += '[<span>'+ i +'</span>]';
            }
            else{
                outputHTML += '<a href="#">' + i + '</a>';
            }
        };
        return outputHTML;
     };

     self.renderSearchResult = function(items) {
        $(".searchResults").html(self.getResultsListHTML(items));
        $('#search-results-number').html((items.member) ? items.member.length : 0);
        $( "#solr-suggestion").html(self.getSuggestionsHTML(items));
        $('.listingBar').html(self.renderBatchingBar(items));

        $('.suggestion').click(function(event){
            var searchText = "";
            $(this).find("span").each(function(){
                searchText += $(this).text();
            });
            $('#SearchableText').val(searchText);
            self.query();
        });
    };



};