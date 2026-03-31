function getFilename(path) {
  if (!path) return '';
  const parts = path.split(/[\/\\]/);
  return parts[parts.length - 1] || '';
}

function updateFilenameLabel(inputId, labelId) {
  const path = document.getElementById(inputId).value;
  document.getElementById(labelId).textContent = getFilename(path);
}

document.addEventListener('DOMContentLoaded', function () {
  // Spinner on submit
  ['pms-form', 'hmb-form'].forEach(function (id) {
    document.getElementById(id).addEventListener('submit', function () {
      var btn = this.querySelector('button[type="submit"]');
      var spinner = this.querySelector('.spinner-border');
      if (btn) btn.disabled = true;
      if (spinner) spinner.classList.remove('d-none');
    });
  });

  // Filename label updates
  document.getElementById('pms_source').addEventListener('input', function() {
    updateFilenameLabel('pms_source', 'pms-filename-label');
  });
  document.getElementById('hmb_source').addEventListener('input', function() {
    updateFilenameLabel('hmb_source', 'hmb-filename-label');
  });
});
