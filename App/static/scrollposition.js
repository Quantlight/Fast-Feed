// Save scroll position before form submission
function saveScrollPosition() {
    sessionStorage.setItem('scrollPos', window.scrollY);
}

// Restore scroll position after page load
window.addEventListener('load', function() {
    const savedScroll = sessionStorage.getItem('scrollPos');
    if (savedScroll) {
        window.scrollTo(0, savedScroll);
        sessionStorage.removeItem('scrollPos');
    }
});