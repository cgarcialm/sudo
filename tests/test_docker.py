import os
import pathlib
import platform
import subprocess
import tempfile
import time


def _base_url():
    if platform.system() == "Darwin":
        return "http://host.docker.internal:8765"
    return "http://localhost:8765"


def _network_args():
    if platform.system() == "Darwin":
        return []
    return ["--network", "host"]


def _run_sudo(extra_args, stdin, memory_dir=None):
    """Run Sudo via run.sh, injecting extra docker args and piping stdin."""
    base_url = _base_url()
    network_args = _network_args()

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
    """Tool tags are parsed internally and never shown in the terminal."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo([], stdin="hello\nexit\n", memory_dir=tmp_dir)

    assert result.returncode == 0
    assert "<screen>" not in result.stdout
    assert "<remember>" not in result.stdout
    assert "Sudo:" in result.stdout


def test_memory_written_after_session(mock_anthropic_server):
    """All memory files are written to the mounted volume after a session."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        result = _run_sudo([], stdin="hello\nexit\n", memory_dir=tmp_dir)

        assert result.returncode == 0
        assert pathlib.Path(tmp_dir, "history.json").exists()
        assert pathlib.Path(tmp_dir, "identity.md").exists()
        assert pathlib.Path(tmp_dir, "summaries.json").exists()
        assert pathlib.Path(tmp_dir, "notes.md").exists()


def test_expression_loop_fires_without_crashing(mock_anthropic_server):
    """Expression loop fires at least once and does not crash the process."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        env = {**os.environ, "ANTHROPIC_API_KEY": "test-key", "MEMORY_DIR": tmp_dir}
        proc = subprocess.Popen(
            [
                "./run.sh",
                "-e",
                f"ANTHROPIC_BASE_URL={_base_url()}",
                "-e",
                "EXPRESSION_INTERVAL_SECONDS=2",
                *_network_args(),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        proc.stdin.write("hello\n")
        proc.stdin.flush()
        time.sleep(4)
        proc.stdin.write("exit\n")
        proc.stdin.flush()
        stdout, stderr = proc.communicate(timeout=30)

    assert proc.returncode == 0
    assert "[expression loop]" not in stderr
