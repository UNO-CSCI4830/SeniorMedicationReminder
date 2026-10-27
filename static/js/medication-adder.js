const medicationAdder = document.getElementById('medication-adder');
const openMedicationAdder = document.getElementById('open-medication-adder');
const medicationForm = document.getElementById('medication-form');
const medicationSteps = [...medicationForm.querySelectorAll('.medication-step')];
const medicationFields = medicationSteps.map(step => step.querySelector('input, select'));
const stepIndicators = [...medicationForm.querySelectorAll('.form-progress li')];
const previousStepButton = document.getElementById('medication-previous');
const nextStepButton = document.getElementById('medication-next');
const submitMedicationButton = document.getElementById('medication-submit');
const medicationFeedback = document.getElementById('medication-save-feedback');
let medicationStep = 0;
let savingMedication = false;

function showMedicationStep(index) {
    medicationStep = index;
    medicationSteps.forEach((step, position) => {
        step.hidden = position !== index;
        stepIndicators[position].classList.toggle('completed', position < index);
        if (position === index) stepIndicators[position].setAttribute('aria-current', 'step');
        else stepIndicators[position].removeAttribute('aria-current');
    });
    previousStepButton.hidden = index === 0;
    nextStepButton.hidden = index === medicationSteps.length - 1;
    submitMedicationButton.hidden = !nextStepButton.hidden;
    document.getElementById('medication-step-description').textContent =
        `Step ${index + 1} of ${medicationSteps.length}: ${stepIndicators[index].textContent}`;
    medicationFields[index].focus();
}

function validateMedicationField(field) {
    field.setCustomValidity('');
    if (!field.value.trim()) field.setCustomValidity('Please complete this field.');
    return field.checkValidity();
}
medicationFields.forEach(field => field.addEventListener('input', () => field.setCustomValidity('')));

openMedicationAdder.addEventListener('click', () => {
    medicationAdder.showModal();
    showMedicationStep(medicationStep);
});
document.getElementById('close-medication-adder').addEventListener('click', () => medicationAdder.close());
medicationAdder.addEventListener('close', () => openMedicationAdder.focus());
previousStepButton.addEventListener('click', () => {
    if (!savingMedication && medicationStep > 0) showMedicationStep(medicationStep - 1);
});
nextStepButton.addEventListener('click', () => {
    if (savingMedication) return;
    const field = medicationFields[medicationStep];
    if (!validateMedicationField(field)) return field.reportValidity();
    if (medicationStep < medicationSteps.length - 1) showMedicationStep(medicationStep + 1);
});
// Enter advances an input's step; it only saves on the final step.
medicationForm.addEventListener('keydown', event => {
    if (event.key === 'Enter' && event.target.tagName === 'INPUT') {
        event.preventDefault();
        if (nextStepButton.hidden) medicationForm.requestSubmit();
        else nextStepButton.click();
    }
});
medicationForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (savingMedication) return;
    if (!nextStepButton.hidden) return nextStepButton.click();
    const invalidIndex = medicationFields.findIndex(field => !validateMedicationField(field));
    if (invalidIndex !== -1) {
        showMedicationStep(invalidIndex);
        medicationFields[invalidIndex].reportValidity();
        return;
    }
    const payload = Object.fromEntries(new FormData(medicationForm));
    for (const key of Object.keys(payload)) payload[key] = payload[key].trim();
    payload.reminder_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    savingMedication = true;
    submitMedicationButton.disabled = true;
    previousStepButton.disabled = true;
    medicationFeedback.textContent = 'Saving medication...';
    try {
        const response = await fetch(medicationForm.action, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            throw new Error(result.error || 'Unable to save. Please try again.');
        }
        window.location.reload();
    } catch (error) {
        medicationFeedback.textContent = error.message || 'Unable to connect. Please try again.';
        savingMedication = false;
        submitMedicationButton.disabled = false;
        previousStepButton.disabled = false;
    }
});
