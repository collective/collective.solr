import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';

class SearchApp extends React.Component {
  constructor(){
    super();
    this.state={
      searchText: ''
    };
  }

  handleUserInput(searchTerm){
    this.setState({searchText:searchTerm})
  }

  render() {
    return (
      <div>
        <SearchBox searchText={this.state.searchText}
                   onUserInput={this.handleUserInput.bind(this)} />
        <SearchResults results={this.props.results}
                       searchText={this.state.searchText} />
      </div>
    )
  }
}
SearchApp.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object)
}


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
    let filteredContacts = this.props.results.filter(
      (result) => result.title.indexOf(this.props.searchText) !== -1
    );
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
            <span id="results-count"><strong id="search-results-number">0</strong> items matching your search terms.</span>
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
              <p><strong>No results were found.</strong></p>

                <ul>
                  {filteredContacts.map(
                    (item) => <SearchResultItem key={item.id}
                                                id={item.id}
                                                title={item.title} />
                  )}
                </ul>

            </div>
          </div>
        </div>
      </div>
    )
  }
}
SearchResults.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object),
  searchText: PropTypes.string.isRequired
}

class SearchResultItem extends React.Component {
  render() {
    return (
      <li>{this.props.id} - {this.props.title}</li>
    )
  }
}
SearchResultItem.propTypes = {
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired
}

let results = [
  { id: '1', title: 'Colorless green ideas sleep furiously'},
  { id: '2', title: 'Furiously sleep ideas green colorless'}
]


ReactDOM.render(
  <SearchApp results={results} />,
  document.getElementById("container")
)
