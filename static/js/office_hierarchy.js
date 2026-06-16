(function () {
    "use strict";

    function getModal() {
        return document.getElementById("newUnitModal");
    }

    function openModal() {
        var modal = getModal();
        if (!modal) {
            return;
        }
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        var firstField = modal.querySelector("select, input, button");
        if (firstField) {
            firstField.focus();
        }
    }

    function closeModal() {
        var modal = getModal();
        if (!modal) {
            return;
        }
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    }

    function clearFormErrors(form) {
        form.querySelectorAll(".new-unit-modal__field").forEach(function (field) {
            field.classList.remove("has-error");
        });
        form.querySelectorAll("[data-error-for]").forEach(function (error) {
            error.textContent = "";
        });
        var formErrors = form.querySelector("[data-form-errors]");
        if (formErrors) {
            formErrors.hidden = true;
            formErrors.textContent = "";
        }
    }

    function showFormErrors(form, errors) {
        clearFormErrors(form);
        var handled = false;

        Object.keys(errors || {}).forEach(function (fieldName) {
            var messages = errors[fieldName] || [];
            var message = messages.join(" ");
            var errorTarget = form.querySelector('[data-error-for="' + fieldName + '"]');
            var input = form.querySelector('[name="' + fieldName + '"]');

            if (errorTarget) {
                errorTarget.textContent = message;
                handled = true;
            }

            if (input) {
                var field = input.closest(".new-unit-modal__field");
                if (field) {
                    field.classList.add("has-error");
                }
            }
        });

        if (!handled) {
            var formErrors = form.querySelector("[data-form-errors]");
            if (formErrors) {
                formErrors.textContent = "Please correct the errors and try again.";
                formErrors.hidden = false;
            }
        }
    }

    function wireModal() {
        document.querySelectorAll("[data-modal-open]").forEach(function (button) {
            button.addEventListener("click", openModal);
        });

        document.querySelectorAll("[data-modal-close]").forEach(function (button) {
            button.addEventListener("click", closeModal);
        });

        var modal = getModal();
        if (modal) {
            modal.addEventListener("click", function (event) {
                if (event.target === modal) {
                    closeModal();
                }
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeModal();
            }
        });
    }

    function wireHierarchyRows() {
        document.querySelectorAll(".office-hierarchy__row").forEach(function (row) {
            row.addEventListener("click", function () {
                if (row.disabled) {
                    return;
                }

                var node = row.closest(".office-hierarchy__node");
                if (!node) {
                    return;
                }

                var isExpanded = node.classList.toggle("expanded");
                node.classList.toggle("collapsed", !isExpanded);
                row.setAttribute("aria-expanded", isExpanded ? "true" : "false");
            });
        });
    }

    function wireCategoryButtons() {
        document.querySelectorAll("[data-category-filter]").forEach(function (button) {
            button.addEventListener("click", function () {
                document.querySelectorAll("[data-category-filter]").forEach(function (item) {
                    item.classList.remove("is-active");
                });
                button.classList.add("is-active");
            });
        });
    }

    function applyOfficeSearch() {
        var input = document.querySelector("[data-office-search]");
        var cards = Array.prototype.slice.call(document.querySelectorAll("[data-office-card]"));
        var empty = document.querySelector("[data-filtered-empty]");

        if (!input || !cards.length) {
            return;
        }

        var query = input.value.trim().toLowerCase();
        var visibleCount = 0;

        cards.forEach(function (card) {
            var text = (card.getAttribute("data-office-search-text") || "").toLowerCase();
            var isVisible = !query || text.indexOf(query) !== -1;
            card.hidden = !isVisible;
            if (isVisible) {
                visibleCount += 1;
            }
        });

        if (empty) {
            empty.hidden = visibleCount !== 0;
        }
    }

    function wireOfficeSearch() {
        var input = document.querySelector("[data-office-search]");
        if (!input) {
            return;
        }

        input.addEventListener("input", applyOfficeSearch);
        applyOfficeSearch();
    }

    function wireCreateForm() {
        var form = document.getElementById("createOfficeForm");
        if (!form) {
            return;
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            clearFormErrors(form);

            var submit = form.querySelector(".new-unit-modal__submit");
            if (submit) {
                submit.disabled = true;
                submit.textContent = "Creating...";
            }

            fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                credentials: "same-origin"
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        return {
                            ok: response.ok,
                            status: response.status,
                            data: data
                        };
                    });
                })
                .then(function (result) {
                    if (result.ok && result.data && result.data.office && result.data.office.id) {
                        var modal = getModal();
                        var baseUrl = modal ? modal.getAttribute("data-office-base-url") : "";
                        window.location.href = baseUrl + result.data.office.id + "/";
                        return;
                    }

                    if (result.data && result.data.errors) {
                        showFormErrors(form, result.data.errors);
                    } else {
                        showFormErrors(form, {});
                    }
                })
                .catch(function () {
                    var formErrors = form.querySelector("[data-form-errors]");
                    if (formErrors) {
                        formErrors.textContent = "The unit could not be created. Please try again.";
                        formErrors.hidden = false;
                    }
                })
                .finally(function () {
                    if (submit) {
                        submit.disabled = false;
                        submit.textContent = "Create Unit";
                    }
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        wireModal();
        wireHierarchyRows();
        wireCategoryButtons();
        wireOfficeSearch();
        wireCreateForm();
    });
})();
