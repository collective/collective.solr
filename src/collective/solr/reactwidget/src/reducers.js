import { combineReducers } from 'redux';
import search from './Search/ducks';

const rootReducer = combineReducers({ search });

export default rootReducer;
