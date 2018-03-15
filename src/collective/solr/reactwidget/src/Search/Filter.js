import React from 'react';
import PropTypes from 'prop-types';

const Filter = ({ items, name, type, onChangeFilter }) => (
  <fieldset>
    <legend>{name}</legend>
    {items.map((item, i) => (
      <div key={i}>
        <input
          type="checkbox"
          id={item.token}
          value={item.token}
          name={item.token}
          onChange={event => onChangeFilter(event.target.value, type)}
        />
        <label htmlFor={item.token}>{item.title}</label>
      </div>
    ))}
  </fieldset>
);

Filter.propTypes = {
  items: PropTypes.array,
  onChangeFilter: PropTypes.func.isRequired,
  name: PropTypes.string,
  type: PropTypes.string,
};

export default Filter;
