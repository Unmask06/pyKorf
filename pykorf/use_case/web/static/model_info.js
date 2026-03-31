// Live filter for pipe table
document.getElementById('pipe-search').addEventListener('input', function() {
  var q = this.value.toLowerCase();
  document.querySelectorAll('#pipe-table tbody tr').forEach(function(row) {
    var name = row.cells[1].textContent.toLowerCase();
    row.style.display = name.includes(q) ? '' : 'none';
  });
});
