from __future__ import annotations

from pathlib import Path
import pytest

from formicx.runtime.process import ProcessManager


@pytest.fixture
def dummy_script(tmp_path: Path) -> Path:
    script = tmp_path / "dummy.py"
    script.write_text("""import time
time.sleep(10)
""")
    return script


def test_process_manager_start_and_terminate(dummy_script: Path):
    pm = ProcessManager()
    handle = pm.start_process("agt_test", dummy_script)

    assert handle.agent_id == "agt_test"
    assert handle.pid > 0
    assert pm.is_running("agt_test")

    exit_code = pm.terminate_process("agt_test", timeout=2.0)
    assert not pm.is_running("agt_test")
    assert exit_code is not None
    assert handle.intentional_stop is True


def test_process_manager_duplicate_start_raises(dummy_script: Path):
    pm = ProcessManager()
    pm.start_process("agt_test", dummy_script)

    try:
        with pytest.raises(RuntimeError):
            pm.start_process("agt_test", dummy_script)
    finally:
        pm.terminate_all()


def test_process_manager_missing_script():
    pm = ProcessManager()
    with pytest.raises(FileNotFoundError):
        pm.start_process("agt_missing", "non_existent_script.py")


def test_process_manager_terminate_all(dummy_script: Path):
    pm = ProcessManager()
    pm.start_process("agt_1", dummy_script)
    pm.start_process("agt_2", dummy_script)

    assert pm.is_running("agt_1")
    assert pm.is_running("agt_2")

    results = pm.terminate_all()
    assert not pm.is_running("agt_1")
    assert not pm.is_running("agt_2")
    assert len(results) == 2
