from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("PySide6.QtNetwork")

ROOT = Path(__file__).resolve().parents[1]


def test_single_instance_forwards_paths(qapp, tmp_path):
    from app.single_instance import SingleInstance

    name = "ffc-test-" + uuid.uuid4().hex
    server = SingleInstance(name)
    try:
        assert server.listen()
        received: list[list[str]] = []
        server.paths_received.connect(received.append)
        source = tmp_path / "sample.txt"
        source.write_text("hello", encoding="utf-8")

        code = (
            "import sys\n"
            "from PySide6.QtCore import QCoreApplication\n"
            "from app.single_instance import SingleInstance\n"
            "app = QCoreApplication([])\n"
            f"ok = SingleInstance({json.dumps(name)}).notify_running("
            f"[{json.dumps(str(source))}])\n"
            "raise SystemExit(0 if ok else 3)\n"
        )
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        environment["PYTHONPATH"] = (
            str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
        )
        process = subprocess.Popen(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.time() + 15
            while not received and process.poll() is None and time.time() < deadline:
                qapp.processEvents()
                time.sleep(0.01)
            while not received and time.time() < deadline:
                qapp.processEvents()
                time.sleep(0.01)
            stdout, stderr = process.communicate(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        assert process.returncode == 0, stderr or stdout
        assert received == [[str(source)]]
    finally:
        server.close()
        qapp.processEvents()
