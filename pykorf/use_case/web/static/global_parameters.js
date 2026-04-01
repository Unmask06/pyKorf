// Highlight card border when switch toggled
document.querySelectorAll('.setting-toggle').forEach(function(cb) {
  cb.addEventListener('change', function() {
    var card = document.getElementById(this.dataset.card);
    if (this.checked) {
      card.classList.replace('border-secondary', 'border-primary');
    } else {
      card.classList.replace('border-primary', 'border-secondary');
    }
  });
});

document.getElementById('btn-select-all').addEventListener('click', function() {
  document.querySelectorAll('.setting-toggle').forEach(function(cb) {
    if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
  });
});

document.getElementById('btn-clear-all').addEventListener('click', function() {
  document.querySelectorAll('.setting-toggle').forEach(function(cb) {
    if (cb.checked) { cb.checked = false; cb.dispatchEvent(new Event('change')); }
  });
});

// Live margin % display
function bindMarginPct(inputId, spanId) {
  var inp = document.getElementById(inputId);
  var span = document.getElementById(spanId);
  if (inp && span) {
    inp.addEventListener('input', function() {
      var v = parseFloat(this.value);
      if (!isNaN(v) && v >= 1) {
        span.textContent = ((v - 1) * 100).toFixed(0) + '% margin';
      }
    });
  }
}
bindMarginPct('dp_margin', 'dp-margin-pct');
bindMarginPct('shutoff_margin', 'shutoff-margin-pct');

// Loading spinner on submit
document.getElementById('settings-form').addEventListener('submit', function() {
  document.getElementById('btn-apply').disabled = true;
  document.getElementById('apply-spinner').classList.remove('d-none');
});
