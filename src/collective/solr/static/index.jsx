import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';
import 'whatwg-fetch';

class SearchApp extends React.Component {
  constructor(){
    super();
    this.state={
      searchText: '',
      results: {},
      portalUrl: document.getElementById('container').dataset.portalurl
    };
  }

  handleUserInput(searchTerm){
    this.setState({searchText:searchTerm});
    // Make the request
    let requestHeaders = new Headers();
    requestHeaders.append("Accept", "application/json");
    fetch(`${this.state.portalUrl}/search?metadata_fields=Creator&metadata_fields=modified&SearchableText=` + searchTerm,
          {headers: requestHeaders, mode: 'cors'})
      .then((response) => response.json())
      .then((responseData) => {
        this.setState({results: responseData});
      })
      .catch((error) => {
        console.log('Error fetching and parsing data', error);
      })
  }

  render() {
    return (
      <div>
        <SearchBox searchText={this.state.searchText}
                   onUserInput={this.handleUserInput.bind(this)} />
        <SearchResults results={this.state.results}
                       searchText={this.state.searchText} />
      </div>
    )
  }
}
// SearchApp.propTypes = {
//   results: PropTypes.arrayOf(PropTypes.object)
// }


class SearchBox extends React.Component {
  handleChange(event){
    this.props.onUserInput(event.target.value)
  }

  render() {
    return (
      <div>
        <div className="input-group">
          <input className="searchPage form-control"
                 name="SearchableText"
                 type="text"
                 size="25"
                 title="Search Site"
                 placeholder="Search"
                 value={this.props.searchText}
                 onChange={this.handleChange.bind(this)}
                 />
          <span className="input-group-btn">
            <input className="searchPage allowMultiSubmit btn btn-primary" type="submit"
                   value="Search" />
          </span>
        </div>
      </div>
    );
  }
}

SearchBox.propTypes = {
  onUserInput: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired
}

class SearchResults extends React.Component {
  render() {
    let resultList, noResultsFound;
    noResultsFound = (
      <p><strong>No results were found.</strong></p>
    )
    if (this.props.results.hasOwnProperty('member')) {
      resultList = this.props.results.member;
      if (this.props.results.items_count > 0) {
        noResultsFound = ''
      } else {
        noResultsFound = (
          <p><strong>No results were found.</strong></p>
        )
      }
    } else {
      resultList = []
    };
    let searchTitle;
    if (this.props.searchText) {
      searchTitle = (
        <strong id="search-term">
          {this.props.searchText}
        </strong>
      )
    }

    return (
      <div>
        <div>
          <h1 className="documentFirstHeading">
            Search results { searchTitle ? 'for': null} { searchTitle }
          </h1>
        </div>
        <div id="search-results-wrapper">
          <div id="search-results-bar">
            <span id="results-count"><strong id="search-results-number">{this.props.results.items_count || 0}</strong> items matching your search terms.</span>
          </div>
          <div className="autotabs">
            <nav className="autotoc-nav" id="searchResultsSort">
              <span className="autotab-heading">Sort by</span>
              <span id="sorting-options">
                <a href="http://localhost:8080/Plone2/@@search?sort_on=" data-order="" className="active">relevance</a>
                <a data-sort="Date" href="http://localhost:8080/Plone2/@@search?sort_on=Date&amp;sort_order=reverse" data-order="reverse" className="">date (newest first)</a>
                <a data-sort="sortable_title" href="http://localhost:8080/Plone2/@@search?sort_on=sortable_title" data-order="" className="">alphabetically</a>
              </span>
            </nav>
            <div id="search-results">
              {noResultsFound}
                <ol className="searchResults">
                  {resultList.map(
                    (item) => <SearchResultItem key={item['@id']}
                                                id={item['@id']}
                                                title={item.title}
                                                description={item.description}
                                                author={item.Creator}
                                                modified={item.modified} />
                  )}
                </ol>

            </div>
          </div>
        </div>
      </div>
    )
  }
}
SearchResults.propTypes = {
  results: PropTypes.object,
  searchText: PropTypes.string.isRequired
}

class SearchResultItem extends React.Component {
  render() {
    return (
      <li>
        <span className="result-title">
          <a href={this.props.id} className="state-published">{this.props.title}</a>
        </span>{" "}
        <span className="discreet">
          <span className="documentAuthor">by <a href="http://localhost:8080/Plone2/author/admin">admin</a></span>
          <span>
            <span class="documentModified">
              —
              <span>last modified {" "}</span>
              {this.props.modified}
            </span>
          </span>
        </span>
        <p className="discreet croppedDescription">{this.props.description}</p>
      </li>
    )
  }
}
SearchResultItem.propTypes = {
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired
}

ReactDOM.render(
  <SearchApp />,
  document.getElementById("container")
)
