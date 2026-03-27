Release a new version of pyKorf. Follow these steps exactly:

## Step 1 — Determine version bump

Run `git log $(git describe --tags --abbrev=0)..HEAD --oneline` to see commits since the last tag.

- Any `feat:` commit → **minor** bump (0.X.0)
- Only `fix:` / `chore:` / `refactor:` commits → **patch** bump (0.0.X)
- Any breaking change noted → **major** bump (X.0.0)

## Step 2 — Update `pyproject.toml`

Set `version = "X.Y.Z"` in the `[project]` section.

## Step 3 — Update `CHANGELOG.md`

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

## Step 4 — Refresh lockfile

After updating the version in `pyproject.toml`, regenerate the lockfile so the release zip ships an up-to-date `uv.lock`:

```
uv lock
```

## Step 5 — Verify CI passes

Run:
```
uv run ruff check pykorf tests
uv run mypy pykorf
uv run pytest -q
```

Fix any failures before proceeding.

## Step 6 — Commit on dev

```
git add pyproject.toml CHANGELOG.md uv.lock
git commit -m "release: vX.Y.Z"
```

## Step 7 — Merge to main and push

```
git checkout main
git merge dev --no-ff -m "release: vX.Y.Z"
git push origin main
git push origin dev
git checkout dev
```

## Step 8 — Report back

Show the user:
- The new version number
- The changelog section that was written
- Confirmation that both branches are pushed
