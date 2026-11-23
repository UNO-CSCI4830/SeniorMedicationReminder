document.addEventListener("DOMContentLoaded", function () {

    const togglePasswordButton = document.getElementById("toggle-password-button");
    const passwordFormContainer = document.getElementById("password-form-container");
    const currentPasswordInput = document.getElementById("current_password");

    const toggleDeleteButton = document.getElementById("toggle-delete-button");
    const deleteFormContainer = document.getElementById("delete-form-container");

    const toggleGuardianButton = document.getElementById("toggle-guardian-button");
    const guardianFormContainer = document.getElementById("guardian-form-container");
    const guardianEmailInput = document.getElementById("guardian_email");

    const togglePhoneButton = document.getElementById("toggle-phone-button");
    const phoneFormContainer = document.getElementById("phone-form-container");
    const phoneNumberInput = document.getElementById("phone_number");

    if (togglePasswordButton && passwordFormContainer) {
        togglePasswordButton.addEventListener("click", function () {
            const isOpening = passwordFormContainer.hidden;
            passwordFormContainer.hidden = !isOpening;
            togglePasswordButton.textContent = isOpening ? "Cancel" : "Change";
            togglePasswordButton.setAttribute("aria-expanded", String(isOpening));

            if (isOpening && currentPasswordInput) {
                currentPasswordInput.focus();
            }
        });
    }

    if (toggleDeleteButton && deleteFormContainer) {
        toggleDeleteButton.addEventListener("click", function () {
            const isOpening = deleteFormContainer.hidden;
            deleteFormContainer.hidden = !isOpening;
            toggleDeleteButton.textContent = isOpening ? "Cancel" : "Delete";
            toggleDeleteButton.setAttribute("aria-expanded", String(isOpening));
        });
    }

    if (toggleGuardianButton && guardianFormContainer) {
        const defaultGuardianLabel = toggleGuardianButton.dataset.defaultLabel || "Add";

        toggleGuardianButton.addEventListener("click", function () {
            const isOpening = guardianFormContainer.hidden;
            guardianFormContainer.hidden = !isOpening;
            toggleGuardianButton.textContent = isOpening ? "Cancel" : defaultGuardianLabel;
            toggleGuardianButton.setAttribute("aria-expanded", String(isOpening));

            if (isOpening && guardianEmailInput) {
                guardianEmailInput.focus();
            }
        });
    }

    if (togglePhoneButton && phoneFormContainer) {
    const defaultPhoneLabel = togglePhoneButton.dataset.defaultLabel || "Add";

        togglePhoneButton.addEventListener("click", function () {
            const isOpening = phoneFormContainer.hidden;
            phoneFormContainer.hidden = !isOpening;
            togglePhoneButton.textContent = isOpening ? "Cancel" : defaultPhoneLabel;
            togglePhoneButton.setAttribute("aria-expanded", String(isOpening));

            if (isOpening && phoneNumberInput) {
                phoneNumberInput.focus();
            }
        });
    }
    
});