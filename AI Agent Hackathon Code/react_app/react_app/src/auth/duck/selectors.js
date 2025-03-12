import * as types from './types';

const getState = state => state[types.NAMESPACE];

const isFetching = state => getState(state).isFetching;
const isAuthenticated = state => getState(state).isAuthenticated;
const getUser = state => getState(state).user;
const getToken = state => getState(state).token;
const getError = state => getState(state).error;
const getMessage = state => getState(state).message;

export default {
    isFetching,
    isAuthenticated,
    getUser,
    getToken,
    getError,
    getMessage
};