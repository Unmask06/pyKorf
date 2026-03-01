# Contributing to pyKorf

Thank you for your interest in contributing to pyKorf!

## Development Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/pykorf.git
cd pykorf
```

2. **Create a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **Install in development mode:**

```bash
pip install -e ".[dev]"
```

Or with uv:

```bash
uv pip install -e ".[dev]"
```

## Development Workflow

1. **Create a branch:**

```bash
git checkout -b feature/my-feature
```

2. **Make your changes**

3. **Run tests:**

```bash
pytest
```

4. **Run linting:**

```bash
ruff check pykorf tests
ruff format pykorf tests
mypy pykorf
```

5. **Commit and push:**

```bash
git add .
git commit -m "Add feature: description"
git push origin feature/my-feature
```

6. **Create a Pull Request**

## Code Style

- Follow PEP 8
- Use type hints
- Use Google-style docstrings
- Maximum line length: 100 characters
- Use constants from `definitions.py`

## Testing

- Write tests for new features
- Maintain test coverage
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`

## Documentation

- Update docstrings
- Update user guide if needed
- Update API reference

## Commit Messages

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `style:` Formatting

## Questions?

Open an issue or discussion on GitHub.
