import * as types from './types';
import axios from 'axios';
import aboutUsUtils from './utils';

//POST API for LinkedIn search
const postMethodCall = (searchQuery) => dispatch => {
  const postUrl = 'http://localhost:8070/api/linkedin/search';
  dispatch({ type: types.FETCH });  // with this action object make 'isFetching' true in redux state.
  
  const requestBody = {
    linkedin_email: "khraju1.1rn17is046@gmail.com",
    linkedin_password: "vishnu123@KHR",
    search_query: searchQuery,
    groq_api_key: "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"
  };
  
  axios.post(postUrl, requestBody, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(function (response) {
      console.log("response");
      console.log(response.data);
      
      // Format the profiles into a readable message
      const formattedResponse = formatLinkedInResponse(response.data);
      
      dispatch({ type: types.POST_API_STATUS, payload: formattedResponse });
    })
    .catch(function (error) {
      // handle error
      console.log(error);
      dispatch({ type: types.POST_API_STATUS, payload: "Error: Unable to fetch LinkedIn profiles. Please try again." });
    });
};

// Helper function to format LinkedIn API response
const formatLinkedInResponse = (data) => {
  if (!data || !data.profiles || data.profiles.length === 0) {
    return "No profiles found matching your search criteria.";
  }
  
  let formattedResponse = `${data.message}\n\n`;
  data.profiles.forEach((profile, index) => {
    formattedResponse += `${index + 1}. ${profile.headline}\n`;
    // Use Markdown syntax for clickable links
    formattedResponse += `   [LinkedIn Profile Link](${profile.url})\n\n`;
  });
  
  return formattedResponse;
};


//POST API EXAMPLE - keeping for reference but not actively used
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
    });
};

const resetReduxState = () => dispatch => {
  dispatch({ type: types.RESET_REDUX });  // with this action object make 'isFetching' true in redux state.
};

//Public actions which are invoked from the application components
export default {
  postMethodCall,
  resetReduxState,
  postMethodCallWithText,
};