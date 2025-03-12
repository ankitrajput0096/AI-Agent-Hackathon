function constructLoginBody(username, password) {
    return {
        username,
        password
    };
}

function constructRegisterBody(username, password) {
    return {
        username,
        password
    };
}

function constructLogoutBody() {
    return {};
}

export default {
    constructLoginBody,
    constructRegisterBody,
    constructLogoutBody
};