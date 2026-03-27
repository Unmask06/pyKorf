/**
 * pyKorf Web UI — shared helpers.
 * Kept minimal: no framework, no build step.
 */

// Show a loading spinner on the submit button of any form with data-loading="true"
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('form[data-loading]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type="submit"]');
      var spinner = form.querySelector('.spinner-border');
      if (btn) btn.disabled = true;
      if (spinner) spinner.classList.remove('d-none');
    });
  });
});
