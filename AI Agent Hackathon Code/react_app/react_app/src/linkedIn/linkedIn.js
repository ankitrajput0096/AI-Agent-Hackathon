import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { actions as IncDecActions, selectors as IncDecSelectors } from './duck';
import Loader from '../Loader/loader';

import LogoutButton from '../auth/LogoutButton';

import "./linkedIn.css";

class LinkedIn extends Component {
  constructor(props) {
    super(props);
    this.state = {
      postName: '',
      conversation: [],
      lastPostData: null,
      isResetting: false, // Flag to prevent updates during reset
      fileUploaded: false, // State to track if a file has been uploaded
      fileContent: '',
      isQuizSelected: false, // Flag to track if Quiz mode is selected
      quizData: null, // To store quiz data from API
      showQuizModal: false, // Control quiz modal visibility
      userAnswers: {}, // Store user's selected answers
      quizSubmitted: false, // Track if quiz has been submitted
      correctAnswersCount: 0, // Count of correct answers
    };
  }

  static propTypes = {
    postData: PropTypes.string.isRequired,
  };

  handleHomePageChange = () => {
    const { resetReduxState } = this.props;
    resetReduxState();
    this.setState({
      conversation: [],
      lastPostData: null,
      isResetting: true, // Block updates from getDerivedStateFromProps
    }, () => {
      // Re-enable updates after resetting
      this.setState({ isResetting: false });
    });
  };

  handleChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  };

  handleSubmit = (Type) => {
    const { postMethodCall } = this.props;
    const { postName } = this.state;

    if (Type === 'postAPI') {
      const userMessage = postName;

      this.setState((prevState) => ({
        conversation: [...prevState.conversation, { sender: 'User', message: userMessage }],
        postName: '',
        fileContent: '',
        fileUploaded: false,
      }));

      // Adding loading message
      this.setState((prevState) => ({
        conversation: [...prevState.conversation, { sender: 'LinkedIn AI', message: 'Searching LinkedIn profiles...' }],
      }));

      postMethodCall(userMessage);
    }
  };

  static getDerivedStateFromProps(nextProps, prevState) {
    const { postData } = nextProps;

    // Prevent updates during reset
    if (prevState.isResetting) {
      return null;
    }

    if (postData && postData !== prevState.lastPostData) {
      // Find and remove the loading message
      const updatedConversation = prevState.conversation.filter(
        msg => !(msg.sender === 'LinkedIn AI' && msg.message === 'Searching LinkedIn profiles...')
      );
      
      return {
        conversation: [...updatedConversation, { sender: 'LinkedIn AI', message: postData }],
        lastPostData: postData,
      };
    }
    return null;
  }

  _renderPostData() {
    return (
      <div className="chat-box">
        <div className="chat-input" style={{ display: 'flex', alignItems: 'center' }}>
          {/* Left side labels grouped together */}
          <div style={{ display: 'flex', marginRight: 'auto' }}>
            <input
              type="file"
              id="file-input"
              accept=".txt"
              onChange={this.handleFileUpload}
              style={{ display: 'none' }}
            />
          </div>
          
          {/* Center span with input */}
          <span style={{ flex: '1', textAlign: 'center' }}>
            <input
              type="text"
              placeholder="Search for LinkedIn profiles..."
              className="text-input"
              value={this.state.postName}
              onChange={(e) => this.handleChange(e)}
              name="postName"
            />
          </span>
        </div>
        <button className="submit-button" onClick={() => this.handleSubmit('postAPI')}>Search</button>
      </div>
    );
  }

  // _renderConversation() {
  //   return (
  //     <div className="conversation-container">
  //       {this.state.conversation.map((entry, index) => (
  //         <div
  //           key={index}
  //           className={`chat-message ${entry.sender === 'User' ? 'user-message' : 'server-message'}`}
  //         >
  //           <strong>{entry.sender}:</strong> <pre style={{whiteSpace: 'pre-wrap'}}>{entry.message}</pre>
  //         </div>
  //       ))}
  //     </div>
  //   );
  // }
// Add this helper method to process message content
processMessageContent(message) {
  return message.split('\n').map((line, lineIndex, linesArray) => {
    // Split line into text and links
    const parts = [];
    let remaining = line;
    let linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    let match;
    let lastIndex = 0;

    while ((match = linkRegex.exec(line)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(line.substring(lastIndex, match.index));
      }

      // Add link component
      parts.push(
        <a
          key={`link-${lineIndex}-${match.index}`}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
        >
          {match[1]}
        </a>
      );

      lastIndex = linkRegex.lastIndex;
    }

    // Add remaining text after last match
    if (lastIndex < line.length) {
      parts.push(line.substring(lastIndex));
    }

    return (
      <div key={`line-${lineIndex}`}>
        {parts}
        {lineIndex < linesArray.length - 1 && <br />}
      </div>
    );
  });
}

_renderConversation() {
  return (
    <div className="conversation-container">
      {this.state.conversation.map((entry, index) => (
        <div
          key={index}
          className={`chat-message ${entry.sender === 'User' ? 'user-message' : 'server-message'}`}
          style={{
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
            overflow: 'hidden'
          }}
        >
          <strong>{entry.sender}:</strong>
          <div style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            overflowWrap: 'break-word',
            maxWidth: '100%'
          }}>
            {this.processMessageContent(entry.message)}
          </div>
        </div>
      ))}
    </div>
  );
}

  _showTitle() {
    if (this.state.conversation.length === 0) {
      return (
        <div className="version-toggle">
          <h2 className="chat-title">Search for LinkedIn Profiles</h2>
        </div>
      );
    }
    return null;
  }

  render() {
    const { isFetching } = this.props;
    if (isFetching) {
      return (
        <h1>
          <Loader />
        </h1>
      );
    } else {
      return (
        <div className="dashboard-container">
          <header className="dashboard-header">
            <div className="header-left-linkedIn">
              <h1 className="title">LinkedIn Search</h1>
            </div>
            <div className="header-right">
              <div className="version-toggle">
                <NavLink to='/about'>
                  <button className="version-button left-button active">Chat UI</button>
                </NavLink>
                <NavLink to='/'>
                  <LogoutButton/>
                </NavLink>
              </div>
            </div>
          </header>
          <main className="dashboard-main">
            {this._showTitle()}
            {this._renderConversation()}
            {this._renderPostData()}
          </main>
          <footer className="dashboard-footer">
            <p>
              LinkedIn Profile Search Tool. Results are based on LinkedIn's public profiles.
            </p>
          </footer>
        </div>
      );
    }
  }
}

const mapStateToProps = (state) => ({
  isFetching: IncDecSelectors.isFetching(state),
  postData: IncDecSelectors.postApiData(state),
});

const mapDispatchToProps = (dispatch) =>
  bindActionCreators(
    {
      postMethodCall: IncDecActions.postMethodCall,
      resetReduxState: IncDecActions.resetReduxState,
      postMethodCallWithText: IncDecActions.postMethodCallWithText,
    },
    dispatch
  );

export default connect(mapStateToProps, mapDispatchToProps)(LinkedIn);