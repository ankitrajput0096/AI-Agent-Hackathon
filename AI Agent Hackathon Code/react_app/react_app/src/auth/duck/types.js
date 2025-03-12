export const NAMESPACE = 'auth';

const format = (value, type = 'action') => `${NAMESPACE}/${value}/${type}`;

export const FETCH = format('fetch');
export const LOGIN_SUCCESS = format('login-success');
export const LOGIN_FAILURE = format('login-failure');
export const REGISTER_SUCCESS = format('register-success');
export const REGISTER_FAILURE = format('register-failure');
export const LOGOUT = format('logout');
export const CLEAR_ERROR = format('clear-error');