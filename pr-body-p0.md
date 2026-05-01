## P0 Priority Refactors

### Changes

1. **Cache config in memory** (`preferences.py`)
   - Added `_config_cache` module-level variable to avoid reading `config.json` from disk on every getter call
   - Cache is invalidated on `save_config()` and populated on first `load_config()` call
   
2. **Atomic config writes** (`preferences.py`)
   - Changed `save_config()` to write to a temp file first, then `replace()` to prevent corruption if process crashes mid-write
   
3. **Centralized persist helper** (`deps.py`)
   - Added `persist(model)` async helper that combines `model.save()` + `await _sess.reload()`
   - This pattern was repeated in 22+ places across all mutating routers
   
4. **Centralized pipe predicate** (`deps.py`)
   - Added `is_real_pipe(pipe)` to replace the copy-pasted `name and not name.startswith("d")` pattern

### Testing
- [x] Ruff check passes
- [x] MyPy check passes

### Next Steps
This PR prepares the ground for P1 (removing the 22+ save+reload duplications by migrating routers to use `persist()`).
