// if username is missing
function usernameValidation(id) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {

        // if username missing
        if ($('#' + id).val() == "") {
            // calling wrapAlert function
            wrapAlert(id, id + ' Misssing');
            return false;
        } else {
            // if all good call warpSuccess
            wrapSuccess(id)
            return true;
        }
    }
}

// if password is missing
function passwordValidation(id) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {
        // password missing
        if ($('#' + id).val() == "") {
            // wrapAlert function
            wrapAlert(id, id + ' Misssing')
            return false;
        } else {
            // wrapSuccess function
            wrapSuccess(id)
            return true;
        }
    }
}

// if user forget to confirms the password or if passwords not match
function passwordConfirmation(id1, id2) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {
        var result1 = false,
            result2 = false;

        // if first password field is empty
        if ($('#' + id1).val() == '') {
            wrapAlert(id1, id1 + ' Missing')
        } else {
            wrapSuccess(id1);
            result1 = true;
        }

        // if user not confirms the password or password not matched
        if ($('#' + id2).val() == "") {
            wrapAlert(id2, 'confirm your ' + id1)
        } else if ($('#' + id1).val() != $('#' + id2).val()) {
            // if password not matched
            wrapAlert(id2, 'password does not match')
        } else {
            wrapSuccess(id2)
            result2 = true;
        }

        return (result1 && result2);
    }
}

// if symbol is missing
function symbolValidation(id) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {

        // symbol missing or symbol value is null
        if ($('#' + id).val() == '' || $('#' + id).val() == null) {
            wrapAlert(id, 'Missing ' + id)
            return false;
        } else {
            wrapSuccess(id)
            return true;
        }
    }
}

// if number of shares is missing
function sharesValidation(id) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {

        // share is missing
        if ($('#' + id).val() == '') {
            wrapAlert(id, 'Missing Number of Shares')
            return false;
        } else if (parseInt($('#' + id).val()) <= 0) {
            // or if share value is not positive integer
            wrapAlert(id, 'positive integer only')
            return false;
        } else {
            wrapSuccess(id)
            return true;
        }
    }
}

// if the checkbox is not tick
function checkValidation(id) {

    // checking if Submit button is first clicked
    if (isSubmitClick) {

        // if checkbox is not ticked
        if ($('#' + id).prop('checked') == false) {
            $('#' + id + 'Text').css('color', 'red');
            wrapAlert(id, 'Tick the check Box')
            return false;
        } else {
            $('#' + id + 'Text').css('color', '#6c757d');
            wrapSuccess(id);
            return true;
        }
    }
}

// wrapAlert function for error messages
function wrapAlert(id, message) {
    // changing border color to red
    $('#' + id).css('border', 'rgb(255, 153, 153) solid 1px');
    // adding the message with alertTooltip class declare in static/style.css
    $('#' + id + 'Tooltip').fadeIn().html('&#9888; ' + message).addClass('alertTooltip');
    return this;
};

// warpSuccess function if success
function wrapSuccess(id) {
    // changing border of the input field to color green
    $('#' + id).css('border', '#28a745 solid 1px');
    // removing the alert message if any from the wrapAlert function with fadeOut animation
    $('#' + id + 'Tooltip').fadeOut();
}
