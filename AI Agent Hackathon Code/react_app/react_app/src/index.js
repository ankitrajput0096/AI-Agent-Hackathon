import React from "react";
import { createRoot } from 'react-dom/client';
import AppRoutes from './routes/routes';
import { Provider } from 'react-redux';
import store from './store/store';

//Here, redux store is wrapped at application level
const domNode = document.getElementById('root');
const root = createRoot(domNode);

root.render(
    <React.StrictMode>
        <Provider store={store}>    
            <AppRoutes />
        </Provider>,
    </React.StrictMode>
);

if (module.hot) {
    module.hot.accept();
}
