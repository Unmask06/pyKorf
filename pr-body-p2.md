## P2 Priority Refactors

### Changes

1. **Remove redundant `len() > 0` guards** (`global_parameters.py`)
   - Deleted 5 instances of `if len(model.pipes) > 0:` and `if len(model.pipes) <= 0:`
   - Loops over empty ranges are no-ops; guards add noise

2. **Fix undefined variable** (`global_parameters.py`)
   - Changed `all_errors.append()` to `errors.append()` (was referencing wrong variable name)

3. **Collapse identical error handlers** (`errors.py`)
   - `use_case_error_handler` and `korf_error_handler` were identical
   - Replaced with `_json_error_handler(400)` factory
   - Removed unused imports

### Dependencies
- Requires P0 (#57) and P1 (#59) merged

### Testing
- [x] Ruff check passes
- [x] MyPy check passes
