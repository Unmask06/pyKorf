function getFilename(path) {
  if (!path) return '';
  // Use Path-like logic: split by both / and \ and get last part
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1] || '';
}

function updateFilenameLabel() {
  const path = document.getElementById('kdf_path').value;
  document.getElementById('filename-label').textContent = getFilename(path);
}

document.getElementById('open-form').addEventListener('submit', function () {
  document.getElementById('open-btn').disabled = true;
  document.getElementById('open-spinner').classList.remove('d-none');
});

document.addEventListener('DOMContentLoaded', function () {
  const kdfPathInput = document.getElementById('kdf_path');
  const openForm = document.getElementById('open-form');

  // Update filename label on input
  kdfPathInput.addEventListener('input', updateFilenameLabel);

  document.querySelectorAll('.recent-file-open-btn').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      kdfPathInput.value = this.dataset.path;
      updateFilenameLabel();
      openForm.submit();
    });
  });
});
