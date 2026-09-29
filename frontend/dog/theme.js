(function () {
    const storageKey = 'pawai-theme';

    function currentTheme() {
        return localStorage.getItem(storageKey) === 'dark' ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        const isLight = theme === 'light';
        document.body.classList.toggle('light-theme', isLight);
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.setAttribute('aria-label', isLight ? 'Switch to dark mode' : 'Switch to light mode');
            toggle.setAttribute('title', isLight ? 'Switch to dark mode' : 'Switch to light mode');
        }
    }

    function initialize() {
        applyTheme(currentTheme());
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.addEventListener('click', function () {
                const nextTheme = document.body.classList.contains('light-theme') ? 'dark' : 'light';
                localStorage.setItem(storageKey, nextTheme);
                applyTheme(nextTheme);
            });
        }
    }

    document.addEventListener('DOMContentLoaded', initialize);
    window.addEventListener('storage', function (event) {
        if (event.key === storageKey) applyTheme(currentTheme());
    });
    window.PawAITheme = { apply: applyTheme, current: currentTheme };
})();
