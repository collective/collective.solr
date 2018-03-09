import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly';

import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import { api } from './middleware';
import reducer from './reducers';

import { Api } from './helpers';

const apiHelper = new Api();

const initialState = {};

const middlewares = composeWithDevTools(applyMiddleware(thunk, api(apiHelper)));
const store = createStore(reducer, initialState, middlewares);

export default store;
