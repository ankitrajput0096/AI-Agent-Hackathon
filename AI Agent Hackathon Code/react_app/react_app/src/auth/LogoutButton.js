import React from 'react';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { actions as AuthActions, selectors as AuthSelectors } from './duck';
import './auth.css';
import { Navigate } from 'react-router-dom';

class LogoutButton extends React.Component {
    state = {
        redirectToHome: false
    };

    static propTypes = {
        logoutUser: PropTypes.func.isRequired,
        isAuthenticated: PropTypes.bool.isRequired,
        username: PropTypes.string
    };

    handleLogout = () => {
        this.props.logoutUser();
        this.setState({ redirectToHome: true });
    };

    render() {
        const { isAuthenticated, username } = this.props;

        if (this.state.redirectToHome) {
            return <Navigate to="/" replace />;
        }

        if (!isAuthenticated) {
            return null;
        }

        return (
            <div className="logout-container" onClick={this.handleLogout}>
                {/* <span className="user-greeting">Hello, {username || 'User'}</span> */}
                {/* <button className="logout-button" onClick={this.handleLogout}> */}
                {/* <span className="version-button right-button>
                    Logout
                </span> */}

                <button className="version-button right-button active">Logout</button>
                


                {/* </button> */}
            </div>
        );
    }
}

const mapStateToProps = (state) => ({
    isAuthenticated: AuthSelectors.isAuthenticated(state),
    username: AuthSelectors.getUser(state)
});

const mapDispatchToProps = (dispatch) =>
    bindActionCreators(
        {
            logoutUser: AuthActions.logoutUser
        },
        dispatch
    );

export default connect(mapStateToProps, mapDispatchToProps)(LogoutButton);