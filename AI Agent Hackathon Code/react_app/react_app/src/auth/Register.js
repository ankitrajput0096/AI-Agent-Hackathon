import React, { Component } from 'react';
import { Navigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { actions as AuthActions, selectors as AuthSelectors } from './duck';
import Loader from '../Loader/loader';
import './auth.css';

class Register extends Component {
    constructor(props) {
        super(props);
        this.state = {
            username: '',
            password: '',
            confirmPassword: '',
            passwordError: '',
            redirectToAbout: false // Updated state variable
        };
    }

    static propTypes = {
        isFetching: PropTypes.bool.isRequired,
        isAuthenticated: PropTypes.bool.isRequired, // Added prop
        message: PropTypes.string,
        error: PropTypes.string,
        registerUser: PropTypes.func.isRequired,
        loginUser: PropTypes.func.isRequired, // Added prop
        clearError: PropTypes.func.isRequired
    };

    componentDidMount() {
        this.props.clearError();
    }

    componentDidUpdate(prevProps) {
        const { message, isAuthenticated } = this.props;

        // After successful registration, trigger login
        if (!prevProps.message && message) {
            const { username, password } = this.state;
            this.props.loginUser(username, password);
        }

        // Redirect after successful login
        if (!prevProps.isAuthenticated && isAuthenticated) {
            this.setState({ redirectToAbout: true });
        }
    }

    handleChange = (event) => {
        this.setState({ 
            [event.target.name]: event.target.value,
            passwordError: ''
        });
    };

    validateForm = () => {
        const { password, confirmPassword } = this.state;
        if (password !== confirmPassword) {
            this.setState({ passwordError: 'Passwords do not match' });
            return false;
        }
        return true;
    };

    handleSubmit = (event) => {
        event.preventDefault();
        if (this.validateForm()) {
            const { username, password } = this.state;
            this.props.registerUser(username, password);
        }
    };

    render() {
        const { isFetching, message, error } = this.props;
        const { passwordError, redirectToAbout } = this.state;

        if (redirectToAbout) {
            return <Navigate to="/about" replace />; // Updated redirect
        }

        if (isFetching) {
            return <Loader />;
        }

        return (
            <div className="auth-container">
                <div className="auth-card">
                    <h2 className="auth-title">Register</h2>
                    
                    {message && <div className="auth-success">{message}</div>}
                    {error && <div className="auth-error">{error}</div>}
                    {passwordError && <div className="auth-error">{passwordError}</div>}
                    
                    <form className="auth-form" onSubmit={this.handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="username">Username</label>
                            <input
                                type="text"
                                id="username"
                                name="username"
                                value={this.state.username}
                                onChange={this.handleChange}
                                className="auth-input"
                                placeholder="Choose a username"
                                required
                            />
                        </div>
                        
                        <div className="form-group">
                            <label htmlFor="password">Password</label>
                            <input
                                type="password"
                                id="password"
                                name="password"
                                value={this.state.password}
                                onChange={this.handleChange}
                                className="auth-input"
                                placeholder="Choose a password"
                                required
                            />
                        </div>
                        
                        <div className="form-group">
                            <label htmlFor="confirmPassword">Confirm Password</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                name="confirmPassword"
                                value={this.state.confirmPassword}
                                onChange={this.handleChange}
                                className="auth-input"
                                placeholder="Confirm your password"
                                required
                            />
                        </div>
                        
                        <button type="submit" className="auth-button">Register</button>
                    </form>
                    
                    <div className="auth-footer">
                        <p>Already have an account? <a href="/login">Login</a></p>
                    </div>
                </div>
            </div>
        );
    }
}

const mapStateToProps = (state) => ({
    isFetching: AuthSelectors.isFetching(state),
    isAuthenticated: AuthSelectors.isAuthenticated(state), // Added
    message: AuthSelectors.getMessage(state),
    error: AuthSelectors.getError(state)
});

const mapDispatchToProps = (dispatch) =>
    bindActionCreators(
        {
            registerUser: AuthActions.registerUser,
            loginUser: AuthActions.loginUser, // Added
            clearError: AuthActions.clearError
        },
        dispatch
    );

export default connect(mapStateToProps, mapDispatchToProps)(Register);