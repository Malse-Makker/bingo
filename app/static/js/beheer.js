// Confirmation prompt for the destructive actions on the admin page.

document.addEventListener("DOMContentLoaded", function () {
  Array.prototype.forEach.call(
    document.querySelectorAll(".js-bevestig"),
    function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.dataset.vraag)) {
          e.preventDefault();
        }
      });
    }
  );
});
