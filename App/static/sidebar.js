$(document).ready(function() {

    $('#sidebarToggle').on('click', function() {
        $('#sidebar').toggleClass('active');
    });

    $('#sidebarClose').on('click', function() {
        $('#sidebar').removeClass('active');
    });

});
