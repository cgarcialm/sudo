---
name: implement
description: Read the plan, propose what to implement next, implement it when confirmed, then review, test, commit, and push to PR
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

Start by reading `HANDOFF.md` if it exists — it contains the current state of the project and next steps from the previous session.

You are implementing the next step of the Sudo project. Follow these steps in order:

## Steps

### 1. Read the plan
Read `docs/PLAN.md` and the current codebase to understand:
- What phases are complete
- What is the next logical thing to implement
- What files exist and what they do

### 2. Propose
Present a clear proposal to the user:
- What you are going to implement
- Which files will be created or modified
- Any new dependencies needed

**Stop and wait for confirmation before doing anything.**

### 3. Implement
Once confirmed, implement the proposed changes following `docs/CODING_STANDARDS.md`.

### 4. Review
Run the review skill inline:
- `black .`
- `flake8 .`
- Check all standards from `docs/CODING_STANDARDS.md`
- Fix any linter/formatter issues automatically
- Fix any standards violations

### 5. Test
- Check if tests exist in `tests/` for the changed files
- If not, write them following the standards in `.claude/skills/test/SKILL.md`
- Run `pytest tests/ -v`
- Fix any test failures caused by bugs in the tests
- If tests reveal bugs in the implementation, fix those too

### 6. Commit
Stage only the files changed in this implementation and commit with a clear message describing what was implemented.

```bash
git add <specific files>
git commit -m "short description of what was implemented"
```

### 7. Update the plan
Update `docs/PLAN.md` to reflect what was just completed:
- Mark finished items with ✅
- Add any notes about what's pending or changed

### 8. Push and PR
- Push the branch: `git push`
- Create a PR using `gh pr create` with a summary of what was implemented and a test plan
- Return the PR URL

### 9. Write handoff
Write `HANDOFF.md` at the project root with:
- **Goal** — what this session set out to do
- **What was tried** — approaches taken
- **What worked** — what's now in place and why
- **What failed** — anything that didn't work and why
- **Next steps** — exactly what to do in the next session, in order

This file is the first thing to read when starting a new session on this project.
