import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

class SearchResults extends Component {
  static propTypes = {
    results: PropTypes.array,
  };

  static defaultProps = {
    results: [],
  };

  render() {
    const { results } = this.props;

    return (
      <ol className="list-sections list-events">
        {results.map((result, i) => (
          <li key={i}>
            <a href={result.getURL}>
              <h2 className="event-title">{result.title}</h2>
              <p className="event-description">{result.description}</p>
            </a>
          </li>
        ))}
      </ol>
    );
  }
}

export default connect(
  state => ({
    results: state.search.items,
  }),
  {},
)(SearchResults);
