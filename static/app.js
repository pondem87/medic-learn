// Progressively enhance the mobile navigation; links stay visible without JavaScript.
(() => {
    const toggle = document.querySelector('[data-nav-toggle]');
    const navigation = document.getElementById('site-navigation');
    if (!toggle || !navigation) return;

    const desktop = window.matchMedia('(min-width: 992px)');
    const setExpanded = (expanded) => {
        toggle.setAttribute('aria-expanded', String(expanded));
        navigation.hidden = !expanded;
    };
    const syncViewport = () => {
        toggle.hidden = desktop.matches;
        setExpanded(desktop.matches);
    };

    toggle.addEventListener('click', () => {
        setExpanded(toggle.getAttribute('aria-expanded') !== 'true');
    });
    navigation.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !desktop.matches) {
            setExpanded(false);
            toggle.focus();
        }
    });
    desktop.addEventListener('change', syncViewport);
    syncViewport();
})();
