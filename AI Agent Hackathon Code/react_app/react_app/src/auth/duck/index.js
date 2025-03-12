import * as types from './types';
import actions from './actions';
import reducer from './reducer';
import selectors from './selectors';
import utils from './utils';

// Export reducer separately
export default reducer;

// Export other files with names accordingly
export {
    types,
    actions,
    selectors,
    utils
};
