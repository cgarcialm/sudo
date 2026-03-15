import pathlib
import platform
import subprocess
import tempfile


def _docker_run(base_url, extra_args, stdin):
    return subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            *extra_args,
            "-e",
            "ANTHROPIC_API_KEY=test-key",
            "-e",
            f"ANTHROPIC_BASE_URL={base_url}",
            "sudo",
        ],
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_chat_single_turn(mock_anthropic_server):
    base_url = (
        "http://host.docker.internal:8765"
        if platform.system() == "Darwin"
        else "http://localhost:8765"
    )
    extra_args = [] if platform.system() == "Darwin" else ["--network", "host"]

    result = _docker_run(base_url, extra_args, stdin="hello\nexit\n")

    assert result.returncode == 0
    assert "Sudo:" in result.stdout


def test_chat_multi_turn(mock_anthropic_server):
    """Two messages are sent and two replies are received in the same session."""
    base_url = (
        "http://host.docker.internal:8765"
        if platform.system() == "Darwin"
        else "http://localhost:8765"
    )
    extra_args = [] if platform.system() == "Darwin" else ["--network", "host"]

    result = _docker_run(
        base_url, extra_args, stdin="first message\nsecond message\nexit\n"
    )

    assert result.returncode == 0
    assert result.stdout.count("Sudo:") == 2


def test_memory_written_after_session(mock_anthropic_server):
    """history.json and identity.md are written to the mounted memory volume."""
    base_url = (
        "http://host.docker.internal:8765"
        if platform.system() == "Darwin"
        else "http://localhost:8765"
    )
    extra_args = [] if platform.system() == "Darwin" else ["--network", "host"]

    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        memory_args = ["-v", f"{tmp_dir}:/app/memory"]
        result = _docker_run(base_url, extra_args + memory_args, stdin="hello\nexit\n")

        assert result.returncode == 0
        assert pathlib.Path(tmp_dir, "history.json").exists()
        assert pathlib.Path(tmp_dir, "identity.md").exists()
