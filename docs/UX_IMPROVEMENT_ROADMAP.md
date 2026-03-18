# pyKorf UX Improvement Roadmap

**Created:** 2026-03-18  
**Status:** 📋 Planning  
**Source:** `plans/ux_improvement_plan.md`

---

## 🎯 Goals

1. Reduce friction in file selection and navigation
2. Improve feedback for operations and errors
3. Add discoverability through shortcuts and help
4. Enhance productivity with search, copy, and export

---

## 📊 Priority Legend

| Priority | Items | Timeline |
|----------|-------|----------|
| 🔴 HIGH | 1, 2, 3, 12 | Week 1-2 |
| 🟡 MEDIUM | 4, 5, 6, 7, 9, 10 | Week 3-6 |
| 🟢 LOW | 8, 11, 13, 14 | Week 7-8 |

---

## 🗺️ Implementation Phases

### Phase 1: Critical UX Improvements (Week 1-2)

#### 🔴 1. File Picker Enhancement
**Files:** `pykorf/use_case/tui/screens/file_picker.py`

- [ ] Add recent files list (expand `get_last_kdf_path()` to store 10 files)
- [ ] Add Browse button for native file dialog
- [ ] Add real-time path validation on `Input.Changed`
- [ ] Show file size and modified date

**Implementation Notes:**
```python
# In preferences.py
def get_recent_files(max_count: int = 10) -> list[str]:
    config = load_config()
    return config.get("recent_files", [])[:max_count]

def add_recent_file(path: str | Path) -> None:
    config = load_config()
    recent = config.get("recent_files", [])
    path_str = str(path)
    if path_str in recent:
        recent.remove(path_str)
    recent.insert(0, path_str)
    config["recent_files"] = recent[:10]
    save_config(config)
```

**Status:** ⏳ Pending

---

#### 🔴 2. Standardized Error Handling
**Files:** All screens with RichLog widgets

- [ ] Use Textual's `notify()` API for toast notifications
- [ ] Standardize icon prefixes: ✓ Success, ⚠ Warning, ✗ Error, ℹ Info
- [ ] Add loading indicators for operations > 1 second

**Status:** ⏳ Pending

---

#### 🔴 3. Keyboard Shortcuts
**Files:** All screen files

- [ ] Add to ALL screens:
  - `Escape` — Back/Close
  - `q` — Quit
  - `F1` — Help
  - `Ctrl+R` — Reload (when model loaded)
  - `Ctrl+S` — Save (when modified)

- [ ] Ensure all screens have Footer widget

**Status:** ⏳ Pending

---

#### 🔴 12. Recent Files History
**Files:** `pykorf/use_case/preferences.py`, `file_picker.py`

- [ ] Modify config to store list of recent files (max 10)
- [ ] Add quick-select buttons in FilePickerScreen
- [ ] Add `add_recent_file()` to config save points

**Status:** ⏳ Pending

---

**Phase 1 Complete:** ⬜ 0/4

---

### Phase 2: Visual Enhancements (Week 3-4)

#### 🟡 4. Loading States
**Files:** `generate_report.py`, `global_settings.py`, `apply_pms.py`, `apply_hmb.py`

- [ ] Add LoadingIndicator for async operations
- [ ] Add ProgressBar for batch operations
- [ ] Add "working" indicator for PMS/HMB apply

**Status:** ⏳ Pending

---

#### 🟡 5. Main Menu Redesign
**File:** `pykorf/use_case/tui/screens/main_menu.py`

- [ ] Group operations by category:
  1. Model Operations (Bulk Copy, Apply PMS, Apply HMB)
  2. Analysis & Reports (Model Info, Generate Report)
  3. Configuration (Config Menu, Global Settings)
  4. File Operations (Load File, Import/Export)

- [ ] Add icons to button labels
- [ ] Improve visual hierarchy with sections

**Status:** ⏳ Pending

---

#### 🟡 6. Real-time Validation
**Files:** `file_picker.py`, `bulk_copy.py`, `config_menu.py`

- [ ] Add `@on(Input.Changed)` handlers for live validation
- [ ] Show visual indicators (icons) next to input fields
- [ ] Display format hints as placeholders

**Implementation Notes:**
```python
@on(Input.Changed, "#file-path-input")
def validate_path_realtime(self, event: Input.Changed) -> None:
    path = Path(event.value.strip())
    if not path.exists():
        error_label.update("⚠ File not found")
    elif path.suffix.lower() != ".kdf":
        error_label.update("⚠ Not a .kdf file")
    else:
        error_label.update("✓ Valid file")
```

