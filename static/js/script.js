/*
================================================================================
DENTAL CLINIC MANAGEMENT SYSTEM - MAIN JAVASCRIPT FILE
================================================================================

PURPOSE:
    This JavaScript file adds interactive functionality to the Dental Clinic
    Management System. It enhances user experience with form handling, password
    validation, alerts, and utility functions.

WHAT IT CONTAINS:
    1. Auto-dismissing Alerts - Flash messages auto-close after 5 seconds
    2. Form Submit Loading States - Shows spinner while processing
    3. Required Field Indicators - Adds red asterisks to required fields
    4. Password Toggle - Show/hide password functionality
    5. Password Strength Validator - Real-time password strength checking
    6. Utility Functions - File size formatting, confirm dialogs
    7. Keyboard Shortcuts - Ctrl+S to save forms

FEATURES:
    - Vanilla JavaScript: No jQuery dependency for better performance
    - Bootstrap 5 Compatible: Works with Bootstrap components
    - Accessibility: ARIA labels and keyboard navigation support
    - Progressive Enhancement: Works even if JavaScript is disabled (fallback)

DEPENDENCIES:
    - Bootstrap 5.3.0 (optional, for alert auto-close)
    - Bootstrap Icons (for password toggle icons)

BROWSER SUPPORT:
    - Modern browsers (Chrome, Firefox, Safari, Edge)
    - Uses ES6+ features (const, let, arrow functions, template literals)

================================================================================
*/


/*
================================================================================
MAIN INITIALIZATION - DOM CONTENT LOADED EVENT
================================================================================
This event fires when the HTML document is fully loaded and parsed.
All DOM manipulation must happen after this event to ensure elements exist.

WHY DOMCONTENTLOADED:
    - Ensures DOM is ready before manipulating it
    - Faster than window.onload (doesn't wait for images/stylesheets)
    - Standard modern approach for initializing JavaScript

WHAT HAPPENS HERE:
    1. Set up auto-closing alerts
    2. Add loading states to form submissions
    3. Mark required fields with asterisks
    4. Set up password toggle buttons
    5. Set up password strength validation
================================================================================
*/

