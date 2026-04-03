// Document Register search modal logic for References page
(function() {
  'use strict';

  var searchTimeout = null;
  var selectedDocNo = null;
  var selectedTitle = null;

  // Debounced search helper
  function debounceSearch(fn, delay) {
    return function(term) {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(function() { fn(term); }, delay);
    };
  }

  // Fetch wrapper with error handling
  function apiFetch(url) {
    return fetch(url).then(function(resp) {
      if (!resp.ok) throw new Error('API error: ' + resp.status);
      return resp.json();
    });
  }

  // Escape HTML to prevent XSS
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // Show/hide loading spinner
  function showLoading(containerId) {
    var c = document.getElementById(containerId);
    if (c) c.innerHTML = '<div class="text-center text-secondary py-3"><div class="spinner-border spinner-border-sm me-2" role="status"></div>Searching...</div>';
  }

  // Show empty state
  function showEmpty(containerId, message) {
    var c = document.getElementById(containerId);
    if (c) c.innerHTML = '<div class="text-center text-secondary py-3"><i class="bi bi-search d-block fs-5 mb-1"></i>' + escapeHtml(message) + '</div>';
  }

  // ── Step 1: EDDR Search ──────────────────────────────────────────────────

  var searchEDDR = debounceSearch(function(term) {
    if (!term || term.length < 2) {
      showEmpty('eddr-results', 'Type at least 2 characters to search');
      return;
    }
    showLoading('eddr-results');
    apiFetch('/api/doc-register/search-eddr?q=' + encodeURIComponent(term))
      .then(function(results) { renderEDDRResults(results); })
      .catch(function(err) { showEmpty('eddr-results', 'Search failed: ' + err.message); });
  }, 300);

  function renderEDDRResults(results) {
    var container = document.getElementById('eddr-results');
    if (!container) return;

    if (!results || results.length === 0) {
      showEmpty('eddr-results', 'No documents found');
      return;
    }

    var html = '<table class="table table-sm table-hover mb-0"><thead class="table-light">' +
      '<tr><th style="width:30%">Document No</th><th>Title</th></tr></thead><tbody>';

    results.forEach(function(r) {
      html += '<tr class="eddr-row" data-doc-no="' + escapeHtml(r.document_no) + '" data-title="' + escapeHtml(r.title) + '" style="cursor:pointer">' +
        '<td class="font-monospace small fw-semibold">' + escapeHtml(r.document_no) + '</td>' +
        '<td class="small">' + escapeHtml(r.title) + '</td></tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    // Attach click handlers
    container.querySelectorAll('.eddr-row').forEach(function(row) {
      row.addEventListener('click', function() {
        selectedDocNo = this.getAttribute('data-doc-no');
        selectedTitle = this.getAttribute('data-title');

        // Highlight selected row
        container.querySelectorAll('.eddr-row').forEach(function(r) { r.classList.remove('table-active'); });
        this.classList.add('table-active');

        // Auto-trigger Step 2
        searchQuery(selectedDocNo);
      });
    });
  }

  // ── Step 2: Query Search ─────────────────────────────────────────────────

  function searchQuery(docNo) {
    if (!docNo) return;
    showLoading('query-results');
    apiFetch('/api/doc-register/search-query?doc_no=' + encodeURIComponent(docNo))
      .then(function(results) { renderQueryResults(results, docNo); })
      .catch(function(err) { showEmpty('query-results', 'Search failed: ' + err.message); });
  }

  function renderQueryResults(results, docNo) {
    var container = document.getElementById('query-results');
    if (!container) return;

    if (!results || results.length === 0) {
      container.innerHTML = '<div class="text-center text-secondary py-3">' +
        '<i class="bi bi-file-earmark-x d-block fs-5 mb-1"></i>' +
        'No files found for document <strong>' + escapeHtml(docNo) + '</strong>. ' +
        'The file may not be synced or available in the register.</div>';
      return;
    }

    var html = '<table class="table table-sm table-hover mb-0"><thead class="table-light">' +
      '<tr><th style="width:28%">Name</th><th style="width:14%">Type</th>' +
      '<th style="width:18%">Modified</th><th style="width:20%">Modified By</th>' +
      '<th>Path</th></tr></thead><tbody>';

    results.forEach(function(r) {
      var typeBadge = r.item_type === 'Folder'
        ? '<span class="badge bg-info text-dark"><i class="bi bi-folder2 me-1"></i>Folder</span>'
        : '<span class="badge bg-success"><i class="bi bi-file-earmark me-1"></i>File</span>';

      var modDisplay = r.modified && r.modified !== '' ? escapeHtml(r.modified.substring(0, 10)) : '—';

      html += '<tr class="query-row" style="cursor:pointer" ' +
        'data-name="' + escapeHtml(r.name) + '" ' +
        'data-path="' + escapeHtml(r.path) + '" ' +
        'data-type="' + escapeHtml(r.item_type) + '">' +
        '<td class="small fw-semibold text-truncate" style="max-width:200px" title="' + escapeHtml(r.name) + '">' + escapeHtml(r.name) + '</td>' +
        '<td>' + typeBadge + '</td>' +
        '<td class="small text-secondary">' + modDisplay + '</td>' +
        '<td class="small text-secondary">' + escapeHtml(r.modified_by || '—') + '</td>' +
        '<td class="small text-secondary text-truncate" style="max-width:180px" title="' + escapeHtml(r.path) + '">' + escapeHtml(r.path) + '</td></tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    // Attach click handlers
    container.querySelectorAll('.query-row').forEach(function(row) {
      row.addEventListener('click', function() {
        selectQueryEntry(this);
      });
    });
  }

  // ── Selection: populate parent form ───────────────────────────────────────

  function selectQueryEntry(row) {
    var name = row.getAttribute('data-name');
    var path = row.getAttribute('data-path');
    var spSite = window.DOC_REGISTER_SP_SITE_URL || '';

    // Construct full SharePoint URL
    var fullPath = spSite + '/' + path.replace(/^\/+/, '') + '/' + name.replace(/^\/+/, '');

    // Populate the parent form
    var nameInput = document.getElementById('add-name');
    var linkInput = document.getElementById('add-link');
    var descInput = document.getElementById('add-description');

    if (nameInput) nameInput.value = selectedDocNo || name;
    if (linkInput) linkInput.value = fullPath;
    if (descInput) descInput.value = selectedTitle || '';

    // Close modal
    var modalEl = document.getElementById('docRegisterModal');
    if (modalEl) {
      var modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }

    // Focus name field for quick edit
    if (nameInput) nameInput.focus();
  }

  // ── DB Status & Rebuild ──────────────────────────────────────────────────

  function checkDBStatus() {
    apiFetch('/api/doc-register/status')
      .then(function(data) {
        var badge = document.getElementById('doc-register-modal-status');
        if (!badge) return;

        if (!data.excel_path) {
          badge.className = 'badge bg-secondary';
          badge.textContent = 'Not configured';
        } else if (!data.db_exists || data.is_stale) {
          badge.className = 'badge bg-warning text-dark';
          badge.textContent = data.is_stale ? 'Stale — click Refresh' : 'Not built';
        } else {
          badge.className = 'badge bg-success';
          badge.textContent = 'Up to date';
        }
      })
      .catch(function() {
        var badge = document.getElementById('doc-register-modal-status');
        if (badge) { badge.className = 'badge bg-danger'; badge.textContent = 'Error'; }
      });
  }

  function rebuildDB() {
    var btn = document.getElementById('doc-register-rebuild-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Rebuilding...';
    }

    fetch('/api/doc-register/rebuild-db', { method: 'POST' })
      .then(function(resp) { return resp.json(); })
      .then(function(data) {
        if (data.success) {
          checkDBStatus();
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh DB';
          }
        } else {
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh DB';
          }
          alert('Rebuild failed: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(function(err) {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh DB';
        }
        alert('Rebuild failed: ' + err.message);
      });
  }

  // ── Modal open handler ───────────────────────────────────────────────────

  function onModalOpen() {
    // Reset state
    selectedDocNo = null;
    selectedTitle = null;
    document.getElementById('eddr-search').value = '';
    showEmpty('eddr-results', 'Type to search documents by title...');
    showEmpty('query-results', 'Select a document above to see available files');
    checkDBStatus();
  }

  // ── Initialize on DOM ready ──────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('eddr-search');
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        searchEDDR(this.value);
      });
    }

    var rebuildBtn = document.getElementById('doc-register-rebuild-btn');
    if (rebuildBtn) {
      rebuildBtn.addEventListener('click', rebuildDB);
    }

    var modalEl = document.getElementById('docRegisterModal');
    if (modalEl) {
      modalEl.addEventListener('shown.bs.modal', onModalOpen);
    }
  });

  // Expose rebuild function globally for inline onclick fallback
  window.docRegisterRebuildDB = rebuildDB;
})();
