// rss.js
document.addEventListener('DOMContentLoaded', function() {
    // Handle default display mode selection
    const toggleModeSelect = document.getElementById('toggleMode');
    toggleModeSelect.addEventListener('change', function() {
        const selectedMode = toggleModeSelect.value;
        if (selectedMode === 'short') {
            // Set display mode to short description
            setDisplayMode('short');
        } else if (selectedMode === 'full') {
            // Set display mode to full content
            setDisplayMode('full');
        }
    });
});

function setDisplayMode(mode) {
    // Get all feed entries
    const feedEntries = document.querySelectorAll('.feed-entry');
    feedEntries.forEach(function(entry) {
        // Hide or show short description and full content based on the selected mode
        const shortDescription = entry.querySelector('.short-description');
        const fullContent = entry.querySelector('.full-content');
        if (mode === 'short') {
            shortDescription.style.display = 'block';
            fullContent.style.display = 'none';
        } else if (mode === 'full') {
            shortDescription.style.display = 'none';
            fullContent.style.display = 'block';
        }
    });
}


