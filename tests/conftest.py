import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def mock_anthropic_server():
    proc = subprocess.Popen(["python3", "tests/mock_anthropic_server.py"])
    time.sleep(0.5)
    yield
    proc.terminate()
    proc.wait()
