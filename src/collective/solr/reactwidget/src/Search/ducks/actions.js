import types from './types';
import { join, head, map, toPairs, pickBy } from 'lodash-es';

export const getResults = (url, options) => {
  let querystring = '';
  const simplequerystring = options
    ? join(
        map(
          toPairs(
            pickBy(
              options,
              (item, key) =>
                key !== 'subjects' && key !== 'types' && key !== 'sorting',
            ),
          ),
          item => join(item, '='),
        ),
        '&',
      )
    : '';
  querystring = simplequerystring ? `${querystring}${simplequerystring}` : '';

  const subjectsQueryString = options
    ? join(
        head(
          map(pickBy(options, (item, key) => key === 'subjects'), (item, key) =>
            item.map(subject => `Subject:list=${subject}`),
          ),
        ),
        '&',
      )
    : '';

  querystring = subjectsQueryString
    ? `${querystring}${subjectsQueryString}`
    : querystring;

  const typesQueryString = options
    ? join(
        head(
          map(pickBy(options, (item, key) => key === 'types'), (item, key) =>
            item.map(subject => `portal_type:list=${subject}`),
          ),
        ),
        '&',
      )
    : '';

  querystring = typesQueryString
    ? `${querystring}${typesQueryString}`
    : querystring;

  let sortonQueryString;
  if (options.sorting) {
    switch (options.sorting[0]) {
      case 'relevance':
        sortonQueryString = '&sort_on=';
        break;
      case 'date':
        sortonQueryString = '&sort_on=Date&sort_order=reverse';
        break;
      case 'sortable_title':
        sortonQueryString = '&sort_on=sortable_title';
        break;
      default:
        sortonQueryString = '&sort_on=';
    }
  } else {
    sortonQueryString = '&sort_on=';
  }

  querystring = sortonQueryString
    ? `${querystring}${sortonQueryString}`
    : querystring;

  return {
    type: types.SEARCH_CONTENT,
    promise: api =>
      api.get(
        `${url}/@search${querystring ? `?${querystring}` : ''}&fullobjects`,
      ),
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

export const getSubjects = () => ({
  type: types.GET_SUBJECTS,
  promise: api => api.get('/@vocabularies/plone.app.vocabularies.Keywords'),
});
