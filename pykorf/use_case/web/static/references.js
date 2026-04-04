// Live filter on reference table
document.getElementById('ref-filter').addEventListener('input', function () {
  var q = this.value.toLowerCase();
  document.querySelectorAll('#ref-table tbody tr').forEach(function (row) {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

// Edit reference: populate add form and delete the original record
function editReference(btn) {
  var id = btn.dataset.refId;
  var ref = JSON.parse(btn.dataset.ref);

  // Delete the existing record so the form re-adds it fresh
  var formData = new FormData();
  formData.append('ref_id', id);
  fetch('/model/references/delete', { method: 'POST', body: formData });

  // Remove the row from the table immediately
  var row = btn.closest('tr');
  if (row) row.remove();

  document.getElementById('edit-id-hidden').value = '';
  document.getElementById('add-name').value = ref.name;
  document.getElementById('add-link').value = ref.link;
  document.getElementById('add-description').value = ref.description || '';
  var sel = document.getElementById('add-category');
  for (var i = 0; i < sel.options.length; i++) {
    if (sel.options[i].value === ref.category) { sel.selectedIndex = i; break; }
  }

  var addBtn = document.getElementById('add-btn');
  addBtn.innerHTML = '<i class="bi bi-pencil me-1"></i>Update Reference';
  addBtn.classList.remove('btn-success');
  addBtn.classList.add('btn-warning');

  var formBody = document.getElementById('add-form-body');
  if (!formBody.classList.contains('show')) {
    formBody.classList.add('show');
  }

  document.getElementById('add-name').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
