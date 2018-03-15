import React, { Component } from 'react';
import { connect } from 'react-redux';

import SearchBox from './SearchBox';
import SearchResults from './SearchResults';
import Filters from './Filters';

class Search extends Component {
  render() {
    const isEmpty = this.props.results.length === 0;

    return (
      <div className="row" style={{ marginTop: '30px' }}>
        <section className="col-lg-3 col-md-4 col-xs-12 side-bar">
          <form id="" method="" action="" className="filter-block">
            <SearchBox />
            <Filters />
          </form>
        </section>
        <section
          id="main-content"
          className="col-lg-9 col-md-8 col-xs-12 main-content"
        >
          <div className="tab-content">
            {isEmpty ? (
              <h3 style={{ marginTop: '10px' }}>Keine Ergebnisse</h3>
            ) : (
              <div
                style={{ opacity: this.props.loaded ? 1 : 0 }}
                className="fade"
              >
                <SearchResults />
              </div>
            )}
          </div>
        </section>
      </div>
    );
  }
}

export default connect(
  (state, props) => ({
    results: state.search.items,
    loaded: state.search.loaded,
  }),
  {},
)(Search);

// <div style={{ opacity: isFetching ? 0 : 1 }} className="fade">
