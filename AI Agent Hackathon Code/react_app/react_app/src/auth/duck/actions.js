import * as types from './types';
import axios from 'axios';
import authUtils from './utils';

// Login user
const loginUser = (username, password) => dispatch => {
    const loginUrl = 'http://localhost:8090/login';
    dispatch({ type: types.FETCH });
    
    const loginData = authUtils.constructLoginBody(username, password);
    
    axios.post(loginUrl, loginData)
        .then(function (response) {
            console.log("Login response:", response.data);
            dispatch({ 
                type: types.LOGIN_SUCCESS, 
                payload: { 
                    user: response.data.user || username,
                    token: response.data.token || 'dummy-token' 
                }
            });
        })
        .catch(function (error) {
            console.log("Login error:", error);
            dispatch({ 
                type: types.LOGIN_FAILURE, 
                payload: error.response?.data?.message || 'Login failed. Please check your credentials.'
            });
        });
};

// Register new user
const registerUser = (username, password) => dispatch => {
    const registerUrl = 'http://localhost:8090/register';
    dispatch({ type: types.FETCH });
    
    const registerData = authUtils.constructRegisterBody(username, password);
    
    axios.post(registerUrl, registerData)
        .then(function (response) {
            console.log("Register response:", response.data);
            dispatch({ 
                type: types.REGISTER_SUCCESS, 
                payload: response.data.message || 'Registration successful. Please login.'
            });
        })
        .catch(function (error) {
            console.log("Register error:", error);
            dispatch({ 
                type: types.REGISTER_FAILURE, 
                payload: error.response?.data?.message || 'Registration failed. Please try again.'
            });
        });
};


// Logout user
const logoutUser = () => dispatch => {
    const logoutUrl = 'http://localhost:8090/logout';
    dispatch({ type: types.FETCH });
    
    const logoutData = authUtils.constructLogoutBody();
    
    axios.post(logoutUrl, logoutData)
        .then(function (response) {
            console.log("Logout response:", response.data);
            dispatch({ type: types.LOGOUT });
        })
        .catch(function (error) {
            console.log("Logout error:", error);
            // Still log out the user from the frontend
            dispatch({ type: types.LOGOUT });
        });
};

// Clear error messages
const clearError = () => dispatch => {
    dispatch({ type: types.CLEAR_ERROR });
};

export default {
    loginUser,
    registerUser,
    logoutUser,
    clearError
};
