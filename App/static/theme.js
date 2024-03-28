document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    requestAnimationFrame(() => {
        document.documentElement.setAttribute('data-theme', 'dark');
      });
  
    themeToggle.addEventListener('click', function() {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
      document.documentElement.setAttribute('data-theme', newTheme);
    });
  });