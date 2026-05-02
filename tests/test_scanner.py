import pytest
from app.core.scanner import StaticScanner

@pytest.fixture
def scanner():
    return StaticScanner()

def test_safe_config(scanner):
    config = {
        "mcpServers": {
            "safe-tool": {
                "command": "python",
                "args": ["script.py"]
            }
        }
    }
    results = scanner.scan_config(config)
    assert len(results) == 0

def test_hardcoded_credentials(scanner):
    config = {
        "mcpServers": {
            "bad-tool": {
                "command": "node",
                "env": {
                    "api_key": "12345"
                }
            }
        }
    }
    results = scanner.scan_config(config)
    assert len(results) > 0
    assert any(r.rule_id == "R001" for r in results)

def test_command_execution(scanner):
    config = {
        "mcpServers": {
            "rce-tool": {
                "command": "bash",
                "args": ["-c", "echo test"]
            }
        }
    }
    results = scanner.scan_config(config)
    assert len(results) > 0
    assert any(r.rule_id == "R002" for r in results)

def test_dangerous_combination(scanner):
    config = {
        "mcpServers": {
            "exfil-tool": {
                "command": "python",
                "capabilities": ["read_file", "network_send"]
            }
        }
    }
    results = scanner.scan_config(config)
    assert len(results) > 0
    assert any(r.rule_id == "C001" for r in results)
