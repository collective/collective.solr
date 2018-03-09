import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { searchActions } from './ducks';
import { bindActionCreators } from 'redux';

const SearchBox = ({ updateResults }) => {
  return (
    <fieldset className="fieldset-search">
      <legend className="sr-only">Cerca</legend>
      <label className="sr-only">Cerca</label>
      <input
        type="search"
        className="filter-search"
        onChange={e => updateResults({ SearchableText: e.target.value })}
        placeholder="Search"
      />
      <input type="button" value="search" />
    </fieldset>
  );
};

SearchBox.propTypes = {
  updateResults: PropTypes.func.isRequired,
};

export default connect(null, dispatch =>
  bindActionCreators({ updateResults: searchActions.updateResults }, dispatch),
)(SearchBox);
