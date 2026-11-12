const medicationAdder = document.getElementById('medication-adder');
const openMedicationAdder = document.getElementById('open-medication-adder');
const medicationForm = document.getElementById('medication-form');
const medicationSteps = [...medicationForm.querySelectorAll('.medication-step')];
const medicationFields = medicationSteps.map(step => [...step.querySelectorAll('input, select')]);
const frequencyField = medicationForm.elements.reminder_frequency;
const dayField = medicationForm.elements.reminder_day;
const timeField = medicationForm.elements.reminder_time;
const dayContainer = document.getElementById('medication-day-field');
const medicationSummary = document.getElementById('medication-summary');
const stepIndicators = [...medicationForm.querySelectorAll('.form-progress li')];
const previousStepButton = document.getElementById('medication-previous');
const nextStepButton = document.getElementById('medication-next');
const submitMedicationButton = document.getElementById('medication-submit');
const medicationFeedback = document.getElementById('medication-save-feedback');
let medicationStep = 0;
let savingMedication = false;
let dialogTrigger = openMedicationAdder;
const closeMedicationAdder = document.getElementById('close-medication-adder');

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
    updateReminderSummary();
    medicationFields[index][0].focus();
}

function updateReminderSummary() {
    const frequency = frequencyField.value;
    const requiresDay = frequency === 'once' || frequency === 'weekly';
    dayContainer.hidden = !requiresDay;
    dayField.disabled = !requiresDay;

    if (!frequency || !timeField.value || (requiresDay && !dayField.value)) {
        medicationSummary.textContent = '';
        return;
    }
    const [hour, minute] = timeField.value.split(':').map(Number);
    const time = new Date(2000, 0, 1, hour, minute).toLocaleTimeString([], {
        hour: 'numeric', minute: '2-digit',
    });
    const schedule = frequency === 'daily' ? 'Daily' :
        `${frequency === 'weekly' ? 'Weekly' : 'Once'} on ${dayField.value}`;
    const [name, dose] = medicationFields[0].map(field => field.value.trim());
    medicationSummary.textContent = `${name} · ${dose} · ${schedule} at ${time}`;
}

function isInvalidMedicationField(field) {
    if (field.disabled) return false;
    field.setCustomValidity('');
    if (!field.value.trim()) field.setCustomValidity('Please complete this field.');
    return !field.checkValidity();
}
medicationForm.addEventListener('input', event => {
    event.target.setCustomValidity('');
    if (event.target === frequencyField) dayField.setCustomValidity('');
    if (medicationStep === 1) updateReminderSummary();
});

function openMedicationForm(trigger) {
    dialogTrigger = trigger;
    const { editUrl, name, doseAmount, frequency, day, time } = trigger.dataset;
    medicationForm.reset();
    medicationFields.flat().forEach(field => field.setCustomValidity(''));
    medicationFeedback.textContent = '';
    document.getElementById('medication-adder-title').textContent = editUrl ? 'Edit Medication' : 'Add Medication';
    if (editUrl) {
        medicationForm.elements.name.value = name;
        medicationForm.elements.dose_amount.value = doseAmount;
        frequencyField.value = frequency;
        dayField.value = day;
        timeField.value = time;
    }
    medicationAdder.showModal();
    showMedicationStep(0);
}

openMedicationAdder.addEventListener('click', () => openMedicationForm(openMedicationAdder));
document.querySelectorAll('.edit-medication-button').forEach(button => {
    button.addEventListener('click', () => openMedicationForm(button));
});
closeMedicationAdder.addEventListener('click', () => medicationAdder.close());
medicationAdder.addEventListener('cancel', event => {
    if (savingMedication) event.preventDefault();
});
medicationAdder.addEventListener('close', () => dialogTrigger.focus());
previousStepButton.addEventListener('click', () => {
    if (!savingMedication && medicationStep > 0) showMedicationStep(medicationStep - 1);
});
nextStepButton.addEventListener('click', () => {
    if (savingMedication) return;
    const field = medicationFields[medicationStep].find(isInvalidMedicationField);
    if (field) return field.reportValidity();
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
    const invalidField = medicationFields.flat().find(isInvalidMedicationField);
    if (invalidField) {
        showMedicationStep(medicationFields.findIndex(fields => fields.includes(invalidField)));
        invalidField.reportValidity();
        return;
    }
    const payload = Object.fromEntries(new FormData(medicationForm));
    for (const key of Object.keys(payload)) payload[key] = payload[key].trim();
    const editUrl = dialogTrigger.dataset.editUrl;
    if (!editUrl) payload.reminder_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    savingMedication = true;
    submitMedicationButton.disabled = true;
    previousStepButton.disabled = true;
    closeMedicationAdder.disabled = true;
    medicationFeedback.textContent = 'Saving medication...';
    try {
        const response = await fetch(editUrl || medicationForm.action, {
            method: editUrl ? 'PATCH' : 'POST',
            headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
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
        closeMedicationAdder.disabled = false;
    }
});
