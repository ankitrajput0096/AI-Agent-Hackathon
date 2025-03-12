function constructPostBody(query) {
    return {
        query
    }
}
//can define more utils functions here

function constructPostBodyWithText(text, query) {
    return {
        text,
        query
    }
}

export default {
    constructPostBody,
    constructPostBodyWithText
    // can export more utils functions here
};