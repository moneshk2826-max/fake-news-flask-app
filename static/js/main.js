document.addEventListener('DOMContentLoaded', function() {
    function isValidSearchInput(value) {
        const text = (value || '').trim();
        if (!text) {
            return false;
        }

        const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/i;
        if (urlPattern.test(text)) {
            return true;
        }

        const words = text.match(/[A-Za-z0-9']+/g) || [];
        const alphaWords = words.filter(function(word) {
            return /[A-Za-z]/.test(word);
        });
        const uniqueWords = new Set(alphaWords.map(function(word) {
            return word.toLowerCase();
        }));

        return text.length >= 15 &&
            words.length >= 4 &&
            alphaWords.length >= 4 &&
            (alphaWords.length === 0 ? false : (uniqueWords.size / alphaWords.length) >= 0.6);
    }

    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(msg) {
        setTimeout(function() {
            msg.style.animation = 'slideOutRight 0.4s ease forwards';
            setTimeout(function() { msg.remove(); }, 400);
        }, 4000);
    });

    // Fade-in animation for elements
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card, .table-wrapper, .form-card').forEach(function(el) {
        observer.observe(el);
    });

    // Add slideOutRight keyframe
    const style = document.createElement('style');
    style.textContent = '@keyframes slideOutRight { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(40px); } }';
    document.head.appendChild(style);

    document.querySelectorAll('.search-box').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const input = form.querySelector('input[name="search"], input[name="urls"]');
            if (!input || isValidSearchInput(input.value)) {
                return;
            }

            event.preventDefault();
            alert('Please enter a full news headline with at least 4 words or a valid http/https URL.');
            input.focus();
        });
    });
});
