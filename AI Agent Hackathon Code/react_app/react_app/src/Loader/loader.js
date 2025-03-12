import React from 'react';
import './Loader.css'; // Import the CSS file or use inline styles if preferred

const Loader = () => {
  return (
    <div className="overlay">
      <div className="loader-text">
        <p>The response may take up to 3-5 minutes. <br /> So, enjoy this animation and sit tight.</p>
      </div>
      <div className="loader-container">
        <div className="dash uno"></div>
        <div className="dash dos"></div>
        <div className="dash tres"></div>
        <div className="dash cuatro"></div>
      </div>
    </div>
  );
};

export default Loader;
