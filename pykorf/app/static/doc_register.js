// Document Register search modal logic for References page
(function() {
  'use strict';

  var searchTimeout = null;
  var selectedDocNo = null;
  var selectedTitle = null;

  // Debounced search helper
  function debounceSearch(fn, delay) {
    var t = null;
    return function(term) {
      clearTimeout(t);
      t = setTimeout(function() { fn(term); }, delay);
    };
  }

  // Fetch wrapper with optional AbortSignal
  function apiFetch(url, options) {
    return fetch(url, options).then(function(resp) {
      if (!resp.ok) throw new Error('API error: ' + resp.status);
      return resp.json();
    });
  }

  // Cancellable fetch — aborts the previous controller before starting a new one
  function apiFetchCancellable(url, abortRef) {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();
    return fetch(url, { signal: abortRef.current.signal }).then(function(resp) {
      if (!resp.ok) throw new Error('API error: ' + resp.status);
      return resp.json();
    });
  }

  // Build a full SharePoint URL from path + name
  function buildSpUrl(path, name) {
    var base = window.DOC_REGISTER_SP_SITE_URL || '';
    return base + '/' + path.replace(/^\/+/, '') + '/' + name.replace(/^\/+/, '');
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

  var _eddrAbortRef = { current: null };
  var searchEDDR = debounceSearch(function(term) {
    if (!term || term.length < 2) {
      showEmpty('eddr-results', 'Type at least 2 characters to search');
      return;
    }
    showLoading('eddr-results');
    apiFetchCancellable('/api/doc-register/search-eddr?q=' + encodeURIComponent(term), _eddrAbortRef)
      .then(function(results) { renderEDDRResults(results); })
      .catch(function(err) { if (err.name !== 'AbortError') showEmpty('eddr-results', 'Search failed: ' + err.message); });
  }, 200);

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
    isDirectSearch = false;
    showLoading('query-results');
    apiFetch('/api/doc-register/search-query?doc_no=' + encodeURIComponent(docNo))
      .then(function(results) {
        currentQueryResults = results;
        currentDocNo = docNo;
        // Clear filter when new results load
        var filterInput = document.getElementById('query-search');
        if (filterInput) filterInput.value = '';
        renderQueryResults(results, docNo, false);
      })
      .catch(function(err) { showEmpty('query-results', 'Search failed: ' + err.message); });
  }

  // Store current query results for filtering
  var currentQueryResults = null;
  var currentDocNo = null;
  var isDirectSearch = false;

  // Debounced direct file search (Step 2 independent search)
  var _filesAbortRef = { current: null };
  var searchFiles = debounceSearch(function(term) {
    if (!term || term.length < 2) {
      showEmpty('query-results', 'Type at least 2 characters to search files/folders');
      currentQueryResults = null;
      currentDocNo = null;
      isDirectSearch = false;
      return;
    }
    isDirectSearch = true;
    showLoading('query-results');
    apiFetchCancellable('/api/doc-register/search-files?q=' + encodeURIComponent(term), _filesAbortRef)
      .then(function(results) {
        currentQueryResults = results;
        currentDocNo = null;
        renderQueryResults(results, null, false);
      })
      .catch(function(err) { if (err.name !== 'AbortError') showEmpty('query-results', 'Search failed: ' + err.message); });
  }, 200);

  // Filter query results based on search term (show/hide existing rows — no DOM rebuild)
  var filterTimeout = null;
  function filterQueryResults(term) {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(function() {
      var container = document.getElementById('query-results');
      if (!container) return;
      var rows = container.querySelectorAll('tr.query-row');
      if (!rows.length) return;
      var lowerTerm = term ? term.trim().toLowerCase() : '';
      var visibleCount = 0;
      rows.forEach(function(row) {
        var haystack = row.getAttribute('data-search') || '';
        var show = !lowerTerm || haystack.includes(lowerTerm);
        row.style.display = show ? '' : 'none';
        if (show) visibleCount++;
      });
      // Update or remove the no-match message
      var noMatch = container.querySelector('.query-no-match');
      if (visibleCount === 0) {
        if (!noMatch) {
          noMatch = document.createElement('tr');
          noMatch.className = 'query-no-match';
          noMatch.innerHTML = '<td colspan="6" class="text-center text-secondary py-3">' +
            '<i class="bi bi-search d-block fs-5 mb-1"></i>No files match your search. Try a different term.</td>';
          var tbody = container.querySelector('tbody');
          if (tbody) tbody.appendChild(noMatch);
        }
      } else if (noMatch) {
        noMatch.remove();
      }
    }, 80);
  }

  function renderQueryResults(results, docNo, isFiltered) {
    var container = document.getElementById('query-results');
    if (!container) return;

    if (!results || results.length === 0) {
      if (isFiltered) {
        container.innerHTML = '<div class="text-center text-secondary py-3">' +
          '<i class="bi bi-search d-block fs-5 mb-1"></i>' +
          'No files match your search. Try a different term.</div>';
      } else if (isDirectSearch) {
        container.innerHTML = '<div class="text-center text-secondary py-3">' +
          '<i class="bi bi-file-earmark-x d-block fs-5 mb-1"></i>' +
          'No files found matching your search.</div>';
      } else if (docNo) {
        container.innerHTML = '<div class="text-center text-secondary py-3">' +
          '<i class="bi bi-file-earmark-x d-block fs-5 mb-1"></i>' +
          'No files found for document <strong>' + escapeHtml(docNo) + '</strong>. ' +
          'The file may not be synced or available in the register.</div>';
      } else {
        showEmpty('query-results', 'Select a document above to see available files');
      }
      return;
    }

    var html = '<table class="table table-sm table-hover mb-0"><thead class="table-light">' +
      '<tr><th style="width:50%">Name</th><th style="width:8%">Type</th>' +
      '<th style="width:10%">Modified</th><th style="width:11%">Modified By</th>' +
      '<th>Path</th><th style="width:3rem"></th></tr></thead><tbody>';

    results.forEach(function(r) {
      var typeBadge = r.item_type === 'Folder'
        ? '<span class="badge bg-info text-dark"><i class="bi bi-folder2 me-1"></i>Folder</span>'
        : '<span class="badge bg-success"><i class="bi bi-file-earmark me-1"></i>File</span>';

      var modDisplay = r.modified && r.modified !== '' ? escapeHtml(r.modified.substring(0, 10)) : '—';
      var fullUrl = buildSpUrl(r.path, r.name);

      var searchKey = (r.name + ' ' + (r.path || '') + ' ' + (r.item_type || '')).toLowerCase();
      html += '<tr class="query-row" style="cursor:pointer;font-size:.75rem" ' +
        'data-name="' + escapeHtml(r.name) + '" ' +
        'data-path="' + escapeHtml(r.path) + '" ' +
        'data-type="' + escapeHtml(r.item_type) + '" ' +
        'data-search="' + escapeHtml(searchKey) + '">' +
        '<td class="fw-semibold text-truncate" style="max-width:280px" title="' + escapeHtml(r.name) + '">' + escapeHtml(r.name) + '</td>' +
        '<td>' + typeBadge + '</td>' +
        '<td class="text-secondary">' + modDisplay + '</td>' +
        '<td class="text-secondary text-truncate" style="max-width:90px" title="' + escapeHtml(r.modified_by || '') + '">' + escapeHtml(r.modified_by || '—') + '</td>' +
        '<td class="text-secondary text-truncate" style="max-width:120px" title="' + escapeHtml(r.path) + '">' + escapeHtml(r.path) + '</td>' +
        '<td class="text-center">' +
          '<a href="' + escapeHtml(fullUrl) + '" target="_blank" rel="noopener" ' +
          'class="btn btn-xs btn-outline-primary py-0 px-1" ' +
          'title="Open in new tab" ' +
          'onclick="event.stopPropagation()">' +
          '<i class="bi bi-box-arrow-up-right"></i></a></td></tr>';
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
    var fullPath = buildSpUrl(path, name);

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

  function showRebuildError(msg) {
    var errEl = document.getElementById('doc-register-rebuild-error');
    if (!errEl) {
      errEl = document.createElement('div');
      errEl.id = 'doc-register-rebuild-error';
      errEl.className = 'text-danger small mt-1';
      var btn = document.getElementById('doc-register-rebuild-btn');
      if (btn && btn.parentNode) btn.parentNode.insertBefore(errEl, btn.nextSibling);
    }
    errEl.textContent = msg;
    setTimeout(function() { if (errEl) errEl.textContent = ''; }, 5000);
  }

  function rebuildDB() {
    var btn = document.getElementById('doc-register-rebuild-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Rebuilding...';
    }

    apiFetch('/api/doc-register/rebuild-db', { method: 'POST' })
      .then(function(data) {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh DB';
        }
        if (data.success) {
          checkDBStatus();
        } else {
          showRebuildError('Rebuild failed: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(function(err) {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh DB';
        }
        showRebuildError('Rebuild failed: ' + err.message);
      });
  }

  // ── Modal open handler ───────────────────────────────────────────────────

  function onModalOpen() {
    // Reset state
    selectedDocNo = null;
    selectedTitle = null;
    currentQueryResults = null;
    currentDocNo = null;
    isDirectSearch = false;

    // Pre-fill search from the Name field (works for both Add and Edit flows)
    var nameInput = document.getElementById('add-name');
    var prefill = nameInput ? nameInput.value.trim() : '';

    var searchInput = document.getElementById('eddr-search');
    if (searchInput) searchInput.value = prefill;

    // Clear Step 2 filter
    var querySearchInput = document.getElementById('query-search');
    if (querySearchInput) querySearchInput.value = '';

    if (prefill.length >= 2) {
      showLoading('eddr-results');
      searchEDDR(prefill);
    } else {
      showEmpty('eddr-results', 'Type to search documents by title...');
    }
    showEmpty('query-results', 'Type to search files directly, or select a document above');
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

    // Step 2: filter already-loaded results instantly; fall back to API search
    var querySearchInput = document.getElementById('query-search');
    if (querySearchInput) {
      querySearchInput.addEventListener('input', function() {
        var val = this.value;
        if (!val.trim()) {
          if (isDirectSearch) {
            // Cleared a direct API search — reset to empty state
            currentQueryResults = null;
            currentDocNo = null;
            isDirectSearch = false;
            showEmpty('query-results', 'Type to search files directly, or select a document above');
          } else if (currentQueryResults) {
            // Cleared a Step-1 filter — restore all rows for the loaded doc
            filterQueryResults('');
          }
          return;
        }
        if (currentQueryResults) {
          // Results already in DOM — just show/hide rows, no rebuild
          filterQueryResults(val);
        } else {
          // Nothing loaded yet — do a direct API search
          searchFiles(val);
        }
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
