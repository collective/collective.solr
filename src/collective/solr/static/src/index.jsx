import React, { PropTypes } from "react";
import ReactDOM from "react-dom";
import "whatwg-fetch";
import "babel-polyfill";
import update from "react-addons-update";
import moment from "moment";
import {DebounceInput} from 'react-debounce-input';

class SearchApp extends React.Component {
  constructor() {
    super();
    this.state = {
      searchText:
        this.getParams(window.location.href.split("?")[1])["SearchableText"] ||
        "",
      results: {},
      portalUrl: document.getElementById("container").dataset.portalurl,
      sortOn: "relevance",
      filter: ""
    };
  }

  getParams = query => {
    if (!query) {
      return {};
    }

    return (/^[?#]/.test(query) ? query.slice(1) : query)
      .split("&")
      .reduce((params, param) => {
        let [key, value] = param.split("=");
        params[key] = value
          ? decodeURIComponent(value.replace(/\+/g, " "))
          : "";
        return params;
      }, {});
  };

  componentWillMount() {
    if (this.state.searchText !== "") {
      this.doSearchRequest({ searchText: this.state.searchText });
    }
  }
  // TODO: The query build should be improved and bypass the fact that the state
  // does not change immediately on setState.

  handleUserInput(searchTerm) {
    this.setState({ searchText: searchTerm });
    const searchOptions = {
      searchText: searchTerm,
      sortOn: this.state.sortOn,
      filter: this.state.filter
    };
    // Catch the case where the search term is empty, return 0 results without contact the server
    if (searchTerm === "") {
      this.setState({
        results: {
          items_total: 0,
          items: []
        }
      });
    } else {
      this.doSearchRequest(searchOptions);
    }
  }

  handleUserChangeSortOn(sortOn) {
    this.setState({ sortOn: sortOn });
    const searchOptions = {
      searchText: this.state.searchText,
      sortOn: sortOn,
      filter: this.state.filter
    };
    this.doSearchRequest(searchOptions);
  }

  handleUserChangeFilter(filter) {
    this.setState({ filter: filter });
    const searchOptions = {
      searchText: this.state.searchText,
      sortOn: this.state.sortOn,
      filter: filter
    };
    this.doSearchRequest(searchOptions);
  }

  doSearchRequest(searchOptions) {
    // Prepare sort_on cases
    let sortonQuery;
    switch (searchOptions.sortOn) {
      case "relevance":
        sortonQuery = "&sort_on=";
        break;
      case "date":
        sortonQuery = "&sort_on=Date&sort_order=reverse";
        break;
      case "sortable_title":
        sortonQuery = "&sort_on=sortable_title";
        break;
      default:
        sortonQuery = "&sort_on=";
    }

    // Add the filter query if present
    let filterQuery = searchOptions.filter ? searchOptions.filter : "";

    // Make the request
    let requestHeaders = new Headers();
    requestHeaders.append("Accept", "application/json");
    fetch(
      `${
        this.state.portalUrl
      }/@search?metadata_fields=Creator&metadata_fields=modified${sortonQuery}${filterQuery}&SearchableText=${
        searchOptions.searchText
      }`,
      {
        headers: requestHeaders,
        mode: "cors",
        credentials: "same-origin"
      }
    )
      .then(response => response.json())
      .then(responseData => {
        this.setState({ results: responseData });
      })
      .catch(error => {
        console.log("Error fetching and parsing data", error);
      });
  }
  render() {
    return (
      <div>
        <SearchBox
          searchText={this.state.searchText}
          onUserInput={this.handleUserInput.bind(this)}
        />
        <UserFilter
          onUserChangeFilter={this.handleUserChangeFilter.bind(this)}
        />
        <SearchResults
          results={this.state.results}
          searchText={this.state.searchText}
          onUserChangeSortOn={this.handleUserChangeSortOn.bind(this)}
        />
      </div>
    );
  }
}

class SearchBox extends React.Component {
  handleChangeSearchString(event) {
    this.props.onUserInput(event.target.value);
  }

  render() {
    return (
      <div id="searchform">
        <div className="input-group">
          <DebounceInput
            minLength={3}
            debounceTimeout={400}
            className="searchPage form-control"
            name="SearchableText"
            type="text"
            size="25"
            title="Search Site"
            placeholder="Search"
            autocomplete="off"
            value={this.props.searchText}
            onChange={this.handleChangeSearchString.bind(this)}
          />
          <span className="input-group-btn">
            <input
              className="searchPage allowMultiSubmit btn btn-primary"
              type="submit"
              value="Search"
            />
          </span>
        </div>
      </div>
    );
  }
}

SearchBox.propTypes = {
  onUserInput: PropTypes.func.isRequired,
  searchText: PropTypes.string.isRequired
};

class UserFilter extends React.Component {
  constructor() {
    super();
    this.state = {
      show_filters: false,
      selectAllToggle: true,
      contentTypes: [
        {
          id: "0",
          checked: true,
          name: "Collection",
          displayName: "Collection"
        },
        { id: "1", checked: true, name: "Document", displayName: "Page" },
        { id: "2", checked: true, name: "Folder", displayName: "Folder" }
      ],
      created: "1970-01-02",
      radio_checked: "ever"
    };
  }

  handleChangeTypesFilter(filterId, event) {
    // Manage state change
    const typeIndex = this.state.contentTypes.findIndex(
      type => type.id === filterId
    );
    let nextState;
    if (this.state.contentTypes[typeIndex].checked === true) {
      nextState = update(this.state.contentTypes, {
        [typeIndex]: { $merge: { checked: false } }
      });
      this.setState({ contentTypes: nextState });
    } else {
      nextState = update(this.state.contentTypes, {
        [typeIndex]: { $merge: { checked: true } }
      });
      this.setState({ contentTypes: nextState });
    }
    this.props.onUserChangeFilter(
      this.buildFilterQueryString(nextState, this.state.created)
    );
  }
  handleChangeCreatedFilter(date, event) {
    this.setState({
      created: date,
      radio_checked: event.target.id.replace("query-date-", "")
    });
    // Build query string
    this.props.onUserChangeFilter(
      this.buildFilterQueryString(this.state.contentTypes, date)
    );
  }

  buildFilterQueryString(typesString, created) {
    // Build query string
    let checkedTypesString = "";
    for (let item of typesString) {
      if (item.checked === true) {
        checkedTypesString = checkedTypesString + `&portal_type=${item.name}`;
      }
    }
    return `${checkedTypesString}&created.query=${created}&created.range=min`;
  }

  handleShowFilters(event) {
    this.setState({ show_filters: !this.state.show_filters });
  }

  selectAllToggle(event) {
    let nextState;
    nextState = update(this.state, {
      selectAllToggle: { $set: false }
    });

    if (this.state.selectAllToggle === true) {
      nextState = update(this.state, {
        selectAllToggle: { $set: false }
      });
      for (let type of nextState.contentTypes) {
        type.checked = false;
      }
    } else {
      nextState = update(this.state, {
        selectAllToggle: { $set: true }
      });
      for (let type of nextState.contentTypes) {
        type.checked = true;
      }
    }
    this.setState({
      contentTypes: nextState.contentTypes,
      selectAllToggle: nextState.selectAllToggle
    });

    this.props.onUserChangeFilter(
      this.buildFilterQueryString(nextState.contentTypes, nextState.created)
    );
  }

  render() {
    return (
      <dl
        className={
          this.state.show_filters ? "actionMenu activated" : "actionMenu"
        }
      >
        <dt className="actionMenuHeader">
          <button
            id="search-filter-toggle"
            onClick={this.handleShowFilters.bind(this)}
          >
            Filter the results
          </button>
        </dt>
        <dd className="actionMenuContent">
          <div id="search-filter">
            <fieldset className="noborder">
              <legend>Item type</legend>
              <div className="field">
                <div className="optionsToggle">
                  <input
                    type="checkbox"
                    name="pt_toggle"
                    value="#"
                    id="pt_toggle"
                    className="noborder"
                    checked={this.state.selectAllToggle}
                    onClick={this.selectAllToggle.bind(this)}
                  />
                  <label htmlFor="pt_toggle">Select All/None</label>
                </div>
                <div className="search-type-options">
                  {/* Static types to search
                    TODO: get them from a backend call */}
                  {this.state.contentTypes.map(item => (
                    <div key={item.id}>
                      <input
                        type="checkbox"
                        name="portal_type"
                        className="noborder"
                        id={`query-portaltype-${item.name}`}
                        checked={item.checked}
                        value={item.displayName}
                        onChange={this.handleChangeTypesFilter.bind(
                          this,
                          item.id
                        )}
                      />
                      <label htmlFor="">{item.displayName}</label>
                    </div>
                  ))}
                </div>
              </div>
            </fieldset>
            <fieldset className="noborder">
              <legend>New items since</legend>
              <div className="field">
                <div className="search-date-options">
                  <div>
                    <input
                      type="radio"
                      id="query-date-yesterday"
                      name="created"
                      checked={this.state.radio_checked === "yesterday"}
                      onChange={this.handleChangeCreatedFilter.bind(
                        this,
                        moment()
                          .subtract(1, "days")
                          .format("YYYY-MM-DD")
                      )}
                    />
                    <label htmlFor="query-date-yesterday">Yesterday</label>
                  </div>
                  <div>
                    <input
                      type="radio"
                      id="query-date-last_week"
                      name="created"
                      checked={this.state.radio_checked === "last_week"}
                      onChange={this.handleChangeCreatedFilter.bind(
                        this,
                        moment()
                          .subtract(1, "weeks")
                          .format("YYYY-MM-DD")
                      )}
                    />
                    <label htmlFor="query-date-lastweek">Last week</label>
                  </div>
                  <div>
                    <input
                      type="radio"
                      id="query-date-last_month"
                      name="created"
                      checked={this.state.radio_checked === "last_month"}
                      onChange={this.handleChangeCreatedFilter.bind(
                        this,
                        moment()
                          .subtract(1, "months")
                          .format("YYYY-MM-DD")
                      )}
                    />
                    <label htmlFor="query-date-lastmonth">Last month</label>
                  </div>
                  <div>
                    <input
                      type="radio"
                      id="query-date-ever"
                      name="created"
                      checked={this.state.radio_checked === "ever"}
                      onChange={this.handleChangeCreatedFilter.bind(
                        this,
                        "1970-01-02"
                      )}
                    />
                    <label htmlFor="query-date-ever">Ever</label>
                  </div>
                </div>
                <input type="hidden" name="created.range:record" value="min" />
              </div>
            </fieldset>
          </div>
        </dd>
      </dl>
    );
  }
}

UserFilter.propTypes = {
  onUserChangeFilter: PropTypes.func.isRequired
};

class SearchResults extends React.Component {
  constructor() {
    super();
    this.state = {
      active_tab: "relevance",
    };
  }

  handleChangeSortOn(event) {
    this.setState({ active_tab: event.target.dataset.sort });
    this.props.onUserChangeSortOn(event.target.dataset.sort);
    event.preventDefault();
  }

  render() {
    let resultList;
    let noResultsFound;
    noResultsFound = (
      <p>
        <strong>No results were found.</strong>
      </p>
    );
    if (this.props.results.hasOwnProperty("items")) {
      resultList = this.props.results.items;
      if (this.props.results.items_total > 0) {
        noResultsFound = "";
      } else {
        noResultsFound = (
          <p>
            <strong>No results were found.</strong>
          </p>
        );
      }
    } else {
      resultList = [];
    }

    let searchTitle;
    if (this.props.searchText) {
      searchTitle = <strong id="search-term">{this.props.searchText}</strong>;
    }

    return (
      <div>
        <div>
          <h1 className="documentFirstHeading">
            Search results {searchTitle ? "for" : null} {searchTitle}
          </h1>
        </div>
        <div id="search-results-wrapper">
          <div id="search-results-bar">
            <span id="results-count">
              <strong id="search-results-number">
                {this.props.results.items_total || 0}
              </strong>{" "}
              items matching your search terms.
            </span>
          </div>
          <div className="autotabs">
            <nav className="autotoc-nav" id="searchResultsSort">
              <span className="autotab-heading">Sort by</span>
              <span id="sorting-options">
                <a
                  href="#"
                  data-sort="relevance"
                  data-order=""
                  className={
                    this.state.active_tab === "relevance" ? "active" : null
                  }
                  onClick={this.handleChangeSortOn.bind(this)}
                >
                  relevance
                </a>
                <a
                  href="#"
                  data-sort="date"
                  data-order="reverse"
                  className={this.state.active_tab === "date" ? "active" : null}
                  onClick={this.handleChangeSortOn.bind(this)}
                >
                  date (newest first)
                </a>
                <a
                  href="#"
                  data-sort="sortable_title"
                  data-order=""
                  className={
                    this.state.active_tab === "sortable_title" ? "active" : null
                  }
                  onClick={this.handleChangeSortOn.bind(this)}
                >
                  alphabetically
                </a>
              </span>
            </nav>
            <div id="search-results">
              {noResultsFound}
              <ol className="searchResults">
                {resultList.map(item => (
                  <SearchResultItem
                    key={item["@id"]}
                    id={item["@id"]}
                    title={item.title}
                    description={item.description}
                    author={item.Creator}
                    modified={item.modified}
                  />
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
SearchResults.propTypes = {
  results: PropTypes.object,
  searchText: PropTypes.string.isRequired,
  onUserChangeSortOn: PropTypes.func.isRequired
};

class SearchResultItem extends React.Component {
  render() {
    return (
      <li>
        <span className="result-title">
          <a href={this.props.id} className="state-published">
            {this.props.title}
          </a>
        </span>{" "}
        <span className="discreet">
          <span className="documentAuthor">
            by{" "}
            <a
              href={`${
                document.getElementById("container").dataset.portalurl
              }/author/${this.props.author}`}
            >
              {this.props.author}
            </a>
          </span>
          <span>
            <span className="documentModified">
              —
              <span>last modified </span>
              {this.props.modified}
            </span>
          </span>
        </span>
        <p className="discreet croppedDescription">{this.props.description}</p>
      </li>
    );
  }
}
SearchResultItem.propTypes = {
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  modified: PropTypes.string.isRequired,
  author: PropTypes.string.isRequired
};

ReactDOM.render(<SearchApp />, document.getElementById("container"));
