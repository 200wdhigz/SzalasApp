(() => {
    'use strict'

    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme()
        if (storedTheme) {
            return storedTheme
        }

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }

    const setTheme = theme => {
        if (theme === 'auto') {
            document.documentElement.setAttribute('data-bs-theme', (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
        } else {
            document.documentElement.setAttribute('data-bs-theme', theme)
        }
    }

    const updateIconClasses = (theme) => {
        const themeSwitcherIcon = document.querySelector('#bd-theme i');
        if (theme === 'dark') {
            themeSwitcherIcon.className = 'bi bi-moon-stars-fill';
        } else if (theme === 'light') {
            themeSwitcherIcon.className = 'bi bi-sun-fill';
        } else {
            themeSwitcherIcon.className = 'bi bi-circle-half';
        }
    }

    setTheme(getPreferredTheme())

    const showActiveTheme = (theme, focus = false) => {
        const themeSwitcher = document.querySelector('#bd-theme');

        if (!themeSwitcher) {
            console.error('Element with id "bd-theme" not found.');
            return;
        }

        const themeSwitcherText = document.querySelector('#bd-theme-text');
        if (!themeSwitcherText) {
            console.error('Element with id "bd-theme-text" not found.');
            return;
        }

        const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`);
        if (!btnToActive) {
            console.error(`Element with data-bs-theme-value="${theme}" not found.`);
            return;
        }

        document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
            element.classList.remove('active');
            element.setAttribute('aria-pressed', 'false');
            const checkIcon = element.querySelector('.bi-check2');
            if (checkIcon) {
                checkIcon.classList.add('d-none');
            }
        });

        btnToActive.classList.add('active');
        btnToActive.setAttribute('aria-pressed', 'true');
        const checkIcon = btnToActive.querySelector('.bi-check2');
        if (checkIcon) {
            checkIcon.classList.remove('d-none');
        }
        const themeSwitcherLabel = `${themeSwitcherText.textContent} (${btnToActive.dataset.bsThemeValue})`;
        themeSwitcher.setAttribute('aria-label', themeSwitcherLabel);

        updateIconClasses(theme);

        if (focus) {
            themeSwitcher.focus();
        }
    };

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme()
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme())
        }
    })

    window.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme())

        document.querySelectorAll('[data-bs-theme-value]')
            .forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const theme = toggle.getAttribute('data-bs-theme-value')
                    setStoredTheme(theme)
                    setTheme(theme)
                    showActiveTheme(theme, true)
                })
            })
    })
})()