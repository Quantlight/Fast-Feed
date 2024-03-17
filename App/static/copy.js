    document.addEventListener('DOMContentLoaded', function () {
        const copyButtons = document.querySelectorAll('.copy-btn');
        
        copyButtons.forEach(button => {
            button.addEventListener('click', () => {
                const listItem = button.closest('.list-group-item');
                const fullContent = listItem.querySelector('.full-content');
                
                // Create a textarea element to hold the text
                const textarea = document.createElement('textarea');
                textarea.value = fullContent.textContent;
                document.body.appendChild(textarea);
                
                // Select and copy the text
                textarea.select();
                document.execCommand('copy');
                
                // Remove the textarea
                document.body.removeChild(textarea);
                
                // Alert or show a message indicating successful copy
                alert('Content copied to clipboard!');
            });
        });
    });

document.addEventListener('DOMContentLoaded', function () {
    const decreaseWidthBtn = document.getElementById('decrease-width-btn');
    const increaseWidthBtn = document.getElementById('increase-width-btn');
    const widthInput = document.getElementById('width-input');
    const listItems = document.querySelectorAll('.list-group-item');

    decreaseWidthBtn.addEventListener('click', function () {
        listItems.forEach(item => {
            item.style.width = '45%'; // Set width to 45% for two items per row
        });
    });

    increaseWidthBtn.addEventListener('click', function () {
        listItems.forEach(item => {
            item.style.width = '100%'; // Set width back to 100% for one item per row
        });
    });

    widthInput.addEventListener('input', function () {
        listItems.forEach(item => {
            item.style.width = widthInput.value + 'px'; // Set width based on user input for each item
        });
    });
});



