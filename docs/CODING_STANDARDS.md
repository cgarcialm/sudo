# Sudo — Coding Standards

## Language & Runtime
- Python 3.11+
- All code must run on ARM64/Linux (Raspberry Pi 4)

## Linter & Formatter
- **Formatter:** `black` (line length 88)
- **Linter:** `flake8` with `black` compatibility
- Run before every commit:
  ```bash
  black .
  flake8 .
  ```
- Config in `pyproject.toml`:
  ```toml
  [tool.black]
  line-length = 88

  [tool.flake8]
  max-line-length = 88
  extend-ignore = E203, W503
  ```

## Structure
- No logic at module level — wrap everything in functions
- Entry point is always `if __name__ == "__main__"`
- One responsibility per function
- Group related functions into modules (e.g. `claude.py`, `camera.py`, `motors.py`)

## Naming
- `snake_case` for variables and functions
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Names should describe what something does, not what it is

## Error Handling
- Always handle `anthropic.APIError` around API calls
- Never swallow exceptions silently — log or re-raise
- No bare `except:` — always specify the exception type

## Security
- No hardcoded secrets or API keys — always use environment variables
- Never commit `.env` files

## Comments
- Only comment where the logic isn't self-evident
- No docstrings required for simple functions
- Add a docstring when a function has non-obvious parameters or side effects

## Tests
- All tests in `tests/`
- Mock all external calls (Claude API, hardware) — no real API calls in tests
- See [test skill](../.claude/skills/test/SKILL.md) for full testing standards
