const medicationList = document.querySelector('[data-status-url]');
let statusRequestPending = false;

function displayLocalMedicationTimes() {
    const clock = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    const fullDate = new Intl.DateTimeFormat('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: 'numeric', minute: '2-digit', hour12: true, timeZoneName: 'short',
    });
    document.querySelectorAll('[data-scheduled-at]').forEach(card => {
        const due = new Date(Number(card.dataset.scheduledAt) * 1000);
        const doseTime = card.querySelector('.dose-time');
        if (doseTime) doseTime.textContent = clock.format(due);
        const scheduledDate = card.querySelector('.scheduled-date');
        scheduledDate.textContent = fullDate.format(due);
        scheduledDate.dateTime = due.toISOString();
    });
}
displayLocalMedicationTimes();

async function refreshMedicationStatuses() {
    if (!medicationList || statusRequestPending || document.hidden) return;
    displayLocalMedicationTimes();
    statusRequestPending = true;
    const feedback = document.getElementById('status-sync-feedback');
    try {
        const response = await fetch(medicationList.dataset.statusUrl, { cache: 'no-store' });
        if (!response.ok) throw new Error('Status refresh failed');
        const medications = await response.json();
        for (const medication of medications) {
            const card = medicationList.querySelector(`[data-medication-id="${medication.id}"]`);
            if (!card) continue;
            card.dataset.scheduledAt = medication.scheduled_at;
            const badge = card.querySelector('.status');
            badge.className = `status status-${medication.status}`;
            badge.textContent = medication.status[0].toUpperCase() + medication.status.slice(1);
            const late = card.querySelector('.late-label');
            late.textContent = medication.late_label;
            late.hidden = !medication.late_label;
            const button = card.querySelector('.status-form button');
            if (button) {
                button.disabled = medication.status === 'taken';
                button.textContent = button.disabled ? 'Taken' : 'Mark as taken';
            }
        }
        displayLocalMedicationTimes();
        feedback.textContent = '';
    } catch {
        feedback.textContent = 'Status updates are temporarily unavailable. Reconnecting...';
    } finally {
        statusRequestPending = false;
    }
}

setInterval(refreshMedicationStatuses, 15000);
document.addEventListener('visibilitychange', refreshMedicationStatuses);
window.addEventListener('focus', refreshMedicationStatuses);
