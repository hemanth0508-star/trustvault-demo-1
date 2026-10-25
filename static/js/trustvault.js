document.querySelectorAll("[data-previous-button]").forEach((link) => {
    link.addEventListener("click", (event) => {
        if (!document.referrer) return;

        const previousPage = new URL(document.referrer);
        if (previousPage.origin === window.location.origin) {
            event.preventDefault();
            window.history.back();
        }
    });
});
