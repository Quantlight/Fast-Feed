// Get the button element
var backToTopButton = document.getElementById("back-to-top");

// Function to handle scroll event
window.onscroll = function() {scrollFunction()};
function scrollFunction() {
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        backToTopButton.style.display = "block";
    } else {
        backToTopButton.style.display = "none";
    }
}
// Function to handle click event on the button
backToTopButton.addEventListener("click", function() {
    // Scroll to the top of the page smoothly
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
});