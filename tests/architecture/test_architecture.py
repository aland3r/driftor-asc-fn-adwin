import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_import_contracts_hold():
    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "--config", str(ROOT / ".importlinter")],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_function_app_is_the_only_entry_point():
    source = (ROOT / "function_app.py").read_text()
    assert "DetectDriftsHandler" in source
    assert "from river" not in source, "o adapter do river fica em adwin/infrastructure"
