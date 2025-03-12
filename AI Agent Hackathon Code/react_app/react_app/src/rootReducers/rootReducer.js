//Combining all the reducers of the applicaiton
import { combineReducers } from 'redux';
import IncDecReducer, { types as aboutUsTypes} from '../AboutUs/duck';
import AuthReducer, {types as AuthTypes} from '../auth/duck';
import linkedInReducer, {types as linkedInTypes} from '../linkedIn/duck';
//import more reducers

const rootReducer = combineReducers({
  [aboutUsTypes.NAMESPACE]: IncDecReducer,
  [AuthTypes.NAMESPACE]: AuthReducer,
  [linkedInTypes.NAMESPACE]: linkedInReducer,
  //can add more reducers here
});

export default rootReducer;
