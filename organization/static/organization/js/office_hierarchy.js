document.addEventListener('click', (event) => {
    const link = event.target.closest('.hierarchy-node__name');
    if (link) {
        event.stopPropagation();
    }
});

const modal = document.querySelector('[data-new-unit-modal]');
const openModalButton = document.querySelector('[data-open-new-unit-modal]');
const modalForm = document.querySelector('[data-new-unit-form]');
const closeModalButtons = document.querySelectorAll('[data-close-new-unit-modal]');
const formErrors = document.querySelector('[data-form-errors]');

function clearFormErrors() {
    if (formErrors) {
        formErrors.hidden = true;
        formErrors.textContent = '';
    }

    document.querySelectorAll('[data-error-for]').forEach((errorNode) => {
        errorNode.textContent = '';
    });
}

function openNewUnitModal() {
    if (!modal) {
        return;
    }

    clearFormErrors();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');

    const firstField = modal.querySelector('select, input:not([type="hidden"]), button');
    if (firstField) {
        firstField.focus();
    }
}

function closeNewUnitModal() {
    if (!modal) {
        return;
    }

    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');

    if (openModalButton) {
        openModalButton.focus();
    }
}

function showFormErrors(errors) {
    clearFormErrors();

    Object.entries(errors || {}).forEach(([fieldName, messages]) => {
        const errorNode = document.querySelector(`[data-error-for="${fieldName}"]`);
        const message = Array.isArray(messages) ? messages.join(' ') : String(messages);

        if (errorNode) {
            errorNode.textContent = message;
        } else if (formErrors) {
            formErrors.hidden = false;
            formErrors.textContent = [formErrors.textContent, message].filter(Boolean).join(' ');
        }
    });
}

if (openModalButton) {
    openModalButton.addEventListener('click', (event) => {
        event.preventDefault();
        openNewUnitModal();
    });
}

closeModalButtons.forEach((button) => {
    button.addEventListener('click', () => {
        closeNewUnitModal();
    });
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal?.classList.contains('is-open')) {
        closeNewUnitModal();
    }
});

if (modalForm) {
    modalForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearFormErrors();

        const submitButton = modalForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Creating...';
        }

        try {
            const response = await fetch(modalForm.action, {
                method: 'POST',
                body: new FormData(modalForm),
                headers: {
                    Accept: 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });

            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                window.location.href = response.url || modalForm.action;
                return;
            }

            const payload = await response.json();
            if (response.ok && payload.success) {
                closeNewUnitModal();
                window.location.reload();
                return;
            }

            showFormErrors(payload.errors || { __all__: payload.message || 'Please correct the errors below.' });
        } catch (error) {
            if (formErrors) {
                formErrors.hidden = false;
                formErrors.textContent = 'Unable to create the unit right now. Please try again.';
            }
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Create Unit';
            }
        }
    });
}
