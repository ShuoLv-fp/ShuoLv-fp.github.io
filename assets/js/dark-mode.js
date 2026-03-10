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

    function toggleDarkMode() {
      const darkMode = localStorage.getItem('darkMode') === 'enabled';
      
      if (!darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('darkMode', 'enabled');
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
      } else {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('darkMode', null);
        sunIcon.style.display = 'block';
        moonIcon.style.display = 'none';
      }
    }

    // Initialize dark mode from localStorage
    if (localStorage.getItem('darkMode') === 'enabled') {
      document.documentElement.setAttribute('data-theme', 'dark');
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'block';
    }

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
