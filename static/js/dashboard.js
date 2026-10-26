// Placeholder handler for buttons
document.querySelectorAll('[data-coming-soon]').forEach((button) => {
    button.addEventListener('click', () => {
        window.alert(`${button.dataset.comingSoon} is coming soon!`);
    });
});

// Browser-only preferences for acessibility features.
const preferenceKey = 'senior-medication-accessibility';
const palettes = ['default', 'blue-orange', 'purple-teal', 'grayscale'];
const defaults = { textSize: '100', bold: false, palette: 'default' };
let preferences = { ...defaults };
try {
    const saved = JSON.parse(localStorage.getItem(preferenceKey));
    if (saved && typeof saved === 'object') {
        preferences = {
            textSize: ['100', '125', '150', '200'].includes(saved.textSize) ? saved.textSize : '100',
            bold: saved.bold === true,
            palette: palettes.includes(saved.palette) ? saved.palette : 'default',
        };
    }
} catch {

}

const settingsDialog = document.getElementById('accessibility-settings');
const settingsButton = document.getElementById('open-settings');
const textSize = document.getElementById('text-size');
const boldText = document.getElementById('bold-text');
const colorPalette = document.getElementById('color-palette');
const feedback = document.getElementById('settings-feedback');

function applyPreferences() {
    document.documentElement.style.fontSize = `${preferences.textSize}%`;
    document.body.classList.toggle('bold-text', preferences.bold);
    document.body.dataset.palette = preferences.palette;
    document.body.classList.toggle('large-text', Number(preferences.textSize) >= 150);
    textSize.value = preferences.textSize;
    boldText.checked = preferences.bold;
    colorPalette.value = preferences.palette;
}

function savePreferences() {
    applyPreferences();
    try {
        localStorage.setItem(preferenceKey, JSON.stringify(preferences));
        feedback.textContent = 'Settings saved.';
    } catch {
        feedback.textContent = 'Settings applied for now. This browser could not save them.';
    }
}

settingsButton.addEventListener('click', () => {
    feedback.textContent = '';
    settingsDialog.showModal();
    textSize.focus();
});
document.getElementById('close-settings').addEventListener('click', () => settingsDialog.close());
settingsDialog.addEventListener('close', () => settingsButton.focus());
textSize.addEventListener('change', () => {
    preferences.textSize = textSize.value;
    savePreferences();
});
boldText.addEventListener('change', () => {
    preferences.bold = boldText.checked;
    savePreferences();
});
colorPalette.addEventListener('change', () => {
    preferences.palette = palettes.includes(colorPalette.value) ? colorPalette.value : 'default';
    savePreferences();
});
document.getElementById('reset-settings').addEventListener('click', () => {
    preferences = { ...defaults };
    savePreferences();
    feedback.textContent = feedback.textContent.replace('Settings saved.', 'Default settings restored.');
});
applyPreferences();

document.querySelectorAll('.remove-medication-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
        if (!window.confirm(`Remove ${form.dataset.medicationName}? This cannot be undone.`)) {
            event.preventDefault();
        }
    });
});


document.addEventListener("DOMContentLoaded", function () {

    const accountButton = document.getElementById("account-button");
    const accountMenu = document.getElementById("account-menu");

    const profileOption = document.getElementById("profile-option");
    const settingsOption = document.getElementById("account-settings-option");
    const logoutOption = document.getElementById("logout-option");

    function closeMenu() {
        accountMenu.hidden = true;
        accountButton.setAttribute("aria-expanded", "false");
    }

    accountButton.addEventListener("click", function () {
        const isOpening = accountMenu.hidden;
        accountMenu.hidden = !isOpening;
        accountButton.setAttribute("aria-expanded", String(isOpening));
    });

    profileOption.addEventListener("click", function () {
        window.location.href = "/profile";
    });

    settingsOption.addEventListener("click", function () {
        window.location.href = "/account-settings";
    });

    logoutOption.addEventListener("click", function () {
        closeMenu();
        alert("Logout functionality coming soon");
    });

    document.addEventListener("click", function (event) {
        if (!event.target.closest(".account-container")) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !accountMenu.hidden) {
            closeMenu();
            accountButton.focus();
        }
    });

});
