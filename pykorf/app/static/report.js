document.addEventListener('DOMContentLoaded', function () {

  // Copy path buttons
  document.querySelectorAll('.copy-path-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var sourceId = this.dataset.copySource;
      var el = document.getElementById(sourceId);
      var text = el ? el.value.trim() : '';
      if (!text) return;
      navigator.clipboard.writeText(text).then(function() {
        var icon = btn.querySelector('i');
        icon.className = 'bi bi-clipboard-check';
        setTimeout(function() { icon.className = 'bi bi-clipboard'; }, 2000);
      });
    });
  });

  // Spinner on submit
  ['report-form', 'export-form', 'batch-form', 'import-form'].forEach(function(id) {
    var form = document.getElementById(id);
    if (!form) return;
    form.addEventListener('submit', function() {
      var btn = this.querySelector('button[type="submit"]');
      var spinner = this.querySelector('.spinner-border');
      if (btn) btn.disabled = true;
      if (spinner) spinner.classList.remove('d-none');
    });
  });

});
