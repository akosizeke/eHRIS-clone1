/**
 * Office Hierarchy - Frontend functionality
 */

(function() {
    'use strict';

    // Modal management
    window.openNewUnitModal = function() {
        const modal = document.getElementById('newUnitModal');
        if (modal) {
            modal.classList.add('active');
        }
    };

    window.closeNewUnitModal = function() {
        const modal = document.getElementById('newUnitModal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // Close modal when clicking outside
    document.addEventListener('DOMContentLoaded', function() {
        const modal = document.getElementById('newUnitModal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeNewUnitModal();
                }
            });
        }

        // Tree node toggle
        document.querySelectorAll('.tree-node-title').forEach(el => {
            el.addEventListener('click', function(e) {
                // Don't toggle if clicking on a link
                if (e.target.tagName === 'A') return;
                
                const node = this.closest('.tree-node');
                if (node) {
                    node.classList.toggle('collapsed');
                    node.classList.toggle('expanded');
                }
            });
        });

        // Apply form field classes for styling
        document.querySelectorAll('form input, form select, form textarea').forEach(field => {
            if (!field.classList.contains('form-input') && 
                !field.classList.contains('form-select') && 
                !field.classList.contains('form-textarea')) {
                
                if (field.tagName === 'SELECT') {
                    field.classList.add('form-select');
                } else if (field.tagName === 'TEXTAREA') {
                    field.classList.add('form-textarea');
                } else if (field.type === 'checkbox') {
                    // Leave checkboxes as is
                } else {
                    field.classList.add('form-input');
                }
            }
        });

        // Form validation on submit
        const form = document.getElementById('createOfficeForm');
        if (form) {
            form.addEventListener('submit', function(e) {
                // Basic client-side validation
                const organization = form.querySelector('[name="organization"]');
                const name = form.querySelector('[name="name"]');
                const officeType = form.querySelector('[name="office_type"]');

                if (!organization.value) {
                    e.preventDefault();
                    alert('Please select an organization');
                    return false;
                }
                if (!name.value.trim()) {
                    e.preventDefault();
                    alert('Please enter a name');
                    return false;
                }
                if (!officeType.value) {
                    e.preventDefault();
                    alert('Please select an office type');
                    return false;
                }
            });
        }
    });

    // Filter by type (if needed for future enhancement)
    window.filterByType = function(type) {
        console.log('Filter by type:', type);
        // TODO: Implement filtering logic if needed
    };
})();
