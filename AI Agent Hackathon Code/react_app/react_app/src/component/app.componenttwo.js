import React, { Component } from "react";
import "./app.componenttwo.css";
import { NavLink } from 'react-router-dom';
class MyComponentTwo extends Component {
  render() {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <div className="header-left">
            <h1 className="title">Chat UI</h1>
          </div>
          <div className="header-right">
            <div className="version-toggle">
              <NavLink to='/'>
                <button className="version-button left-button">Homepage</button>
              </NavLink>
              <button className="version-button right-button active">Chat UI</button>
            </div>
          </div>
        </header>
        <main className="dashboard-main">
          <div className="version-toggle">
            <h2 className="chat-title"> What can I help with? </h2>
          </div>

          <div className="lightning-icon">
            <i className="fas fa-bolt"></i>
          </div>

          <div className="chat-box">
            <input
              type="text"
              placeholder="Type your message here..."
              className="chat-input"
            />
            <button className="submit-button">Submit</button>
          </div>
        </main>
        <footer className="dashboard-footer">
          <p>
            Personal Project, this may produce inaccurate information
            about people, places, or facts.
          </p>
        </footer>
      </div>
    );
  }
}

export default MyComponentTwo;
