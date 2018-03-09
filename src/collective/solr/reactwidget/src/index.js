import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import store from './store';
import Search from './Search/Search';

ReactDOM.render(
  <Provider store={store}>
    <Search />
  </Provider>,
  document.getElementById('container'),
);
