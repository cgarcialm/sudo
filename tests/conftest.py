import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def docker_image():
    """Build the Docker image before running Docker integration tests."""
    subprocess.run(
        ["docker", "build", "--platform", "linux/arm64", "-t", "sudo", "."],
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def mock_anthropic_server(docker_image):
    proc = subprocess.Popen(["python3", "tests/mock_anthropic_server.py"])
    time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()
