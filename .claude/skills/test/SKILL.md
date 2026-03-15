---
name: test
description: Write and run tests for Sudo project files following project standards
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

You are writing and running tests for the Sudo project. Follow these standards:

## Standards

**Framework:** pytest

**Structure:**
- All test files live in `tests/`
- Test files mirror the source: `main.py` → `tests/test_main.py`
- If a test file already exists, add new tests to it rather than creating a new one

**Test types:**
- Unit tests for all logic and functions
- Integration tests for anything that touches external services (Claude API, hardware) — but **always mock external calls** so no real API calls are made and no money is spent
- Use `unittest.mock` or `pytest-mock` for mocking

**Mocking the Anthropic API:**
```python
from unittest.mock import MagicMock, patch

@patch("anthropic.Anthropic")
def test_something(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="mocked response")]
    )
    # test your code here
```

**Naming:**
- `test_<what it does>` for happy path
- `test_<what it does>_when_<condition>` for edge cases

## Steps

1. Read the target file(s) — if `$ARGUMENTS` is provided use that, otherwise use `git diff --name-only` to find changed files
2. Identify what needs testing: functions, classes, edge cases, error handling
3. Check if a test file already exists in `tests/` — add to it if so, create it if not
4. Write the tests following the standards above
5. Install any missing test dependencies (`pip install pytest pytest-mock` if needed)
6. Run `pytest tests/ -v` and report results:
   - How many passed / failed / skipped
   - Full output for any failures
7. If tests fail due to a bug in the tests themselves, fix the tests
8. If tests fail due to a bug in the source code, report it and ask before changing anything
9. **Docker integration test** — if the changes affect code that runs inside the container:
   - Start the mock server: `python tests/mock_anthropic_server.py &`
   - Build the image: `docker build --platform linux/arm64 -t sudo .`
   - Run the container against the mock: `docker run --rm --network host -e ANTHROPIC_API_KEY=test-key -e ANTHROPIC_BASE_URL=http://localhost:8765 sudo`
   - Verify it prints a response and exits cleanly
