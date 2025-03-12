//Namespace
export const NAMESPACE = 'about-us';

const format = (value, type = 'action') => `${NAMESPACE}/${value}/${type}`;

//public actions
export const FETCH = format('fetch');
export const POST_API_STATUS = format('post-api-status');
export const RESET_REDUX = format('reset-redux');