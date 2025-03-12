import * as types from './types';

const getState = state => state[types.NAMESPACE];

const isFetching = state => getState(state).isFetching;
const postApiData = state => getState(state).postApiDataStatus;

export default {
  isFetching,
  postApiData,
};
