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
    const isEmpty = results.length === 0;
    console.log(isEmpty);
    if (isEmpty) {
      return <h2>No results</h2>;
    }

    return (
      <ol className="list-sections list-events">
        {results.map((result, i) => (
          <li key={i}>
            <a href={result.getURL} style={{ marginLeft: '10px' }}>
              <h2 className="event-title">{result.title}</h2>
              <p className="event-description">{result.description}</p>
              <p className="event-category">
                {result.subjects.map(subject => (
                  <span key={subject}>{`${subject}, `}</span>
                ))}
              </p>
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
