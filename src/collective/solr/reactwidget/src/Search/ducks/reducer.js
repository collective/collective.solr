import { map } from 'lodash';
import config from '../../config';
import types from './types';

const initialState = {
  error: null,
  items: [],
  subjects: [],
  types: [
    { title: 'Folder', token: 'Folder' },
    { title: 'Document', token: 'Document' },
    { title: 'Collection', token: 'Collection' },
    { title: 'News Item', token: 'News Item' },
    { title: 'Event', token: 'Event' },
  ],
  sorting: [
    { title: 'Relevanz', token: 'relevance' },
    { title: 'Datum', token: 'date' },
    { title: 'Alphabetisch', token: 'sortable_title' },
  ],
  options: {},
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
    case `${types.GET_SUBJECTS}_PENDING`:
      return {
        ...state,
        error: null,
        loading: true,
        loaded: false,
      };
    case `${types.GET_SUBJECTS}_FAIL`:
      return {
        ...state,
        error: action.error,
        subjects: [],
        loading: false,
        loaded: false,
      };
    case `${types.GET_SUBJECTS}_SUCCESS`:
      return {
        ...state,
        subjects: action.result.terms,
      };
    default:
      return state;
  }
};

export default reducer;
