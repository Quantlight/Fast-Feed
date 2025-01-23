var popup = document.getElementById("popup");
var button = document.getElementById("add_articles");
var articles = document.querySelectorAll(".list-group-item")

// When the button is clicked, show the popup
button.onclick = function() {
  popup.style.display = "block";
}

// Function to close the popup when the close button is clicked
function closePopup() {
  popup.style.display = "none";
}