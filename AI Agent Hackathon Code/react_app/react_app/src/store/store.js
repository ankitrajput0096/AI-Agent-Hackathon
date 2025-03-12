//Creating the redux store for the application
import { configureStore } from '@reduxjs/toolkit';
import rootReducer from '../rootReducers/rootReducer';

const store = configureStore(
    {reducer: rootReducer }
);
export default store;