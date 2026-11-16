document.addEventListener("DOMContentLoaded", function () {

    const togglePasswordButton = document.getElementById("toggle-password-button");
    const passwordFormContainer = document.getElementById("password-form-container");
    const currentPasswordInput = document.getElementById("current_password");

    const toggleDeleteButton = document.getElementById("toggle-delete-button");
    const deleteFormContainer = document.getElementById("delete-form-container");

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

});