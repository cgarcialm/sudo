---
name: implement
description: Read the plan, propose what to implement next, implement it when confirmed, then test, review, commit, and push to PR
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

Start by reading `.claude/HANDOFF.md` if it exists — it contains the current state of the project and next steps from the previous session.

You are implementing the next step of the Sudo project. Follow these steps in order:

## Steps

### 1. Compact context
Tell the user: "Please run `/compact` now to clear the context window before we start." Then wait for them to confirm before continuing.

### 2. Sync and branch
- Switch to main and pull latest: `git checkout main && git pull origin main`
- Create a new branch for the feature using `feat/short-description` naming: `git checkout -b feat/<name>`

### 3. Read the plan
Read `docs/PLAN.md` and the current codebase to understand:
- What phases are complete
- What is the next logical thing to implement
- What files exist and what they do

### 4. Propose
Present a clear proposal to the user:
- What you are going to implement
- Which files will be created or modified
- Any new dependencies needed

**Stop and wait for confirmation before doing anything.**

### 5. Implement
Once confirmed, implement the proposed changes following `docs/CODING_STANDARDS.md`.

### 6. Test
- Check if tests exist in `tests/` for the changed files
- If not, write them following the standards in `.claude/skills/test/SKILL.md`
- Run `pytest tests/ -v --ignore=tests/test_docker.py`
- Run `pytest tests/test_docker.py -v` (the `docker_image` fixture builds the image automatically)
- Fix any test failures

### 7. Review
- `black .`
- `flake8 .`
- Check all standards from `docs/CODING_STANDARDS.md`
- Fix any linter/formatter issues automatically
- Fix any standards violations
- Update `docs/ARCHITECTURE.md` and `docs/PLAN.md` to reflect any decisions made during implementation (e.g. approach changed, scope narrowed, new constraints). Write the current truth — the next session has no memory of this conversation, so docs must stand on their own.

### 8. Loop until complete
This loop is still implementation — do not exit it until everything is clean and the user confirms.

If automated checks fail, or if the user gives feedback that reveals a gap, treat it as going back into the loop: fix it, re-run tests and review, share results, and wait for confirmation again. Any user feedback during this phase is a signal that something was missed — address it fully before moving on.

Repeat until `pytest` and `flake8` both pass 100% and the user is satisfied.

**Share results with the user and wait for confirmation before continuing.**

### 9. Simplify
Run `/simplify` on the changed code. Fix any issues it finds, then re-run tests to confirm nothing broke.

**Do this every time, before committing — not just when asked.**

### 10. Commit
Stage only the files changed in this implementation and commit with a clear message describing what was implemented.

```bash
git add <specific files>
git commit -m "short description of what was implemented"
```

### 11. Update the plan
Update `docs/PLAN.md` to reflect what was just completed:
- Mark finished items with ✅
- Add any notes about what's pending or changed

### 12. Update skills
Review what was learned during this session — things that worked well, things that were painful, patterns that emerged — and propose improvements to any of the skills in `.claude/skills/`.

Present the proposed changes clearly:
- Which skill(s) to update
- What to change and why

**Stop and wait for confirmation before editing any skill files.**

Once confirmed, apply the changes.

### 13. Write handoff
Write `.claude/HANDOFF.md`. The next session has no memory of this conversation — write everything needed to continue without context. Include:
- **Goal** — what this session set out to do
- **What was tried** — approaches taken
- **What worked** — what's now in place and why
- **What failed** — anything that didn't work and why
- **Next steps** — exactly what to do in the next session, in order

This file is the first thing to read when starting a new session on this project.

### 14. Push and PR
- Push the branch: `git push`
- Create a PR using `gh pr create` with a summary of what was implemented and a test plan
- Return the PR URL

**Stop here and wait for the user to confirm the PR is merged before ending the session.**
