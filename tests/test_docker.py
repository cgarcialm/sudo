import os
import pathlib
import platform
import subprocess
import tempfile


def _run_sudo(extra_args, stdin, memory_dir=None):
    """Run Sudo via run.sh, injecting extra docker args and piping stdin."""
    is_darwin = platform.system() == "Darwin"
    base_url = (
        "http://host.docker.internal:8765" if is_darwin else "http://localhost:8765"
    )
    network_args = [] if is_darwin else ["--network", "host"]

    env = {
        **os.environ,
        "ANTHROPIC_API_KEY": "test-key",
    }
    if memory_dir:
        env["MEMORY_DIR"] = memory_dir

    return subprocess.run(
        [
            "./run.sh",
            "-e",
            f"ANTHROPIC_BASE_URL={base_url}",
            *network_args,
            *extra_args,
        ],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def test_chat_single_turn(mock_anthropic_server):
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo([], stdin="hello\nexit\n", memory_dir=tmp_dir)

    assert result.returncode == 0
    assert "Sudo:" in result.stdout


def test_chat_multi_turn(mock_anthropic_server):
    """Two messages are sent and two replies are received in the same session."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo(
            [], stdin="first message\nsecond message\nexit\n", memory_dir=tmp_dir
        )

    assert result.returncode == 0
    assert result.stdout.count("Sudo:") == 2


def test_screen_tag_stripped_from_output(mock_anthropic_server):
    """<screen> blocks are parsed internally and never shown in the terminal."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo([], stdin="hello\nexit\n", memory_dir=tmp_dir)

    assert result.returncode == 0
    assert "<screen>" not in result.stdout
    assert "Sudo:" in result.stdout


def test_memory_written_after_session(mock_anthropic_server):
    """history.json, identity.md, and summaries.json are written to the mounted memory volume."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo([], stdin="hello\nexit\n", memory_dir=tmp_dir)

        assert result.returncode == 0
        assert pathlib.Path(tmp_dir, "history.json").exists()
        assert pathlib.Path(tmp_dir, "identity.md").exists()
        assert pathlib.Path(tmp_dir, "summaries.json").exists()
