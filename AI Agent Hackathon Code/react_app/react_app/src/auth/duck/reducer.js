import * as types from './types';

const initialState = {
    isFetching: false,
    isAuthenticated: false,
    user: null,
    token: null,
    error: null,
    message: null
};

const AuthReducer = (state = initialState, action) => {
    switch (action.type) {
        case types.FETCH:
            return {
                ...state,
                isFetching: true,
                error: null
            };
            
        case types.LOGIN_SUCCESS:
            return {
                ...state,
                isFetching: false,
                isAuthenticated: true,
                user: action.payload.user,
                token: action.payload.token,
                error: null
            };
            
        case types.LOGIN_FAILURE:
            return {
                ...state,
                isFetching: false,
                isAuthenticated: false,
                error: action.payload
            };
            
        case types.REGISTER_SUCCESS:
            return {
                ...state,
                isFetching: false,
                message: action.payload,
                error: null
            };
            
        case types.REGISTER_FAILURE:
            return {
                ...state,
                isFetching: false,
                error: action.payload
            };
            
        case types.LOGOUT:
            return {
                ...initialState
            };
            
        case types.CLEAR_ERROR:
            return {
                ...state,
                error: null,
                message: null
            };
            
        default:
            return state;
    }
};

export default AuthReducer;