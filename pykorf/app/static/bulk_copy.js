document.addEventListener('DOMContentLoaded', function () {
  const refInput = document.getElementById('ref_pipe');
  const targetInput = document.getElementById('target_pipes');
  const pipeFilter = document.getElementById('pipe-filter');
  const pipeList = document.getElementById('pipe-list');
  const form = document.getElementById('copy-form');
  const clearBtn = document.getElementById('clear-targets');

  // Filter pipe list
  pipeFilter.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    pipeList.querySelectorAll('.pipe-btn').forEach(function(btn) {
      const name = btn.dataset.pipe.toLowerCase();
      btn.style.display = name.includes(q) ? '' : 'none';
    });
  });

  // Click pipe to fill reference or add to targets
  pipeList.addEventListener('click', function(e) {
    const btn = e.target.closest('.pipe-btn');
    if (!btn) return;
    const pipeName = btn.dataset.pipe;

    // If reference is empty, fill it; otherwise add to targets
    if (!refInput.value.trim()) {
      refInput.value = pipeName;
    } else {
      const current = targetInput.value.trim();
      const targets = current ? current.split(',').map(s => s.trim()).filter(Boolean) : [];
      if (!targets.includes(pipeName)) {
        targets.push(pipeName);
        targetInput.value = targets.join(', ');
      }
    }
  });

  // Clear targets button
  clearBtn.addEventListener('click', function() {
    targetInput.value = '';
    targetInput.focus();
  });

  // Clipboard copy for results log
  const clipboardBtn = document.getElementById('btn-clipboard');
  if (clipboardBtn) {
    clipboardBtn.addEventListener('click', function() {
      const logEl = document.getElementById('copy-log-text');
      const text = logEl ? logEl.innerText.trim() : '';
      navigator.clipboard.writeText(text).then(function() {
        clipboardBtn.innerHTML = '<i class="bi bi-clipboard-check me-1"></i>Copied!';
        setTimeout(function() {
          clipboardBtn.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy Log';
        }, 2000);
      });
    });
  }

  // Spinner on submit
  form.addEventListener('submit', function() {
    const btn = document.getElementById('btn-execute');
    const spinner = document.getElementById('execute-spinner');
    btn.disabled = true;
    spinner.classList.remove('d-none');
  });
});
