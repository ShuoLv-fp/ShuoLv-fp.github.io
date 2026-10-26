document.addEventListener('DOMContentLoaded', function() {
  try {
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (!darkModeToggle) {
      console.error('Dark mode toggle button not found');
      return;
    }

    const sunIcon = darkModeToggle.querySelector('.sun-icon');
    const moonIcon = darkModeToggle.querySelector('.moon-icon');
    
    if (!sunIcon || !moonIcon) {
      console.error('Dark mode icons not found');
      return;
    }

    function applyTheme(theme) {
      const darkMode = theme === 'dark';

      if (darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
      } else {
        document.documentElement.removeAttribute('data-theme');
        sunIcon.style.display = 'block';
        moonIcon.style.display = 'none';
      }
    }

    function toggleDarkMode() {
      const darkMode = document.documentElement.getAttribute('data-theme') === 'dark';

      if (!darkMode) {
        localStorage.setItem('theme', 'dark');
        applyTheme('dark');
      } else {
        localStorage.setItem('theme', 'light');
        applyTheme('light');
      }
    }

    const savedTheme = localStorage.getItem('theme');
    applyTheme(savedTheme === 'dark' ? 'dark' : 'light');

    // Add click event listener
    darkModeToggle.addEventListener('click', toggleDarkMode);

    // Add keyboard event listener for accessibility
    darkModeToggle.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleDarkMode();
      }
    });

  } catch (error) {
    console.error('Error initializing dark mode:', error);
  }
});
