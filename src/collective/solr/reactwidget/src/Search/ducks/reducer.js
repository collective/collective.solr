import { map } from 'lodash';
import config from '../../config';
import types from './types';

const initialState = {
  error: null,
  items: [],
  total: 0,
  loaded: false,
  loading: false,
};

const reducer = (state = initialState, action = {}) => {
  switch (action.type) {
    case `${types.SEARCH_CONTENT}_PENDING`:
      return {
        ...state,
        error: null,
        loading: true,
        loaded: false,
      };
    case `${types.SEARCH_CONTENT}_SUCCESS`:
      return {
        ...state,
        error: null,
        items: map(action.result.items, item => ({
          ...item,
          '@id': item['@id'].replace(config.apiPath, ''),
        })),
        total: action.result.items_total,
        loaded: true,
        loading: false,
      };
    case `${types.SEARCH_CONTENT}_FAIL`:
      return {
        ...state,
        error: action.error,
        items: [],
        total: 0,
        loading: false,
        loaded: false,
      };
    case types.UPDATE_SEARCH_OPTIONS:
      return {
        ...state,
        options: {
          ...state.options,
          ...action.options,
        },
      };
    case types.RESET_SEARCH_CONTENT:
      return {
        ...state,
        error: null,
        items: [],
        total: 0,
        loading: false,
        loaded: false,
      };
    default:
      return state;
  }
};

export default reducer;
