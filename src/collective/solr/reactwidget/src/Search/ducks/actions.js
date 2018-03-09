import types from './types';
import { join, map, toPairs, pickBy } from 'lodash-es';

export const getResults = (url, options) => {
  const querystring = options
    ? join(map(toPairs(pickBy(options)), item => join(item, '=')), '&')
    : '';
  return {
    type: types.SEARCH_CONTENT,
    promise: api =>
      api.get(`${url}/@search${querystring ? `?${querystring}` : ''}`),
  };
};

export const updateOptions = options => ({
  type: types.UPDATE_SEARCH_OPTIONS,
  options,
});

export const updateResults = options => (dispatch, getState) => {
  dispatch(updateOptions(options));
  dispatch(getResults('', getState().search.options));
};
