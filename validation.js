const form = document.getElementById('form')
const firstname_input = document.getElementById('firstname-input')
const lastname_input = document.getElementById('lastname-input')
const phone_input = document.getElementById('phone-input')
const email_input = document.getElementById('email-input')
const password_input = document.getElementById('password-input')
const confirm_password_input = document.getElementById('confirm-password-input')
const guardian_checkbox = document.getElementById('guardian-checkbox')
const guardian_fields = document.getElementById('guardian-fields')
const guardian_name_input = document.getElementById('guardian-name-input')
const guardian_phone_input = document.getElementById('guardian-phone-input')
const guardian_email_input = document.getElementById('guardian-email-input')
const contact_input = document.getElementById('contact-input')
const error_message = document.getElementById('error-message')
const success_message = document.getElementById('success-message')

function isValidEmail(email){
    email = email.trim()
    let atIndex = email.indexOf('@')
    let dotIndex = email.lastIndexOf('.')

    return atIndex > 0 && dotIndex > atIndex + 1 && dotIndex < email.length - 1
}

function isValidPhone(phone){
    let digitCount = 0

    for(let i = 0; i < phone.length; i++){
        if(phone[i] >= '0' && phone[i] <= '9'){
            digitCount++
        }
    }

    return digitCount >= 10
}

function flag(input){
    input.parentElement.classList.add('incorrect')
}

form.addEventListener('submit', (e) => {
    let errors = []

    if(firstname_input){
        errors = getSignupFormErrors()
    }
    else if(contact_input){
        errors = getForgotPasswordErrors()
        e.preventDefault()
        if(errors.length === 0){
            success_message.innerText = 'If an account matches ' + contact_input.value.trim() + ', a reset link is on its way.'
            form.reset()
        }
    }
    else{
        errors = getLoginFormErrors(email_input.value, password_input.value)
    }

    if(errors.length > 0){
        e.preventDefault()
        if(success_message) success_message.innerText = ''
        error_message.innerText = errors.join(". ")
    }
})

function getSignupFormErrors(){
    let errors = []

    if(firstname_input.value.trim() === ''){
        errors.push('First name is required')
        flag(firstname_input)
    }
    if(lastname_input.value.trim() === ''){
        errors.push('Last name is required')
        flag(lastname_input)
    }
    if(phone_input.value.trim() === ''){
        errors.push('Phone number is required')
        flag(phone_input)
    }
    else if(!isValidPhone(phone_input.value)){
        errors.push('Enter a valid phone number')
        flag(phone_input)
    }
    if(email_input.value.trim() === ''){
        errors.push('Email is required')
        flag(email_input)
    }
    else if(!isValidEmail(email_input.value)){
        errors.push('Enter a valid email')
        flag(email_input)
    }
    if(password_input.value === ''){
        errors.push('Password is required')
        flag(password_input)
    }
    else if(password_input.value.length < 8){
        errors.push('Password must have at least 8 characters')
        flag(password_input)
    }
    if(password_input.value !== confirm_password_input.value){
        errors.push('Passwords do not match')
        flag(confirm_password_input)
    }

    if(guardian_checkbox.checked){
        if(guardian_name_input.value.trim() === ''){
            errors.push('Guardian full name is required')
            flag(guardian_name_input)
        }
        if(guardian_phone_input.value.trim() === ''){
            errors.push('Guardian phone number is required')
            flag(guardian_phone_input)
        }
        else if(!isValidPhone(guardian_phone_input.value)){
            errors.push('Enter a valid guardian phone number')
            flag(guardian_phone_input)
        }
        if(guardian_email_input.value.trim() === ''){
            errors.push('Guardian email is required')
            flag(guardian_email_input)
        }
        else if(!isValidEmail(guardian_email_input.value)){
            errors.push('Enter a valid guardian email')
            flag(guardian_email_input)
        }
    }

    return errors
}

function getLoginFormErrors(email, password){
    let errors = []

    if(email.trim() === ''){
        errors.push('Email is required')
        flag(email_input)
    }
    if(password === ''){
        errors.push('Password is required')
        flag(password_input)
    }

    return errors
}

function getForgotPasswordErrors(){
    let errors = []
    const value = contact_input.value.trim()

    if(value === ''){
        errors.push('Enter your email or phone number')
        flag(contact_input)
    }
    else if(!isValidEmail(value) && !isValidPhone(value)){
        errors.push('Enter a valid email or phone number')
        flag(contact_input)
    }

    return errors
}

if(guardian_checkbox){
    const guardianInputs = [guardian_name_input, guardian_phone_input, guardian_email_input]

    function updateGuardianSection(){
        const show = guardian_checkbox.checked
        guardian_fields.classList.toggle('hidden', !show)
        guardianInputs.forEach(input => {
            input.required = show
            if(!show){
                input.value = ''
                input.parentElement.classList.remove('incorrect')
            }
        })
    }

    guardian_checkbox.addEventListener('change', updateGuardianSection)
    updateGuardianSection()
}

const allInputs = Array.from(form.querySelectorAll('input')).filter(input => input.type !== 'checkbox')

allInputs.forEach(input => {
    input.addEventListener('input', () => {
        if(input.parentElement.classList.contains('incorrect')){
            input.parentElement.classList.remove('incorrect')
            error_message.innerText = ''
        }
    })
})
