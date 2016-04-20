import React, {PropTypes} from 'react';
import ReactDOM from 'react-dom';


class SearchApp extends React.Component {
  render() {
    return (
      <div>
        <SearchBox />
        <SearchResults results={this.props.results} />
      </div>
    )
  }
}
SearchApp.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object)
}


class SearchBox extends React.Component {
  render() {
    return (
      <input type="search" placeholder="Search" />
    );
  }
}


class SearchResults extends React.Component {
  render() {
    return (
      <ul>
        {this.props.results.map(
          (item) => <SearchResultItem key={item.id}
                                      id={item.id}
                                      title={item.title} />
        )}
      </ul>
    )
  }
}
SearchResults.propTypes = {
  results: PropTypes.arrayOf(PropTypes.object)
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
