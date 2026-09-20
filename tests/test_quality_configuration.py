"""Guard the shared quality and safety configuration."""

import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parents[1]


def load_pyproject() -> dict[str, Any]:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_coverage_threshold_is_at_least_eighty_five_percent() -> None:
    configuration = load_pyproject()

    assert configuration["tool"]["coverage"]["report"]["fail_under"] >= 85


def test_runtime_dependencies_exclude_cloud_and_command_execution_sdks() -> None:
    configuration = load_pyproject()
    dependencies = " ".join(configuration["project"]["dependencies"]).lower()

    prohibited = ("boto", "kubernetes", "paramiko", "ansible", "openai")
    assert not any(package in dependencies for package in prohibited)


def test_container_smoke_script_is_executable() -> None:
    smoke_script = PROJECT_ROOT / "scripts" / "smoke.sh"

    assert smoke_script.stat().st_mode & 0o111
