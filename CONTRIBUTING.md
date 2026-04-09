# Contributing

## Development Environment
Use a project-local virtual environment for isolated dependencies.

### Linux/macOS (bash or zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Fish shell
```bash
python3 -m venv .venv
source .venv/bin/activate.fish
```

## Install
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

For dev tooling:
```bash
pip install -e ".[dev]"
```

## Verify Setup
```bash
pm-pipeline --help
python3 -m src.cli --help
```

## Common Setup Issues

1. Editable install fails with `Cannot import 'setuptools.backends._legacy'`

Ensure [pyproject.toml](pyproject.toml) has:

```toml
build-backend = "setuptools.build_meta"
```

Then rerun:

```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
```

2. `pm-pipeline: command not found` after successful install

```bash
hash -r
pm-pipeline --help
python3 -m src.cli --help
```

## Run Tests
```bash
pytest -q
```

## Lint (if installed)
```bash
ruff check src tests
```

## Change Policy
1. If you change harvest/translate/engine/publish behavior, update README and .github/copilot-instructions.md in the same PR.
2. Keep changes config-driven where possible; avoid hardcoding org-specific behavior.
3. Preserve deterministic outputs and offline-first defaults.
4. For Mermaid diagrams, use the shared default style in templates/mermaid-style.md unless a custom style is explicitly requested.
5. For Copilot chat workflows, keep project skills in `.github/skills/pm-doc-*/SKILL.md` and project agents in `.github/agents/*.agent.md`.
6. When adding or changing skills, update README usage examples in the same PR.
