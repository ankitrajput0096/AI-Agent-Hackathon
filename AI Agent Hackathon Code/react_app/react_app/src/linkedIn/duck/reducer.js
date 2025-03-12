import * as types from './types';

const initialState = {  //initial state of reducer for this component in redux store.
  isFetching: false,
  postApiDataStatus: '',
};

//This function handles operations which needs to be performed 
//depending on the action Type and payload of the action triggered.
const IncDecReducer = (state = initialState, action) => {
  switch (action.type) { // 'switch' case based on action type
    case types.FETCH:
      return {
        ...state,
        isFetching: true
      };
    case types.POST_API_STATUS:
      return {
        ...state,
        postApiDataStatus: action.payload,
        isFetching: false
      };
    case types.RESET_REDUX: {
      return {
        ...state,
        postApiDataStatus: '',
      }
    }
    default:
      return state;
  }
};

export default IncDecReducer;