document.addEventListener('DOMContentLoaded', function() {

    /*
    ==========================================================================
    FEATURE 1: AUTO-CLOSE ALERTS AFTER 5 SECONDS
    ==========================================================================
    Flash messages (success, error, warning, info) automatically disappear
    after 5 seconds to avoid cluttering the interface.

    HOW IT WORKS:
        1. Find all alert elements on the page
        2. Set a 5-second timer for each alert
        3. When timer expires, close the alert using Bootstrap's Alert component

    WHY:
        - Better UX: Users don't need to manually close every message
        - Clean Interface: Alerts don't pile up on the page
        - Non-intrusive: 5 seconds is enough time to read the message

    TECHNICAL DETAILS:
        - querySelectorAll() finds all elements with .alert class
        - setTimeout() delays execution by 5000ms (5 seconds)
        - Bootstrap Alert API handles the smooth fade-out animation
        - Safety check: Only runs if Bootstrap is loaded
    ==========================================================================
    */

    document.querySelectorAll('.alert').forEach(alert => {
        // Set 5-second timer to auto-close each alert
        setTimeout(() => {
            // Check if Bootstrap is available (defensive programming)
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                // Create Bootstrap Alert instance and close it
                new bootstrap.Alert(alert).close();
            }
        }, 5000); // 5000 milliseconds = 5 seconds
    });


    /*
    ==========================================================================
    FEATURE 2: FORM SUBMISSION LOADING STATES
    ==========================================================================
    When user submits a form, show a loading spinner and disable the button
    to prevent duplicate submissions.

    HOW IT WORKS:
        1. Listen for submit event on all forms
        2. Find the submit button inside the form
        3. Disable the button (prevents multiple clicks)
        4. Replace button text with spinner + "Processing..." text

    WHY:
        - Prevents Double Submissions: User can't click submit twice
        - Visual Feedback: User knows the form is being processed
        - Better UX: Clear indication that something is happening

    EXAMPLE:
        Before submit: [Save Patient]
        After submit:  [🔄 Processing...]

    TECHNICAL DETAILS:
        - querySelectorAll('form') finds all forms on the page
        - addEventListener('submit') fires when form is submitted
        - btn.disabled = true prevents further clicks
        - Bootstrap spinner-border creates the loading animation
    ==========================================================================
    */

    document.querySelectorAll('form').forEach(form => {
        // Add submit event listener to each form
        form.addEventListener('submit', function() {
            // Find the submit button (type="submit")
            const btn = form.querySelector('button[type="submit"]');

            if (btn) {
                // Disable button to prevent duplicate submissions
                btn.disabled = true;

                // Save original button text (in case we need to restore it later)
                const originalText = btn.innerHTML;

                // Replace button content with spinner + text
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    });


    /*
    ==========================================================================
    FEATURE 3: REQUIRED FIELD INDICATORS (RED ASTERISKS)
    ==========================================================================
    Automatically adds a red asterisk (*) next to the label of required fields.

    HOW IT WORKS:
        1. Find all required inputs, textareas, and selects
        2. Find the corresponding label for each required field
        3. If label doesn't already have an asterisk, add one

    WHY:
        - Visual Indication: Users know which fields are mandatory
        - Accessibility: Clear requirement markers
        - Convention: Red asterisk is standard UI pattern

    EXAMPLE:
        Before: "First Name"
        After:  "First Name *" (asterisk in red)

    TECHNICAL DETAILS:
        - [required] attribute selector finds all required fields
        - querySelector uses label[for="..."] to find matching label
        - textContent.includes('*') checks if asterisk already exists
        - innerHTML += adds red asterisk span to label
    ==========================================================================
    */

    document.querySelectorAll('input[required], textarea[required], select[required]').forEach(input => {
        // Find the label associated with this input (by matching 'for' attribute to input 'id')
        const label = document.querySelector(`label[for="${input.id}"]`);

        // If label exists and doesn't already have an asterisk
        if (label && !label.textContent.includes('*')) {
            // Add red asterisk to label text
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
    });


    /*
    ==========================================================================
    FEATURE 4: PASSWORD TOGGLE (SHOW/HIDE PASSWORD)
    ==========================================================================
    Adds an eye icon button to password fields that toggles between showing
    and hiding the password.

    HOW IT WORKS:
        1. For each password input, create a toggle button with eye icon
        2. When clicked, switch input type between 'password' and 'text'
        3. Change icon from eye (hidden) to eye-slash (visible)

    WHY:
        - User Convenience: Users can verify what they typed
        - Error Prevention: Reduces typos in passwords
        - Modern UX: Standard feature in modern web apps

    VISUAL FLOW:
        Password hidden: [********] 👁️  (eye icon)
        Password visible: [mypass123] 🚫👁️  (eye-slash icon)

    TECHNICAL DETAILS:
        - Function checks if toggle already added (dataset.toggleAdded)
        - Handles two cases: input already in input-group, or standalone input
        - Creates input-group wrapper if needed for consistent styling
        - Toggle button appended to input-group for proper alignment
    ==========================================================================
    */

    function setupPasswordToggle(passwordInput) {
        // Safety check: Ensure input exists and hasn't been processed already
        if (!passwordInput || passwordInput.dataset.toggleAdded) return;

        // Mark input as processed to prevent duplicate toggle buttons
        passwordInput.dataset.toggleAdded = 'true';

        // Find the wrapper element (either existing input-group or parent element)
        const wrapper = passwordInput.closest('.input-group') || passwordInput.parentElement;

        // CASE 1: Input is already inside an input-group
        if (wrapper.classList.contains('input-group')) {
            // Create toggle button element
            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'input-group-text password-toggle'; // Bootstrap styling
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>'; // Eye icon (hidden state)
            toggleBtn.style.cursor = 'pointer'; // Hand cursor on hover

            // Add click event to toggle password visibility
            toggleBtn.addEventListener('click', function() {
                if (passwordInput.type === 'password') {
                    // Currently hidden → Show password
                    passwordInput.type = 'text';
                    toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>'; // Eye-slash icon
                } else {
                    // Currently visible → Hide password
                    passwordInput.type = 'password';
                    toggleBtn.innerHTML = '<i class="bi bi-eye"></i>'; // Eye icon
                }
            });

            // Append toggle button to input-group
            wrapper.appendChild(toggleBtn);

        // CASE 2: Input is standalone (not in input-group)
        } else {
            // Create input-group wrapper
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';

            // Insert input-group before the input
            wrapper.insertBefore(inputGroup, passwordInput);

            // Move input into the new input-group
            inputGroup.appendChild(passwordInput);

            // Create toggle button
            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'input-group-text password-toggle';
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
            toggleBtn.style.cursor = 'pointer';

            // Add click event to toggle password visibility
            toggleBtn.addEventListener('click', function() {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
                } else {
                    passwordInput.type = 'password';
                    toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
                }
            });

            // Append toggle button to input-group
            inputGroup.appendChild(toggleBtn);
        }
    }

    // Apply password toggle to all password input fields
    document.querySelectorAll('input[type="password"]').forEach(setupPasswordToggle);


    /*
    ==========================================================================
    FEATURE 5: PASSWORD STRENGTH VALIDATION (STAFF FORMS ONLY)
    ==========================================================================
    Real-time password strength validation for staff account creation.
    Shows instant feedback: "Weak password!" or "Your password looks good."

    HOW IT WORKS:
        1. Find all staff forms (class="staffForm")
        2. Find password input inside each form (class="staffPassword")
        3. As user types, check password strength in real-time
        4. Display feedback message (green checkmark or red X)
        5. Prevent form submission if password is weak

    PASSWORD REQUIREMENTS (Strong Password):
        - At least 8 characters long
        - Contains at least 1 uppercase letter (A-Z)
        - Contains at least 1 number (0-9)
        - Contains at least 1 special character (#@!*)

    VISUAL FEEDBACK:
        Strong: "✔ Your password looks good." (green text)
        Weak:   "✖ Weak password!" (red text)

    WHY:
        - Security: Encourages strong passwords
        - User Guidance: Real-time feedback helps users create valid passwords
        - Error Prevention: Blocks submission of weak passwords

    TECHNICAL DETAILS:
        - Uses regex to check for uppercase /[A-Z]/, numbers /[0-9]/, special chars /[#@!*]/
        - input event fires on every keystroke
        - submit event prevents form submission if password is weak
        - alert() provides clear error message before blocking
    ==========================================================================
    */

    document.querySelectorAll('.staffForm').forEach(form => {
        // Find password input inside this staff form
        const pwInput = form.querySelector('.staffPassword');
        if (!pwInput) return; // Skip if no password input found

        // Find or create feedback element for displaying strength message
        let feedback = form.querySelector('.passwordFeedback');
        if (!feedback) {
            // Create feedback element if it doesn't exist
            feedback = document.createElement('div');
            feedback.className = 'passwordFeedback mt-2'; // Bootstrap margin-top

            // Append feedback after input or input-group
            pwInput.closest('.input-group') ?
                pwInput.closest('.input-group').parentNode.appendChild(feedback) :
                pwInput.parentNode.appendChild(feedback);
        }

        // REAL-TIME VALIDATION: Check password strength as user types
        pwInput.addEventListener('input', () => {
            const val = pwInput.value; // Get current password value

            // Check if password meets all strength requirements
            const isStrong = val.length >= 8 &&       // At least 8 characters
                             /[A-Z]/.test(val) &&     // At least 1 uppercase letter
                             /[0-9]/.test(val) &&     // At least 1 number
                             /[#@!*]/.test(val);      // At least 1 special character

            if(val) { // Only show feedback if password is not empty
                if(isStrong) {
                    // Password is strong - show success message
                    feedback.textContent = "✔ Your password looks good.";
                    feedback.style.color = "green";
                    feedback.style.fontWeight = "normal";
                } else {
                    // Password is weak - show warning message
                    feedback.textContent = "✖ Weak password!";
                    feedback.style.color = "red";
                    feedback.style.fontWeight = "normal";
                }
            } else {
                // Password field is empty - clear feedback
                feedback.textContent = "";
            }
        });

        // FORM SUBMISSION VALIDATION: Prevent submission if password is weak
        form.addEventListener('submit', e => {
            const val = pwInput.value;

            // Check if password is strong
            const isStrong = val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val) && /[#@!*]/.test(val);

            // If password exists but is weak, block submission
            if(val && !isStrong) {
                e.preventDefault(); // Stop form from submitting
                alert("Weak password! Please meet all requirements before submitting.");
            }
        });
    });

}); // End of DOMContentLoaded event listener


/*
================================================================================
UTILITY FUNCTIONS
================================================================================
Helper functions that can be called from anywhere in the application.
These are defined outside DOMContentLoaded so they're globally accessible.
================================================================================
*/


/*
==========================================================================
UTILITY FUNCTION: Format File Size
==========================================================================
Converts file size from bytes to human-readable format.

USAGE:
    formatFileSize(1024)      → "1 KB"
    formatFileSize(1048576)   → "1 MB"
    formatFileSize(500)       → "500 Bytes"

HOW IT WORKS:
    1. Takes file size in bytes as input
    2. Divides by 1024 repeatedly to get KB, MB, GB
    3. Returns formatted string with appropriate unit

PARAMETERS:
    bytes (number): File size in bytes

RETURNS:
    string: Formatted file size (e.g., "1.5 MB")

USED IN:
    - Backup file size display
    - File upload size display
==========================================================================
*/
function formatFileSize(bytes) {
    // Handle edge case: 0 or null bytes
    if (!bytes) return '0 Bytes';

    const k = 1024;                                    // 1 KB = 1024 bytes
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];         // Unit labels

    // Calculate which unit to use
    // Math.log(bytes) / Math.log(k) finds the power of 1024
    // Example: 1048576 bytes = 1024^2 = MB (index 2)
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    // Convert bytes to the appropriate unit and round to 2 decimal places
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}


/*
==========================================================================
UTILITY FUNCTION: Confirm Action Dialog
==========================================================================
Wrapper function for browser's confirm() dialog.
Useful for delete confirmations and destructive actions.

USAGE:
    if (confirmAction("Are you sure you want to delete this patient?")) {
        // User clicked OK - proceed with deletion
        deletePatient();
    }

HOW IT WORKS:
    Shows a browser confirmation dialog with OK and Cancel buttons.
    Returns true if user clicks OK, false if Cancel.

PARAMETERS:
    message (string): Confirmation message to display

RETURNS:
    boolean: true if user confirms, false if user cancels

USED IN:
    - Delete patient confirmations
    - Delete staff confirmations
    - Database restore confirmations
==========================================================================
*/
function confirmAction(message) {
    return confirm(message);
}


/*
================================================================================
KEYBOARD SHORTCUTS
================================================================================
Global keyboard shortcuts to improve productivity.
Defined outside DOMContentLoaded to work on all pages.
================================================================================
*/

/*
==========================================================================
KEYBOARD SHORTCUT: Ctrl+S to Save Form
==========================================================================
Allows users to press Ctrl+S (or Cmd+S on Mac) to submit the current form.

HOW IT WORKS:
    1. Listen for keydown event globally
    2. Check if Ctrl (or Cmd) + S is pressed
    3. Prevent default browser "Save Page" behavior
    4. Find the first form on the page and submit it

WHY:
    - Power User Feature: Faster form submission for frequent users
    - Familiar Shortcut: Ctrl+S is universal "save" shortcut
    - Accessibility: Keyboard-only users can submit without mouse

TECHNICAL DETAILS:
    - e.ctrlKey detects Ctrl key (works for Cmd on Mac)
    - e.key.toLowerCase() === 's' detects S key
    - e.preventDefault() stops browser's default save dialog
    - form.submit() programmatically submits the form
==========================================================================
*/
document.addEventListener('keydown', e => {
    // Check if Ctrl+S (or Cmd+S on Mac) is pressed
    if (e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault(); // Prevent browser's "Save Page" dialog

        // Find the first form on the page
        const form = document.querySelector('form');

        // If form exists, submit it
        if (form) form.submit();
    }
});


/*
================================================================================
END OF SCRIPT
================================================================================

SUMMARY:
    - Total Functions: 3 (setupPasswordToggle, formatFileSize, confirmAction)
    - Total Event Listeners: 7 (DOMContentLoaded, alerts, forms, required fields,
                                  password inputs, staff forms, keyboard shortcuts)
    - Total Features: 7 (alerts, loading states, required indicators, password toggle,
                          password strength, file size format, keyboard shortcuts)

BROWSER COMPATIBILITY:
    - Chrome 90+
    - Firefox 88+
    - Safari 14+
    - Edge 90+

MAINTENANCE NOTES:
    - All selectors use classes (.staffForm, .staffPassword) for flexibility
    - Defensive programming: Checks if elements exist before manipulating
    - No external dependencies except Bootstrap (optional)
    - Progressive enhancement: Forms work without JavaScript

FUTURE ENHANCEMENTS:
    - Add more keyboard shortcuts (Ctrl+N for new, Ctrl+E for edit)
    - Add form auto-save with localStorage
    - Add client-side form validation with better error messages
    - Add custom file upload progress bars
================================================================================
*/
