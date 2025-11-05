document.addEventListener('DOMContentLoaded', function() {

    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                new bootstrap.Alert(alert).close();
            }
        }, 5000);
    });

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                const originalText = btn.innerHTML;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    });

    document.querySelectorAll('input[required], textarea[required], select[required]').forEach(input => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label && !label.textContent.includes('*')) {
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
    });

    function setupPasswordToggle(passwordInput) {
        if (!passwordInput || passwordInput.dataset.toggleAdded) return;
        
        passwordInput.dataset.toggleAdded = 'true';
        
        const wrapper = passwordInput.closest('.input-group') || passwordInput.parentElement;
        
        if (wrapper.classList.contains('input-group')) {
            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'input-group-text password-toggle';
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
            toggleBtn.style.cursor = 'pointer';
            
            toggleBtn.addEventListener('click', function() {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
                } else {
                    passwordInput.type = 'password';
                    toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
                }
            });
            
            wrapper.appendChild(toggleBtn);
        } else {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';
            
            wrapper.insertBefore(inputGroup, passwordInput);
            inputGroup.appendChild(passwordInput);
            
            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'input-group-text password-toggle';
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
            toggleBtn.style.cursor = 'pointer';
            
            toggleBtn.addEventListener('click', function() {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
                } else {
                    passwordInput.type = 'password';
                    toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
                }
            });
            
            inputGroup.appendChild(toggleBtn);
        }
    }

    document.querySelectorAll('input[type="password"]').forEach(setupPasswordToggle);

    document.querySelectorAll('.staffForm').forEach(form => {
        const pwInput = form.querySelector('.staffPassword');
        if (!pwInput) return;

        let feedback = form.querySelector('.passwordFeedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'passwordFeedback mt-2';
            pwInput.closest('.input-group') ? 
                pwInput.closest('.input-group').parentNode.appendChild(feedback) :
                pwInput.parentNode.appendChild(feedback);
        }

        pwInput.addEventListener('input', () => {
            const val = pwInput.value;
            const isStrong = val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val) && /[#@!*]/.test(val);

            if(val) {
                if(isStrong) {
                    feedback.textContent = "✔ Your password looks good.";
                    feedback.style.color = "green";
                    feedback.style.fontWeight = "normal";
                } else {
                    feedback.textContent = "✖ Weak password!";
                    feedback.style.color = "red";
                    feedback.style.fontWeight = "normal";
                }
            } else {
                feedback.textContent = "";
            }
        });

        form.addEventListener('submit', e => {
            const val = pwInput.value;
            const isStrong = val.length >= 8 && /[A-Z]/.test(val) && /[0-9]/.test(val) && /[#@!*]/.test(val);
            if(val && !isStrong) {
                e.preventDefault();
                alert("Weak password! Please meet all requirements before submitting.");
            }
        });
    });

});

function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function confirmAction(message) {
    return confirm(message);
}

document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) form.submit();
    }
});
