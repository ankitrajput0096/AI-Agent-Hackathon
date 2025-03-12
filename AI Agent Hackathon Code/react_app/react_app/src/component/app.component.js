import React from "react";
import "./app.component.css"; // Assume CSS is handled in LandingPage.css

import RobotImage from "../assets/Picture1.png";
import DataExtractionImage from "../assets/Picture2.png";
import { NavLink } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="landing-page">
      <main className="main-content">
        <h1 className="headline">Global Learn AI</h1>

        <p className="subtext">
        Meet your AI learning companion—bridging educational gaps worldwide with personalized, adaptive education.
        <br></br>
        From classrooms to careers, our AI agent empowers learners of all ages, everywhere.
        <br></br>
        Together, we’re redefining learning for a brighter, smarter future.
        </p>
        <NavLink to='/register' style={{"text-decoration": "none"}}>
          <div className="cta-buttons">
            <button className="cta-button primary">Let's get started</button>
          </div>
        </NavLink>
        <div className="illustrations">
          <div className="illustration-left">
            <img src={DataExtractionImage} alt="Person using a phone" />
          </div>
          <div className="illustration-right">
            <img src={RobotImage} alt="Person working on a laptop" />
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
