# Contributing

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Workflow

```bash
# Setup
git clone https://github.com/YOUR-USERNAME/layman
cd layman
uv sync

# Create branch
git checkout -b feature/my-feature

# Make changes...

# Run linting
just lint

# Test manually
uv run layman

# Commit
git add .
git commit -m "feat: add feature description"

# Push and create PR
git push origin feature/my-feature
```

## Code Style

### Python

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 88 (ruff default)
- Use descriptive variable names

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add three-column layout
fix: correct window tracking on close
docs: update MasterStack documentation
refactor: simplify event handling
```

### Documentation

- Update docs for any API changes
- Include mermaid diagrams for complex flows
- Keep README.md in sync

## Adding a Layout Manager

1. Create new file in `src/layman/managers/`
2. Inherit from `WorkspaceLayoutManager`
3. Set unique `shortName`
4. Override event hooks as needed
5. Add to `managers/__init__.py`
6. Document in `docs/layouts/`

Example:

```python
from layman.managers.workspace import WorkspaceLayoutManager

class MyLayoutManager(WorkspaceLayoutManager):
    shortName = "MyLayout"
    overridesMoveBinds = True

    def __init__(self, con, workspace, workspaceName, options):
        super().__init__(con, workspace, workspaceName, options)
        # Initialize state

    def windowAdded(self, event, workspace, window):
        # Handle new window
        pass
```

## Testing Changes

1. Run linting: `just lint`
2. Test manually in sway/i3
3. Verify with debug mode enabled
4. Test edge cases (rapid window creation, etc.)

## Pull Request Checklist

- [ ] Code follows project style
- [ ] Linting passes (`just lint`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] Changes tested manually
- [ ] No unrelated changes included

## Questions?

Open an issue for discussion before major changes.
