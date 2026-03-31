/**
 * pyKorf Web UI — Path Browser widget.
 * Supports SharePoint URL detection for synced folders.
 */

// ═══════════════════════════════════════════════════════════════════════════
// Path Browser
// ═══════════════════════════════════════════════════════════════════════════

var PathBrowser = (function () {
  'use strict';

  var _targetInputId  = null;   // id of the <input> to fill on confirm
  var _filterMode     = 'any';  // kdf | excel | json | any
  var _preferSp       = false;  // true → auto-use SharePoint URL when available
  var _selectedPath   = null;   // local path of highlighted file
  var _selectedSpUrl  = null;   // SP URL of highlighted file (may be null)
  var _modal          = null;   // Bootstrap Modal instance
  var _currentPath    = '';     // directory being displayed

  // Icon map by filter mode
  var _fileIcon = {
    kdf:   'bi-file-earmark-binary text-info',
    excel: 'bi-file-earmark-spreadsheet text-success',
    json:  'bi-file-earmark-code text-warning',
    any:   'bi-file-earmark text-info',
  };

  function _el(id) { return document.getElementById(id); }

  // ── Public: open the browser ──────────────────────────────────────────────
  function open(targetInputId, filterMode, startPath, preferSharePoint) {
    _targetInputId = targetInputId;
    _filterMode    = filterMode || 'any';
    _preferSp      = !!preferSharePoint;
    _selectedPath  = null;
    _selectedSpUrl = null;

    if (!_modal) {
      _modal = new bootstrap.Modal(_el('pathBrowser'));
    }

    _el('pb-up').onclick        = goUp;
    _el('pb-filter').oninput    = applyFilter;
    _el('pb-select-btn').onclick = confirmSelect;

    var inputVal = (_el(targetInputId) || {}).value || '';
    var start    = startPath || inputVal || _currentPath || '';

    _modal.show();
    _el('pb-filter').value = '';
    _el('pb-select-btn').disabled = true;
    _updateSelectionLabel(null, null);

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
        list.innerHTML = '<div class="pb-item text-danger"><i class="bi bi-exclamation-triangle me-2"></i>' + esc(String(e)) + '</div>';
      });
  }

  // ── Render API response ────────────────────────────────────────────────────
  function render(data) {
    _currentPath = data.current;
    _el('pb-current-path').textContent = data.current;

    // SharePoint sync indicator for current directory
    var spBanner = _el('pb-sp-banner');
    if (data.current_sp_url) {
      spBanner.classList.remove('d-none');
      spBanner.title = data.current_sp_url;
    } else {
      spBanner.classList.add('d-none');
    }

    // Drive buttons (Windows)
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

    _el('pb-up').disabled = !data.parent;

    var list = _el('pb-list');
    list.innerHTML = '';
    var filter = (_el('pb-filter').value || '').toLowerCase();

    // ── Directories ────────────────────────────────────────────────────────
    data.dirs.forEach(function (d) {
      if (filter && d.name.toLowerCase().indexOf(filter) === -1) return;
      var item = document.createElement('div');
      item.className = 'pb-item pb-dir';
      item.dataset.path = d.path;

      var syncBadge = d.synced
        ? '<span class="badge bg-primary ms-auto pb-sp-badge" title="SharePoint synced folder">☁ SP</span>'
        : '';

      item.innerHTML =
        '<i class="bi bi-folder-fill text-warning"></i>' +
        '<span class="flex-grow-1">' + esc(d.name) + '</span>' +
        syncBadge;

      item.onclick = function () { browse(d.path); };
      list.appendChild(item);
    });

    // ── Files ──────────────────────────────────────────────────────────────
    var icon = _fileIcon[_filterMode] || _fileIcon.any;
    data.files.forEach(function (f) {
      if (filter && f.name.toLowerCase().indexOf(filter) === -1) return;

      var item = document.createElement('div');
      item.className = 'pb-item pb-file';
      item.dataset.path = f.path;
      item.dataset.spUrl = f.sharepoint_url || '';

      var spBadge = f.sharepoint_url
        ? '<span class="badge bg-primary ms-1 pb-sp-badge" title="' + esc(f.sharepoint_url) + '">☁ SP</span>'
        : '';

      item.innerHTML =
        '<i class="bi ' + icon + '"></i>' +
        '<span class="flex-grow-1">' + esc(f.name) + '</span>' +
        spBadge;

      item.onclick    = function () { selectItem(item, f.path, f.sharepoint_url || null); };
      item.ondblclick = function () { selectItem(item, f.path, f.sharepoint_url || null); confirmSelect(); };
      list.appendChild(item);
    });

    if (!list.children.length) {
      list.innerHTML = '<div class="pb-item text-secondary"><i class="bi bi-inbox me-2"></i>No matching files</div>';
    }
  }

  // ── Select a file item ─────────────────────────────────────────────────────
  function selectItem(el, localPath, spUrl) {
    _el('pb-list').querySelectorAll('.pb-selected').forEach(function (e) {
      e.classList.remove('pb-selected');
    });
    el.classList.add('pb-selected');
    _selectedPath  = localPath;
    _selectedSpUrl = spUrl || null;
    _updateSelectionLabel(localPath, spUrl);
    _el('pb-select-btn').disabled = false;
  }

  // ── Update the footer selection label + SP toggle ─────────────────────────
  function _updateSelectionLabel(localPath, spUrl) {
    var label  = _el('pb-selection-label');
    var toggle = _el('pb-sp-toggle');

    if (!localPath) {
      label.textContent = 'No file selected';
      if (toggle) toggle.classList.add('d-none');
      return;
    }

    if (spUrl) {
      // Show toggle between local path and SP URL
      var useSpNow = _preferSp;
      label.innerHTML =
        '<span id="pb-active-path" class="text-truncate small font-monospace" ' +
        'style="max-width:320px;display:inline-block">' +
        esc(useSpNow ? spUrl : localPath) + '</span>';

      toggle.classList.remove('d-none');
      var spBtn   = _el('pb-sp-use-btn');
      var localBtn = _el('pb-local-use-btn');

      if (useSpNow) {
        spBtn.classList.add('active');
        localBtn.classList.remove('active');
      } else {
        localBtn.classList.add('active');
        spBtn.classList.remove('active');
      }

      spBtn.onclick = function () {
        _preferSp = true;
        spBtn.classList.add('active');
        localBtn.classList.remove('active');
        _el('pb-active-path').textContent = spUrl;
      };
      localBtn.onclick = function () {
        _preferSp = false;
        localBtn.classList.add('active');
        spBtn.classList.remove('active');
        _el('pb-active-path').textContent = localPath;
      };
    } else {
      label.innerHTML =
        '<span class="text-truncate small font-monospace" style="max-width:420px;display:inline-block">' +
        esc(localPath) + '</span>';
      if (toggle) toggle.classList.add('d-none');
    }
  }

  // ── Confirm and fill target input ─────────────────────────────────────────
  function confirmSelect() {
    if (!_selectedPath) return;

    // Use SP URL when preferred AND available, otherwise local path
    var value = (_preferSp && _selectedSpUrl) ? _selectedSpUrl : _selectedPath;

    var input = _el(_targetInputId);
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('input',  { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (_modal) _modal.hide();
  }

  // ── Go up one level ────────────────────────────────────────────────────────
  function goUp() {
    var cur = _el('pb-current-path').textContent;
    if (!cur || cur === '—') return;
    fetch('/api/browse?filter=' + encodeURIComponent(_filterMode) + '&path=' + encodeURIComponent(cur))
      .then(function (r) { return r.json(); })
      .then(function (data) { if (data.parent) browse(data.parent); });
  }

  function applyFilter() { browse(_currentPath); }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  return { open: open };
})();


// ── data-attribute wiring ────────────────────────────────────────────────────
// <button data-browse-target="inputId"
//         data-browse-filter="kdf|excel|json|any"
//         data-browse-prefer-sp="true">Browse</button>
document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-browse-target]');
    if (!btn) return;
    var target   = btn.dataset.browseTarget;
    var filter   = btn.dataset.browseFilter  || 'any';
    var preferSp = btn.dataset.browsePrefSp === 'true';
    PathBrowser.open(target, filter, '', preferSp);
  });
});
