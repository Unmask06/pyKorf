/**
 * pyKorf Web UI — shared helpers.
 * No framework, no build step.
 */

// ─── Generic loading-spinner on any data-loading form ─────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('form[data-loading]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn    = form.querySelector('button[type="submit"]');
      var spinner = form.querySelector('.spinner-border');
      if (btn)     btn.disabled = true;
      if (spinner) spinner.classList.remove('d-none');
    });
  });
});


// ═══════════════════════════════════════════════════════════════════════════
// Path Browser
// ═══════════════════════════════════════════════════════════════════════════

var PathBrowser = (function () {
  'use strict';

  var _targetInputId = null;   // id of the <input> to fill on select
  var _filterMode    = 'any';  // kdf | excel | json | any
  var _selectedPath  = null;   // currently highlighted file path
  var _modal         = null;   // Bootstrap Modal instance
  var _currentPath   = '';     // directory being displayed

  // Icon map for filter modes
  var _fileIcon = {
    kdf:   'bi-file-earmark-binary text-info',
    excel: 'bi-file-earmark-spreadsheet text-success',
    json:  'bi-file-earmark-code text-warning',
    any:   'bi-file-earmark text-info',
  };

  // ── DOM refs (resolved on first use) ─────────────────────────────────────
  function _el(id) { return document.getElementById(id); }

  // ── Public: open the browser ──────────────────────────────────────────────
  function open(targetInputId, filterMode, startPath) {
    _targetInputId = targetInputId;
    _filterMode    = filterMode || 'any';
    _selectedPath  = null;

    if (!_modal) {
      _modal = new bootstrap.Modal(_el('pathBrowser'));
    }

    // Wire up buttons once
    _el('pb-up').onclick        = goUp;
    _el('pb-filter').oninput    = applyFilter;
    _el('pb-select-btn').onclick = confirmSelect;

    // Derive start path from current input value or last path
    var inputVal = (_el(targetInputId) || {}).value || '';
    var start    = startPath || inputVal || _currentPath || '';

    _modal.show();
    _el('pb-filter').value = '';
    _el('pb-selection-label').textContent = 'No file selected';
    _el('pb-select-btn').disabled = true;

    browse(start);
  }

  // ── Browse to a path ──────────────────────────────────────────────────────
  function browse(path) {
    var list = _el('pb-list');
    list.innerHTML = '<div class="pb-item text-secondary"><i class="bi bi-hourglass-split me-2"></i>Loading…</div>';

    var url = '/api/browse?filter=' + encodeURIComponent(_filterMode);
    if (path) url += '&path=' + encodeURIComponent(path);

    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) { render(data); })
      .catch(function (e) {
        list.innerHTML = '<div class="pb-item text-danger"><i class="bi bi-exclamation-triangle me-2"></i>' + e + '</div>';
      });
  }

  // ── Render API response ────────────────────────────────────────────────────
  function render(data) {
    _currentPath = data.current;
    _el('pb-current-path').textContent = data.current;

    // Drives (Windows)
    var drivesRow = _el('pb-drives-row');
    var drivesEl  = _el('pb-drives');
    if (data.drives && data.drives.length) {
      drivesRow.classList.remove('d-none');
      drivesEl.innerHTML = '';
      data.drives.forEach(function (d) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-outline-secondary pb-drive-btn';
        btn.textContent = d;
        btn.onclick = function () { browse(d); };
        drivesEl.appendChild(btn);
      });
    } else {
      drivesRow.classList.add('d-none');
    }

    // Up button
    _el('pb-up').disabled = !data.parent;

    // Build list
    var list = _el('pb-list');
    list.innerHTML = '';
    var filter = _el('pb-filter').value.toLowerCase();

    // Dirs
    data.dirs.forEach(function (d) {
      if (filter && d.name.toLowerCase().indexOf(filter) === -1) return;
      var item = document.createElement('div');
      item.className = 'pb-item pb-dir';
      item.dataset.path = d.path;
      item.dataset.isDir = '1';
      item.innerHTML = '<i class="bi bi-folder-fill text-warning"></i><span>' + esc(d.name) + '</span>';
      item.onclick = function () { browse(d.path); };
      list.appendChild(item);
    });

    // Files
    var icon = _fileIcon[_filterMode] || _fileIcon.any;
    data.files.forEach(function (f) {
      if (filter && f.name.toLowerCase().indexOf(filter) === -1) return;
      var item = document.createElement('div');
      item.className = 'pb-item pb-file';
      item.dataset.path = f.path;
      item.innerHTML = '<i class="bi ' + icon + '"></i><span>' + esc(f.name) + '</span>';
      item.onclick = function () { selectItem(item, f.path); };
      item.ondblclick = function () { selectItem(item, f.path); confirmSelect(); };
      list.appendChild(item);
    });

    if (!list.children.length) {
      list.innerHTML = '<div class="pb-item text-secondary"><i class="bi bi-inbox me-2"></i>No matching files</div>';
    }
  }

  // ── Select a file item ─────────────────────────────────────────────────────
  function selectItem(el, path) {
    // Clear previous selection
    _el('pb-list').querySelectorAll('.pb-selected').forEach(function (e) {
      e.classList.remove('pb-selected');
    });
    el.classList.add('pb-selected');
    _selectedPath = path;
    _el('pb-selection-label').textContent = path;
    _el('pb-select-btn').disabled = false;
  }

  // ── Confirm and fill target input ─────────────────────────────────────────
  function confirmSelect() {
    if (!_selectedPath) return;
    var input = _el(_targetInputId);
    if (input) {
      input.value = _selectedPath;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (_modal) _modal.hide();
  }

  // ── Go up one level ────────────────────────────────────────────────────────
  function goUp() {
    var cur = _el('pb-current-path').textContent;
    if (!cur || cur === '—') return;
    // Ask server to navigate up (parent is returned by server)
    fetch('/api/browse?filter=' + encodeURIComponent(_filterMode) + '&path=' + encodeURIComponent(cur))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.parent) browse(data.parent);
      });
  }

  // ── Re-filter on typing ────────────────────────────────────────────────────
  function applyFilter() {
    // Re-render with same data by browsing current path (cheap — local only)
    browse(_currentPath);
  }

  // ── HTML escape helper ─────────────────────────────────────────────────────
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return { open: open };
})();


// ── Convenience: attach Browse button to any input via data attributes ─────
// Usage: <button data-browse-target="inputId" data-browse-filter="kdf">Browse</button>
document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-browse-target]');
    if (!btn) return;
    var target = btn.dataset.browseTarget;
    var filter = btn.dataset.browseFilter || 'any';
    PathBrowser.open(target, filter);
  });
});
