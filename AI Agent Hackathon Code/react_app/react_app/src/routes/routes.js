//This is the starting point of the application

import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import App from '../component/app.component';
import Register from '../auth/Register';
import Login from '../auth/Login';
import About from '../AboutUs/about';
import LinkedIn from '../linkedIn/linkedIn';
import "../css/main.css";    // importing 'main.css' file which contains all the
                             // css of the application.
                          

export default () => {
 return (
  <BrowserRouter>
    <Routes>
      <Route exact path="/" element={<App />} />
      <Route exact path="/register" element={<Register />} />
      <Route exact path="/about" element={<About />} />
      <Route exact path="/login" element={<Login />} />
      <Route exact path="/linkedIn" element={<LinkedIn />} />
    </Routes>
  </BrowserRouter>    
 )
}