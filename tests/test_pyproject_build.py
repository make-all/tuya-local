"""Protects `uv build` (and any PEP 517 frontend) from failing to parse pyproject.toml."""

import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_uv_build_backend_module_name_is_a_string():
    """The uv_build backend requires `module-name` to be a single string, not a list.

    A list value ("sequence") is rejected by uv_build's schema with
    `invalid type: sequence, expected a string`, which makes `uv build` fail
    before it can even build the package.
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)

    module_name = data["tool"]["uv"]["build-backend"]["module-name"]

    assert isinstance(module_name, str)


def test_uv_build_succeeds():
    """`uv build` must produce a wheel/sdist instead of failing on pyproject.toml parsing."""
    result = subprocess.run(
        ["uv", "build", "--out-dir", "/tmp/tuya-local-test-dist"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "invalid type: sequence, expected a string" not in result.stderr
