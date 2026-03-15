import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def docker_image():
    """Build the Docker image before running Docker integration tests."""
    result = subprocess.run(
        ["docker", "build", "--platform", "linux/arm64", "-t", "sudo", "."],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Docker build failed:\n{result.stderr.decode()}")


@pytest.fixture(scope="session")
def mock_anthropic_server(docker_image):
    proc = subprocess.Popen(["python3", "tests/mock_anthropic_server.py"])
    time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()
