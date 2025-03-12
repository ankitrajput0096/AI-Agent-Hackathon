import * as types from './types';
import axios from 'axios';
import aboutUsUtils from './utils';

//POST API EXAMPLE
const postMethodCall = (name) => dispatch => {
  const postUrl = 'http://localhost:8090/ask_general_query';
  dispatch({ type: types.FETCH });  // with this action object make 'isFetching' true in redux state.
  const newTopic = aboutUsUtils.constructPostBody(name);
  axios.post(postUrl , newTopic)
    .then(function (response) {

      console.log("response");
      console.log(response.data);

      dispatch({ type: types.POST_API_STATUS, payload: response.data.response })   // with this action upload the response in redux store and make 'isFetching' false.
    })
    .catch(function (error) {
      // handle error
      console.log(error);
      // dispatch({ type: types.GET_API_DATA, payload: {}})
    })
    .finally(function () {
      // always executed
      // dispatch({ type: 'GET_TODOS_FINALLY' })
    });
}

//POST API EXAMPLE
const postMethodCallWithText = (text, name) => dispatch => {
  const postUrl = 'http://localhost:8090/text_and_query';
  dispatch({ type: types.FETCH });  // with this action object make 'isFetching' true in redux state.
  const newTopic = aboutUsUtils.constructPostBodyWithText(text, name);
  axios.post(postUrl , newTopic)
    .then(function (response) {

      console.log("response: ");
      console.log(response);
      console.log("response data: ");
      console.log(response.data);

      dispatch({ type: types.POST_API_STATUS, payload: response.data.answer })   // with this action upload the response in redux store and make 'isFetching' false.
    })
    .catch(function (error) {
      // handle error
      console.log(error);
      // dispatch({ type: types.GET_API_DATA, payload: {}})
    })
    .finally(function () {
      // always executed
      // dispatch({ type: 'GET_TODOS_FINALLY' })
    });
}

const resetReduxState = () => dispatch => {
  dispatch({ type: types.RESET_REDUX });  // with this action object make 'isFetching' true in redux state.
}

//Public actions which are invoked from the application components
export default {
  postMethodCall,
  resetReduxState,
  postMethodCallWithText,
};
