---
name: review
description: Review code against Sudo project coding standards and fix any issues found
allowed-tools: Bash, Read, Glob, Grep, Edit
---

Review the target file(s) against the Sudo coding standards defined in `docs/CODING_STANDARDS.md`.

## Steps

1. Read `docs/CODING_STANDARDS.md`
2. Read the target file(s) — if `$ARGUMENTS` is provided use that, otherwise review all changed files via `git diff --name-only`
3. Run the linter and formatter:
   ```bash
   black --check .
   flake8 .
   ```
4. Check the code against each standard:
   - No logic at module level
   - Entry point uses `if __name__ == "__main__"`
   - Functions have single responsibility
   - Naming conventions followed
   - API errors handled around Claude API calls
   - No bare `except:`
   - No hardcoded secrets
   - Comments only where logic isn't self-evident
5. Fix all linter and formatter issues automatically
6. Report any structural or standards violations and ask before changing them
7. Check that `docs/ARCHITECTURE.md` and `docs/PLAN.md` reflect any decisions made in the implementation — flag any discrepancies and update them. The next session has no memory of this conversation, so docs must reflect the current truth without relying on context from the chat.
8. Check `tests/test_docker.py` — does it reflect what the system actually does on the Pi right now? If the implementation changed the system's behaviour or entrypoint, flag it as a gap and require it to be addressed before committing
