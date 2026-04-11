Release a new version of pyKorf. Follow these steps exactly:

## Step 0 — Commit all working changes

Run:
```
git status
```

If there are unstaged or uncommitted changes, review and commit them:
```
git diff --stat
git add -A
git commit -m "<describe what you're committing>"
```

## Step 1 — Pre-flight: ensure dev is in sync with main

Run:
```
git fetch origin
git log dev..origin/main --oneline
```

If this prints any commits, main is ahead of dev. Merge it first before proceeding:
```
git merge origin/main --no-ff -m "chore: sync dev with main"
```

## Step 2 — Determine version bump

Run `git log $(git describe --tags --abbrev=0)..HEAD --oneline` to see commits since the last tag.

- Any `feat:` commit → **minor** bump (0.X.0)
- Only `fix:` / `chore:` / `refactor:` commits → **patch** bump (0.0.X)
- Any breaking change noted → **major** bump (X.0.0)

## Step 3 — Update `pyproject.toml`

Set `version = "X.Y.Z"` in the `[project]` section.

## Step 4 — Update `CHANGELOG.md`

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

## Step 5 — Refresh lockfile

After updating the version in `pyproject.toml`, regenerate the lockfile so the release zip ships an up-to-date `uv.lock`:

```
uv lock
```

## Step 6 — Verify CI passes

Run:
```
uv run ruff check pykorf tests
uv run mypy pykorf
uv run pytest -q
```

Fix any failures before proceeding.

## Step 7 — Commit on dev

```
git add pyproject.toml CHANGELOG.md uv.lock
git commit -m "release: vX.Y.Z"
```

## Step 8 — Merge to main, sync back to dev, and push

```
git checkout main
git merge dev --no-ff -m "release: vX.Y.Z"
git push origin main
git checkout dev
git merge main --ff-only
git push origin dev
```

The `--ff-only` merge after switching back to dev fast-forwards dev to include the release merge commit on main.
This keeps both branches at the same tip and prevents main from drifting ahead of dev.

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

## Step 9 — Report back

Show the user:
- The new version number
- The changelog section that was written
- Confirmation that both branches are pushed
