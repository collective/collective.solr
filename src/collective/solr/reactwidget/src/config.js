/**
 * Config.
 * @module config
 */
import defaults from 'lodash-es/defaults';

export default defaults(
  {},
  {
    apiPath: process.env.API_PATH,
  },
  {
    apiPath: document.getElementById('container')
      ? document.getElementById('container').dataset.portalurl
      : '',
  },
);
