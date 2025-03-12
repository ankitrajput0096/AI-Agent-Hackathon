import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { actions as IncDecActions, selectors as IncDecSelectors } from './duck';
import Loader from '../Loader/loader';

import LogoutButton from '../auth/LogoutButton';

import "./about.css";

class Contact extends Component {
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

  // Add new click handler method
  handleQuizClick = () => {
    this.setState(prevState => ({
      isQuizSelected: !prevState.isQuizSelected
    }));
  };

  handleChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  };

  handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = () => {
        this.setState({fileContent: reader.result});
      };
      reader.readAsText(file);
      this.setState({ fileUploaded: true }); // Update state to indicate file upload
    } else {
      alert('Please upload a valid .txt file');
    }
  };

  handleSubmit = (Type) => {
    const { postMethodCall, postMethodCallWithText } = this.props;
    const { isQuizSelected, postName, fileContent } = this.state;

    if (Type === 'postAPI') {
      const userMessage = postName;

      this.setState((prevState) => ({
        conversation: [...prevState.conversation, { sender: 'User', message: userMessage }],
        postName: '',
        fileContent: '',
        fileUploaded: false,
      }));

      if (isQuizSelected) {
        // Make quiz API call
        this.makeQuizApiCall(userMessage);
      } else if (fileContent.length > 0) {
        postMethodCallWithText(fileContent, userMessage);
      } else {
        postMethodCall(userMessage);
      }
    }
  };

  makeQuizApiCall = (query) => {
    // Call the quiz API
    fetch('http://localhost:8090/make_quiz', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })
      .then(response => response.json())
      .then(data => {

        console.log("the quiz");
        console.log(data);


        this.setState({
          quizData: data.quiz,
          showQuizModal: true,
          userAnswers: {},
          quizSubmitted: false,
          correctAnswersCount: 0,
        });
      })
      .catch(error => {
        console.error('Error fetching quiz:', error);
        this.setState((prevState) => ({
          conversation: [...prevState.conversation, { sender: 'AI Friend', message: 'Sorry, there was an error generating the quiz.' }],
        }));
      });
  };

  handleAnswerSelect = (questionIndex, choice) => {
    this.setState(prevState => ({
      userAnswers: {
        ...prevState.userAnswers,
        [questionIndex]: choice
      }
    }));
  };

  handleQuizSubmit = () => {
    const { quizData, userAnswers } = this.state;
    let correctCount = 0;

    // Calculate correct answers
    quizData.forEach((question, index) => {
      if (userAnswers[index] === question.answer) {
        correctCount++;
      }
    });

    this.setState({
      quizSubmitted: true,
      correctAnswersCount: correctCount,
    });
  };

  closeQuizModal = () => {
    const { quizData, correctAnswersCount } = this.state;
    
    // Add a message to the conversation about quiz results
    this.setState((prevState) => ({
      showQuizModal: false,
      isQuizSelected: false,
      conversation: [...prevState.conversation, { 
        sender: 'AI Friend', 
        message: `Quiz\nNumber of questions: ${quizData.length}\nNumber of correct answers: ${correctAnswersCount}` 
      }],
    }));
  };

  static getDerivedStateFromProps(nextProps, prevState) {
    const { postData } = nextProps;

    // Prevent updates during reset
    if (prevState.isResetting) {
      return null;
    }

    if (postData && postData !== prevState.lastPostData) {
      return {
        conversation: [...prevState.conversation, { sender: 'AI Friend', message: postData }],
        lastPostData: postData,
      };
    }
    return null;
  }

  _renderPostData() {
    const { fileUploaded } = this.state;
  
    return (
      <div className="chat-box">
        <div className="chat-input" style={{ display: 'flex', alignItems: 'center' }}>
          {/* Left side labels grouped together */}
          <div style={{ display: 'flex', marginRight: 'auto' }}>
            <label
              htmlFor="file-input"
              className={`plus-input ${fileUploaded ? 'file-selected' : ''}`}
              title=""
            >
              +
            </label>
            <label
              onClick={this.handleQuizClick}
              className={`quiz-label ${this.state.isQuizSelected ? 'quiz-label-selected' : ''}`}
            >
              Quiz
            </label>
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
              placeholder="Type your message here..."
              className="text-input"
              value={this.state.postName}
              onChange={(e) => this.handleChange(e)}
              name="postName"
            />
          </span>
        </div>
        <button className="submit-button" onClick={() => this.handleSubmit('postAPI')}>Submit</button>
      </div>
    );
  }

  _renderConversation() {
    return (
      <div className="conversation-container">
        {this.state.conversation.map((entry, index) => (
          <div
            key={index}
            className={`chat-message ${entry.sender === 'User' ? 'user-message' : 'server-message'}`}
          >
            <strong>{entry.sender}:</strong> {entry.message}
          </div>
        ))}
      </div>
    );
  }

  _renderQuizModal() {
    const { quizData, showQuizModal, userAnswers, quizSubmitted } = this.state;

    if (!showQuizModal || !quizData) return null;

    return (
      <div className="quiz-modal-overlay" style={quizModalOverlayStyle}>
        <div className="quiz-modal" style={quizModalStyle}>
          <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Quiz</h2>
          
          {quizData.map((question, questionIndex) => (
            <div key={questionIndex} style={{ marginBottom: '20px', padding: '15px', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
              <p style={{ fontWeight: 'bold', marginBottom: '10px' }}>{questionIndex + 1}. {question.question}</p>
              
              {Object.entries(question.choices).map(([choiceKey, choiceText]) => (
                <div key={choiceKey} style={{ margin: '8px 0' }}>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name={`question-${questionIndex}`}
                      value={choiceKey}
                      checked={userAnswers[questionIndex] === choiceKey}
                      onChange={() => this.handleAnswerSelect(questionIndex, choiceKey)}
                      disabled={quizSubmitted}
                      style={{ marginRight: '10px' }}
                    />
                    <span style={
                      quizSubmitted 
                        ? (choiceKey === question.answer 
                          ? { color: 'green', fontWeight: 'bold' } 
                          : (userAnswers[questionIndex] === choiceKey 
                            ? { color: 'red', textDecoration: 'line-through' } 
                            : {}))
                        : {}
                    }>
                      {choiceText}
                    </span>
                  </label>
                </div>
              ))}
              
              {quizSubmitted && (
                <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#e8f4f8', borderRadius: '5px' }}>
                  <p style={{ fontWeight: 'bold' }}>Explanation:</p>
                  <p>{question.explanation}</p>
                </div>
              )}
            </div>
          ))}
          
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            {!quizSubmitted ? (
              <button 
                onClick={this.handleQuizSubmit}
                style={submitButtonStyle}
              >
                Submit Quiz
              </button>
            ) : (
              <div>
                <p style={{ marginBottom: '15px', fontWeight: 'bold' }}>
                  You got {this.state.correctAnswersCount} out of {quizData.length} correct!
                </p>
                <button 
                  onClick={this.closeQuizModal}
                  style={closeButtonStyle}
                >
                  Close Quiz
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  _showTitle() {
    if (this.state.conversation.length === 0) {
      return (
        <div className="version-toggle">
          <h2 className="chat-title">What can I help with?</h2>
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
            <div className="header-left">
              <h1 className="title">Chat UI</h1>
            </div>
            <div className="header-right">
              <div className="version-toggle">
                <NavLink to='/linkedIn'>
                  <button className="version-button left-button active">LinkedIn UI</button>
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
            {this._renderQuizModal()}
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
}

// Styles for the quiz modal
const quizModalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1000,
};

const quizModalStyle = {
  backgroundColor: 'white',
  padding: '20px',
  borderRadius: '10px',
  maxWidth: '800px',
  width: '90%',
  maxHeight: '90vh',
  overflow: 'auto',
  boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
};

const submitButtonStyle = {
  backgroundColor: '#0056b3',
  color: 'white',
  padding: '10px 20px',
  border: 'none',
  borderRadius: '5px',
  fontSize: '16px',
  cursor: 'pointer',
  fontWeight: 'bold',
};

const closeButtonStyle = {
  backgroundColor: '#555',
  color: 'white',
  padding: '10px 20px',
  border: 'none',
  borderRadius: '5px',
  fontSize: '16px',
  cursor: 'pointer',
  fontWeight: 'bold',
};

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

export default connect(mapStateToProps, mapDispatchToProps)(Contact);