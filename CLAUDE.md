# Sudo

A Raspberry Pi robot powered by Claude. Sudo has its own personality, a 16×16 pixel screen, and persistent memory across sessions.

## Structure

- `src/` — Python source: `chat.py`, `memory.py`, `screen.py`, `config.py`, `main.py`
- `tests/` — unit tests and Docker integration tests
- `docs/` — architecture diagram and phase plan
- `memory/` — runtime data: `history.json`, `identity.md`, `screen.png`
- `.claude/` — skills and handoff for Claude-driven development

## Running

```bash
./run.sh                                              # interactive chat (requires ANTHROPIC_API_KEY)
pytest tests/ -v --ignore=tests/test_docker.py        # unit tests
docker build -t sudo . && pytest tests/test_docker.py -v  # Docker integration tests
black . && flake8 .                                   # format and lint
```

## Development workflow

This repo is Claude-driven. Use the skills in `.claude/skills/` for all development work.

- `/implement` — pick up the next phase from `docs/PLAN.md` and implement it end-to-end
- `/review` — review code against `docs/CODING_STANDARDS.md`
- `/simplify` — review for reuse, quality, and efficiency issues

Always read `.claude/HANDOFF.md` first — it has the current state and exact next steps.
