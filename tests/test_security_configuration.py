"""Security-policy configuration guards."""

import json
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parents[1]


def test_github_actions_are_pinned_to_immutable_commits() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    references = re.findall(r"uses:\s+[^@\s]+@([^\s]+)", workflow)

    assert references
    assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in references)


def test_secret_baseline_contains_no_accepted_findings() -> None:
    baseline = json.loads((PROJECT_ROOT / ".secrets.baseline").read_text(encoding="utf-8"))

    assert baseline["results"] == {}


def test_dependabot_covers_source_container_and_workflow_dependencies() -> None:
    configuration = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    ecosystems = {update["package-ecosystem"] for update in configuration["updates"]}

    assert ecosystems == {"uv", "docker", "github-actions"}
