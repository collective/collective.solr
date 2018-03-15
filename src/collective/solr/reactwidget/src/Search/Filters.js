import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { searchActions } from './ducks';
import Filter from './Filter';

class Filters extends Component {
  static propTypes = {
    subjects: PropTypes.array,
    types: PropTypes.array,
    sorting: PropTypes.array,
  };

  state = {
    selectedSubjectsCheckboxes: new Set(),
    selectedTypesCheckboxes: new Set(),
    selectedSortingCheckboxes: ['relevance'],
  };

  componentWillMount() {
    this.props.getSubjects();
  }

  resetCheckboxes = () => {
    this.setState({ selectedSubjectsCheckboxes: new Set() });
    // dispatch(
    //   refreshEvents({
    //     items: this.selectedSubjectsCheckboxes,
    //     locations: this.selectedLocationCheckboxes,
    //   }),
    // );
  };

  handleChangeFilter = (item, type) => {
    let currentFilterSelection;
    switch (type) {
      case 'subjects':
        currentFilterSelection = this.state.selectedSubjectsCheckboxes;
        if (currentFilterSelection.has(item)) {
          currentFilterSelection.delete(item);
        } else {
          currentFilterSelection.add(item);
        }
        this.setState({ selectedSubjectsCheckboxes: currentFilterSelection });
        break;
      case 'types':
        currentFilterSelection = this.state.selectedTypesCheckboxes;
        if (currentFilterSelection.has(item)) {
          currentFilterSelection.delete(item);
        } else {
          currentFilterSelection.add(item);
        }
        this.setState({ selectedTypesCheckboxes: currentFilterSelection });
        break;
      case 'sorting':
        currentFilterSelection = [item];
        this.setState({ selectedSortingCheckboxes: [item] });
        break;
      default:
        return;
    }

    this.props.updateResults({
      [type]: [...currentFilterSelection],
    });
  };

  render() {
    const { sorting, subjects, types } = this.props;
    return (
      <div>
        <fieldset>
          <legend className="titling">Filtern</legend>
          <button
            type="reset"
            className="btn-destructive"
            onClick={e => this.resetCheckboxes()}
          >
            Filter zurücksetzen
          </button>
        </fieldset>
        <Filter
          onChangeFilter={this.handleChangeFilter}
          items={subjects}
          name="Stichworte"
          type="subjects"
        />
        <Filter
          onChangeFilter={this.handleChangeFilter}
          items={types}
          name="Typen"
          type="types"
        />
        <fieldset>
          <legend>Sortieren</legend>
          {sorting.map((item, i) => (
            <div key={i}>
              <input
                type="radio"
                checked={this.state.selectedSortingCheckboxes.includes(
                  item.token,
                )}
                id={item.token}
                value={item.token}
                name={item.token}
                onChange={event =>
                  this.handleChangeFilter(event.target.value, 'sorting')
                }
              />
              <label htmlFor={item.token}>{item.title}</label>
            </div>
          ))}
        </fieldset>
      </div>
    );
  }
}

export default connect(
  state => ({
    subjects: state.search.subjects,
    types: state.search.types,
    sorting: state.search.sorting,
  }),
  {
    getSubjects: searchActions.getSubjects,
    updateResults: searchActions.updateResults,
  },
)(Filters);