**Status:** ⏳ Pending

---

**Phase 2 Complete:** ⬜ 0/3

---

### Phase 3: Productivity Features (Week 5-6)

#### 🟡 7. Search/Filter
**Files:** `bulk_copy.py`, `model_info.py`, `global_settings.py`

- [ ] Replace Static/RichLog with DataTable for lists
- [ ] Add search input above lists
- [ ] Implement type-to-select functionality

**DataTable Benefits:**
- Built-in sorting
- Keyboard navigation
- Type-to-select
- Better scrolling

**Status:** ⏳ Pending

---

#### 🟢 8. Copy/Export Logs
**Files:** All screens with RichLog

- [ ] Add buttons: 📋 Copy, 💾 Export, 🗑 Clear
- [ ] Add keyboard shortcut: `Ctrl+C` copy selected, `Ctrl+Shift+C` copy all
- [ ] Use `notify()` for export confirmation

**Status:** ⏳ Pending

---

#### 🟡 9. Tooltips & Help
**Files:** All screens

- [ ] Add F1 key binding to all screens
- [ ] Create context-sensitive help screens
- [ ] Include examples and field descriptions
- [ ] Link to external documentation

**Status:** ⏳ Pending

---

**Phase 3 Complete:** ⬜ 0/3

---

### Phase 4: Advanced Features (Week 7-8)

#### 🟢 10. Auto-save & Recovery
**Files:** `pykorf/model/core.py`, `app.py`

- [ ] Add auto-save backup to temp location
- [ ] Implement periodic backup (every 5 minutes)
- [ ] Check for backup on startup and offer recovery

**Status:** ⏳ Pending

---

#### 🟢 11. Accessibility
**Files:** `pykorf/use_case/tui/app.py`

- [ ] Add high-contrast theme option
- [ ] Add icons to all status indicators (not just color)
- [ ] Create custom CSS theme classes (`.success`, `.warning`, `.error`)

**Status:** ⏳ Pending

---

#### 🟢 13. Undo/Redo (Future)
**Files:** `pykorf/model/core.py`

- [ ] Implement Command pattern for model operations
- [ ] Maintain command history stack
- [ ] Add `undo()`/`redo()` methods to Model class

**Status:** ⏳ Blocked (Complex, future enhancement)

---

#### 🟢 14. Log Export Enhancement
**Files:** All screens with RichLog

- [ ] Export log to timestamped text file
- [ ] Add export path selector
- [ ] Include model metadata in export

**Status:** ⏳ Pending

---

**Phase 4 Complete:** ⬜ 0/4

---

## 📈 Progress Dashboard

```
Overall: [░░░░░░░░░░] 0/14 (0%)

Phase 1: [░░░░] 0/4 (0%)
Phase 2: [░░░] 0/3 (0%)
Phase 3: [░░░] 0/3 (0%)
Phase 4: [░░░░] 0/4 (0%)
```

| Phase | Items | Status |
|-------|-------|--------|
| 1. Critical | 4 | ⏳ Not Started |
| 2. Visual | 3 | ⏳ Not Started |
| 3. Productivity | 3 | ⏳ Not Started |
| 4. Advanced | 4 | ⏳ Not Started |

---

## 🧪 Testing Checklist

For each completed item:

- [ ] Works with small models (<10 elements)
- [ ] Works with large models (>100 elements)
- [ ] Keyboard navigation works
- [ ] Mouse navigation works
- [ ] Error states handled gracefully
- [ ] No console errors
- [ ] Backward compatible
- [ ] Tested on Windows

---

## 📝 Quick Reference

### Screen Inventory

| Screen | Issues | Priority Items |
|--------|--------|----------------|
| FilePickerScreen | Manual path entry | 1, 6, 12 |
| MainMenuScreen | Dense layout | 5, 9 |
| BulkCopyFluidsScreen | No search | 6, 7, 8 |
| ApplyPmsScreen | Minimal feedback | 4, 6 |
| ModelInfoScreen | Static lists | 7, 9 |
| GenerateReportScreen | No progress | 4, 8 |
| GlobalSettingsScreen | No filter | 4, 7 |
| ConfigMenuScreen | No validation | 6, 8 |

---

## 🔗 Related Docs

- [UX Improvement Plan](../plans/ux_improvement_plan.md)
- [Textual Docs](https://textual.textualize.io/)
- [README](../README.md)

---

**Last Updated:** 2026-03-18  
**Next Review:** After Phase 1 completion
