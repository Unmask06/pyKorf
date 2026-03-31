// Live filter on reference table
document.getElementById('ref-filter').addEventListener('input', function () {
  var q = this.value.toLowerCase();
  document.querySelectorAll('#ref-table tbody tr').forEach(function (row) {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});

// Open edit modal and pre-fill fields
function openEdit(id, ref) {
  document.getElementById('edit-id').value   = id;
  document.getElementById('edit-name').value = ref.name;
  document.getElementById('edit-link').value = ref.link;
  document.getElementById('edit-description').value = ref.description || '';
  var sel = document.getElementById('edit-category');
  for (var i = 0; i < sel.options.length; i++) {
    if (sel.options[i].value === ref.category) { sel.selectedIndex = i; break; }
  }
  new bootstrap.Modal(document.getElementById('editModal')).show();
}
