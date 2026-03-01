# pyKorf Documentation

This directory contains the complete documentation for pyKorf.

## Building Documentation

### Prerequisites

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

### Serve Locally

```bash
mkdocs serve
```

### Build

```bash
mkdocs build
```

### Deploy

```bash
mkdocs gh-deploy
```

## Documentation Structure

```
docs/
├── index.md                      # Home page
├── getting-started/              # Getting started guides
│   ├── installation.md
│   ├── quickstart.md
│   └── concepts.md
├── user-guide/                   # User guides
│   ├── loading-models.md
│   ├── working-with-elements.md
│   ├── multi-case-analysis.md
│   ├── connectivity.md
│   ├── validation.md
│   ├── export-import.md
│   ├── query-dsl.md
│   └── visualization.md
├── api/                          # API reference
│   ├── overview.md
│   ├── model.md
│   ├── elements.md
│   └── ...
├── cli/                          # CLI reference
│   ├── overview.md
│   └── commands.md
├── advanced/                     # Advanced topics
│   └── ...
├── development/                  # Development docs
│   ├── contributing.md
│   └── changelog.md
└── about/                        # About
    └── license.md
```

## Writing Documentation

### Style Guide

- Use Google-style docstrings
- Include code examples
- Use type hints
- Keep lines under 100 characters

### Adding Pages

1. Create `.md` file in appropriate directory
2. Add to `mkdocs.yml` navigation
3. Use mkdocstrings for API docs

### Code Examples

Use fenced code blocks with language:

```python
from pykorf import Model

model = Model()
```

### Admonitions

```markdown
!!! note "Title"
    Content here

!!! warning "Important"
    Warning content
```
