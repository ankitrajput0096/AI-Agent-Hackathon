import React, { Component } from 'react';
import { Navigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { actions as AuthActions, selectors as AuthSelectors } from './duck';
import Loader from '../Loader/loader';
import './auth.css';

class Login extends Component {
    constructor(props) {
        super(props);
        this.state = {
            username: '',
            password: '',
            redirectToHome: false
        };
    }

    static propTypes = {
        isFetching: PropTypes.bool.isRequired,
        isAuthenticated: PropTypes.bool.isRequired,
        error: PropTypes.string,
        loginUser: PropTypes.func.isRequired,
        clearError: PropTypes.func.isRequired
    };

    componentDidMount() {
        // Clear any previous errors
        this.props.clearError();
    }

    componentDidUpdate(prevProps) {
        // Redirect to home if login is successful
        if (!prevProps.isAuthenticated && this.props.isAuthenticated) {
            this.setState({ redirectToHome: true });
        }
    }

    handleChange = (event) => {
        this.setState({ [event.target.name]: event.target.value });
    };

    handleSubmit = (event) => {
        event.preventDefault();
        const { username, password } = this.state;
        const { loginUser } = this.props;
        
        if (username.trim() && password.trim()) {
            loginUser(username, password);
        }
    };

    render() {
        const { isFetching, isAuthenticated, error } = this.props;
        const { redirectToHome } = this.state;

        if (redirectToHome) {
            return <Navigate to="/about" />;
        }

        if (isFetching) {
            return <Loader />;
        }

        return (
            <div className="auth-container">
                <div className="auth-card">
                    <h2 className="auth-title">Login</h2>
                    
                    {error && <div className="auth-error">{error}</div>}
                    
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
                                placeholder="Enter your username"
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
                                placeholder="Enter your password"
                                required
                            />
                        </div>
                        
                        <button type="submit" className="auth-button">Login</button>
                    </form>
                    
                    <div className="auth-footer">
                        <p>Don't have an account? <a href="/register">Register</a></p>
                    </div>
                </div>
            </div>
        );
    }
}

const mapStateToProps = (state) => ({
    isFetching: AuthSelectors.isFetching(state),
    isAuthenticated: AuthSelectors.isAuthenticated(state),
    error: AuthSelectors.getError(state)
});

const mapDispatchToProps = (dispatch) =>
    bindActionCreators(
        {
            loginUser: AuthActions.loginUser,
            clearError: AuthActions.clearError
        },
        dispatch
    );

export default connect(mapStateToProps, mapDispatchToProps)(Login);