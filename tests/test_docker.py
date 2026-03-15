import platform
import subprocess


def test_container_responds_via_mock(mock_anthropic_server):
    base_url = (
        "http://host.docker.internal:8765"
        if platform.system() == "Darwin"
        else "http://localhost:8765"
    )
    extra_args = [] if platform.system() == "Darwin" else ["--network", "host"]

    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            *extra_args,
            "-e",
            "ANTHROPIC_API_KEY=test-key",
            "-e",
            f"ANTHROPIC_BASE_URL={base_url}",
            "sudo",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0
