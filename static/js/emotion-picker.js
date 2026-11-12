/* Emotion dropdowns: show the chosen level in the closed row, then close. */
document.querySelectorAll('details.emo').forEach(function (box) {
    var current = box.querySelector('.emo-current');

    box.addEventListener('change', function (event) {
        var radio = event.target;
        if (!radio.matches('input[type=radio]')) return;
        if (radio.value) {
            current.textContent = radio.value + ' \u00b7 ' + radio.dataset.mental;
            current.classList.add('is-set');
        } else {
            current.textContent = 'Not rated';
            current.classList.remove('is-set');
        }
        box.open = false;
        box.querySelector('summary').focus();
    });

    box.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && box.open) {
            box.open = false;
            box.querySelector('summary').focus();
        }
    });

    // Opening one closes the others so the form doesn't grow without end.
    box.addEventListener('toggle', function () {
        if (!box.open) return;
        document.querySelectorAll('details.emo[open]').forEach(function (other) {
            if (other !== box) other.open = false;
        });
    });
});
