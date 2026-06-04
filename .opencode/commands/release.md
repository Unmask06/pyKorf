---
description: Release a new version of pyKorf — bump version, update changelog, generate types, commit, and merge to main
agent: build
---

Release a new version of pyKorf. Follow these steps exactly.

## Step 0 — Prerequisites: clean working tree and kill stale processes

Kill any lingering pykorf processes (they block `uv run` later):

```
Get-Process -Name "pykorf" -ErrorAction SilentlyContinue | Stop-Process -Force
```

Check the working tree — verify only your intentional changes are present:

```
git diff --stat
```

If files like `openapi.json` or frontend generated types show as modified but you didn't change them, they are CRLF noise. Restore them:

```
git checkout -- pykorf/app/openapi.json pykorf/app/frontend/src/api/generated/
```

Final verification — should be clean aside from your intended changes:

```
git status --porcelain
```

## Step 1 — Generate OpenAPI schema and TypeScript types (only if needed)

Generate `openapi.json` programmatically — no running server required:

```
uv run python -c "from pykorf.app.api import create_app; import json; app = create_app(); openapi = app.openapi(); json.dump(openapi, open('pykorf/app/openapi.json', 'w'), indent=2)"
```

Check if it actually changed — if nothing prints, there is no diff and you can skip frontend type generation:

```
git diff --stat pykorf/app/openapi.json
```

If there IS a real diff, regenerate frontend types (use `cmd /c` since PowerShell blocks npm/npx):

```
cmd /c "cd C:\Users\PrasannaPalanivel\Documents\Code\pyKorf\pykorf\app\frontend && npm run generate-types"
```

If `openapi.json` has NO real diff, skip type generation — the types haven't changed either.

## Step 2 — Commit all working changes

Review what will be committed:

```
git status
git diff --stat
```

Stage only files with real changes. Do NOT `git add -A` blindly — CRLF noise files will creep in:

```
git add <intended files>
git commit -m "<type>: <description>"
```

If Step 1 produced real changes to `openapi.json` and generated types, include those. Since you didn't commit them initially, you can amend (if the commit was the last action) or commit separately.

## Step 3 — Pre-flight: ensure dev is in sync with main

```
git fetch origin
git log dev..origin/main --oneline
```

If this prints any commits, main is ahead of dev. Merge it first before proceeding:

```
git merge origin/main --no-ff -m "chore: sync dev with main"
```

## Step 4 — Determine version bump

Run `git log $(git describe --tags --abbrev=0)..HEAD --oneline` to see commits since the last tag.

- Any `feat:` commit → **minor** bump (0.X.0)
- Only `fix:` / `chore:` / `refactor:` commits → **patch** bump (0.0.X)
- Any breaking change noted → **major** bump (X.0.0)

## Step 5 — Update `pyproject.toml`

Set `version = "X.Y.Z"` in the `[project]` section.

## Step 6 — Update `CHANGELOG.md`

Add a new section at the top (below the header):

```
## [X.Y.Z] - YYYY-MM-DD
```

Write the changelog for **end users**, not developers:
- Group entries as: **What's New**, **Improved**, **Fixed**
- Use plain English sentences, not commit message style
- Omit: CI/CD changes, linting fixes, type annotations, internal refactors, test changes
- Each bullet = one sentence, no technical jargon
- Example good entry: "Reports now include the model title and source file at the top."
- Example bad entry: "feat(exporter): add model_title from SYMBOL FSIZ=2 to export_to_excel"

## Step 7 — Refresh lockfile

After updating the version in `pyproject.toml`, regenerate the lockfile so the release zip ships an up-to-date `uv.lock`:

```
uv lock
```

## Step 8 — Verify CI passes

Kill any stale processes first (prevents "file in use" errors):

```
Get-Process -Name "pykorf" -ErrorAction SilentlyContinue | Stop-Process -Force
```

Run lint, format, type-check, and tests:

```
uv run ruff check pykorf tests
uv run ruff format pykorf tests
uv run mypy pykorf
uv run pytest -q
```

If `uv run` fails with "file in use" or "cannot remove pykorf.exe", use direct venv calls as fallback:

```
.venv\Scripts\ruff.exe check pykorf tests
.venv\Scripts\ruff.exe format pykorf tests
.venv\Scripts\mypy.exe pykorf
.venv\Scripts\pytest.exe -q
```

Fix any failures before proceeding.

## Step 9 — Commit on dev

Stage only the release files:

```
git add pyproject.toml CHANGELOG.md uv.lock
```

If Step 1 produced real changes, also add:

```
git add pykorf/app/openapi.json pykorf/app/frontend/src/api/generated/
```

Commit:

```
git commit -m "release: vX.Y.Z"
```

## Step 10 — Merge to main, sync back, and push

**Before switching branches**, clean any CRLF noise from the working tree:

```
git status --porcelain
```

If files like `openapi.json` or generated types show as modified but weren't staged, restore them:

```
git checkout -- pykorf/app/openapi.json pykorf/app/frontend/src/api/generated/
```

Then proceed with the merge:

```
git checkout main
git merge dev --no-ff -m "release: vX.Y.Z"
git push origin main
git checkout dev
git merge main --ff-only
git push origin dev
```

The `--ff-only` merge after switching back to dev fast-forwards dev to include the release merge commit on main. This keeps both branches at the same tip and prevents main from drifting ahead of dev.

---

## ⚠️ Critical: Do NOT Create Git Tags Manually

The GitHub Actions workflow (`.github/workflows/release.yml`) automatically:
1. Detects the new version from `pyproject.toml`
2. Creates the Git tag when publishing the GitHub release
3. Uploads release assets

**If you manually create a tag:**
- The workflow will detect it and skip the build/release steps
- No GitHub release will be created
- No distribution assets will be uploaded

---

## Step 11 — Report back

Show the user:
- The new version number
- The changelog section that was written
- Confirmation that both branches are pushed
