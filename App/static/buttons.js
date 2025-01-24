document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // Function to handle AJAX toggling
    async function toggleState(endpoint, button, iconClassTrue, iconClassFalse, buttonTextTrue, buttonTextFalse) {
        const entryId = button.dataset.entryId;
        try {
            const response = await fetch(endpoint.replace('0', entryId), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                // Update button appearance
                const icon = button.querySelector('i');
                if (data.is_unread || data.is_starred || data.is_read_later) {
                    button.classList.add('btn-success');
                    icon.className = iconClassTrue;
                    button.innerHTML = `<i class="${iconClassTrue}"></i> ${buttonTextTrue}`;
                } else {
                    button.classList.remove('btn-success');
                    icon.className = iconClassFalse;
                    button.innerHTML = `<i class="${iconClassFalse}"></i> ${buttonTextFalse}`;
                }
                // showNotification(data.message);
            } else {
                showNotification('An error occurred. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to update. Please check your connection.');
        }
    }

    // Attach event listeners to buttons
    document.querySelectorAll('.toggle-unread').forEach(button => {
        button.addEventListener('click', () => {
            toggleState(
                '/toggle_unread/0', // URL with placeholder
                button,
                'fas fa-envelope-open-text', // Icon for unread
                'far fa-envelope', // Icon for read
                '', // Text for unread
                '' // Text for read
            );
        });
    });

    document.querySelectorAll('.toggle-starred').forEach(button => {
        button.addEventListener('click', () => {
            toggleState(
                '/toggle_starred/0',
                button,
                'fas fa-star',
                'far fa-star',
                '',
                ''
            ).then(data => {
                // Update similarity score if request was successful
                if (data.status === 'success') {
                    const scoreElement = document.getElementById(`similarity-${button.dataset.entryId}`);
                    if (scoreElement) {
                        const formattedScore = (data.similarity_score * 100).toFixed(1);
                        scoreElement.textContent = formattedScore;
                    }
                }
            });
        });
    });

    document.querySelectorAll('.toggle-read-later').forEach(button => {
        button.addEventListener('click', () => {
            toggleState(
                '/toggle_read_later/0', // URL with placeholder
                button,
                'fas fa-bookmark', // Icon for read later
                'far fa-bookmark', // Icon for not read later
                '', // Text for read later
                '' // Text for not read later
            );
        });
    });

    function showNotification(message) {
        // Replace this with a proper notification library (e.g., Toastr)
        alert(message); // Temporary solution
    }
});