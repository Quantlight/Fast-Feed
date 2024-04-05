document.addEventListener('DOMContentLoaded', function() {
  const themeToggle = document.getElementById('themeToggle');
  let currentTheme = getCookie('theme') || 'light'; // Default theme is light if cookie doesn't exist
  document.documentElement.setAttribute('data-theme', currentTheme);

  themeToggle.addEventListener('click', function() {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      setCookie('theme', newTheme, 365); // Set cookie to expire in 365 days
      currentTheme = newTheme; // Update currentTheme variable
  });
});

function setCookie(name, value, days) {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = name + '=' + value + ';expires=' + expires.toUTCString() + ';path=/';
}

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
          return cookie.substring(name.length + 1);
      }
  }
  return null;
}
