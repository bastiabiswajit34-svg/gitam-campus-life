/* ============================================================
   GITAM CAMPUS LIFE
   MAIN JAVASCRIPT
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* ========================================================
       AUTO-HIDE FLASH MESSAGES
       ======================================================== */

    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition = "opacity 0.5s ease";
            message.style.opacity = "0";

            setTimeout(function () {
                message.remove();
            }, 500);

        }, 5000);

    });


    /* ========================================================
       CONFIRM DELETE / ACTION FORMS
       ======================================================== */

    const confirmForms = document.querySelectorAll(
        "form[data-confirm]"
    );

    confirmForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const message = form.getAttribute("data-confirm");

            if (message && !confirm(message)) {
                event.preventDefault();
            }

        });

    });


    /* ========================================================
       CURRENT YEAR
       ======================================================== */

    const yearElements = document.querySelectorAll(
        "[data-current-year]"
    );

    yearElements.forEach(function (element) {
        element.textContent = new Date().getFullYear();
    });


    /* ========================================================
       MOBILE NAVIGATION
       ======================================================== */

    const menuButton = document.querySelector(
        "[data-menu-button]"
    );

    const navigation = document.querySelector(
        "[data-navigation]"
    );

    if (menuButton && navigation) {

        menuButton.addEventListener("click", function () {

            navigation.classList.toggle("mobile-open");

        });

    }


    /* ========================================================
       PASSWORD SHOW / HIDE
       ======================================================== */

    const passwordToggles = document.querySelectorAll(
        "[data-password-toggle]"
    );

    passwordToggles.forEach(function (toggle) {

        toggle.addEventListener("click", function () {

            const targetId =
                toggle.getAttribute("data-password-toggle");

            const passwordInput =
                document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }

            if (passwordInput.type === "password") {

                passwordInput.type = "text";
                toggle.textContent = "Hide Password";

            } else {

                passwordInput.type = "password";
                toggle.textContent = "Show Password";

            }

        });

    });


    /* ========================================================
       FORM SUBMIT LOADING STATE
       ======================================================== */

    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const submitButton =
                form.querySelector(
                    'button[type="submit"]'
                );

            if (!submitButton) {
                return;
            }

            /*
             * Do not disable buttons for forms that already
             * use JavaScript validation or confirmation.
             */

            if (submitButton.hasAttribute("data-no-loading")) {
                return;
            }

            submitButton.setAttribute(
                "data-original-text",
                submitButton.textContent
            );

            submitButton.textContent = "Processing...";

            /*
             * Keep the button enabled briefly so the browser
             * can complete the form submission normally.
             */

            setTimeout(function () {

                if (document.body.contains(submitButton)) {

                    submitButton.disabled = true;

                }

            }, 50);

        });

    });


    /* ========================================================
       DATE INPUT MINIMUM DATE
       ======================================================== */

    const today = new Date();

    const year = today.getFullYear();

    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        today.getDate()
    ).padStart(2, "0");

    const todayString =
        year + "-" + month + "-" + day;

    const futureDateInputs = document.querySelectorAll(
        'input[data-future-date]'
    );

    futureDateInputs.forEach(function (input) {

        input.min = todayString;

    });


    /* ========================================================
       PRINT BUTTON
       ======================================================== */

    const printButtons = document.querySelectorAll(
        "[data-print]"
    );

    printButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            window.print();

        });

    });


    /* ========================================================
       SEARCH / FILTER TABLES
       ======================================================== */

    const searchInputs = document.querySelectorAll(
        "[data-table-search]"
    );

    searchInputs.forEach(function (input) {

        const tableId =
            input.getAttribute("data-table-search");

        const table =
            document.getElementById(tableId);

        if (!table) {
            return;
        }

        input.addEventListener("input", function () {

            const searchText =
                input.value.toLowerCase().trim();

            const rows =
                table.querySelectorAll("tbody tr");

            rows.forEach(function (row) {

                const rowText =
                    row.textContent.toLowerCase();

                if (rowText.includes(searchText)) {

                    row.style.display = "";

                } else {

                    row.style.display = "none";

                }

            });

        });

    });


    /* ========================================================
       AUTO-RESIZE TEXTAREA
       ======================================================== */

    const textareas =
        document.querySelectorAll("textarea");

    textareas.forEach(function (textarea) {

        textarea.addEventListener("input", function () {

            textarea.style.height = "auto";

            textarea.style.height =
                textarea.scrollHeight + "px";

        });

    });


    /* ========================================================
       PREVENT DOUBLE CLICK ON ACTION BUTTONS
       ======================================================== */

    const actionForms =
        document.querySelectorAll(
            "form[data-prevent-double-submit]"
        );

    actionForms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const button =
                form.querySelector(
                    'button[type="submit"]'
                );

            if (!button) {
                return;
            }

            button.disabled = true;

            button.textContent = "Please wait...";

        });

    });


    /* ========================================================
       QR SCANNER / QR PLACEHOLDER MESSAGE
       ======================================================== */

    const qrButtons =
        document.querySelectorAll("[data-qr-action]");

    qrButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const action =
                button.getAttribute("data-qr-action");

            if (action === "scan") {

                alert(
                    "QR scanner will be connected to the campus system."
                );

            }

        });

    });


    /* ========================================================
       CONSOLE INFORMATION
       ======================================================== */

    console.log(
        "GITAM Campus Life 2.0 loaded successfully."
    );

    console.log(
        "MADE BY TEAM INNOVATORS HUB"
    );

});
