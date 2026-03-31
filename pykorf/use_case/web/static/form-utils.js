/**
 * pyKorf Web UI — generic loading-spinner on any data-loading form.
 */

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('form[data-loading]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn    = form.querySelector('button[type="submit"]');
      var spinner = form.querySelector('.spinner-border');
      if (btn)     btn.disabled = true;
      if (spinner) spinner.classList.remove('d-none');
    });
  });
});
