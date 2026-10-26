"""Validate project agent policy and lossless context archives; no model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
MODELS = {"gpt-6.1-sol", "gpt-6-luna", "gpt-6-astra"}
EFFORTS = {"low", "medium", "high"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def check_model(config: dict, label: str) -> None:
    require(config.get("model") in MODELS, f"{label}: model outside approved 6+ catalog")
    require(config.get("model_reasoning_effort") in EFFORTS,
            f"{label}: missing or excessive default reasoning effort")


def validate() -> dict:
    config = read_toml(ROOT / ".codex/config.toml")
    check_model(config, "principal")
    require(set(config) == {"model", "model_reasoning_effort", "agents"},
            "project config must not change global permissions/provider/profiles")
    agents = config["agents"]
    require(agents.get("enabled") is True, "agents disabled")
    require(type(agents.get("max_concurrent_threads_per_session")) is int
            and agents["max_concurrent_threads_per_session"] == 1,
            "expected exactly one auxiliary slot, excluding primary")
    check_model({"model": agents.get("default_subagent_model"),
                 "model_reasoning_effort": agents.get("default_subagent_reasoning_effort")},
                "auxiliary default")
    expected = {"fifa_explorer", "fifa_implementer", "fifa_reviewer", "fifa_architect"}
    found = set()
    for path in sorted((ROOT / ".codex/agents").glob("*.toml")):
        role = read_toml(path)
        require(set(role) == {"name", "description", "model", "model_reasoning_effort",
                              "developer_instructions"}, f"unexpected schema: {path.name}")
        require(role["name"] == path.stem and path.stem not in found,
                f"duplicate or mismatched role: {path.name}")
        for key in ("description", "developer_instructions"):
            require(isinstance(role[key], str) and bool(role[key].strip()),
                    f"{path.name}: empty {key}")
        check_model(role, path.name)
        found.add(path.stem)
    require(found == expected, "missing or unexpected agent role")

    manifest = json.loads((ROOT / "docs/history/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        archive = (ROOT / entry["archive"]).read_bytes()
        require(len(archive) == entry["bytes"]
                and hashlib.sha256(archive).hexdigest() == entry["sha256"],
                f"archive bytes changed: {entry['archive']}")
        original = subprocess.check_output(
            ["git", "show", f"{manifest['source_commit']}:{entry['source']}"], cwd=ROOT)
        require(hashlib.sha256(original).hexdigest() == entry["git_blob_sha256"]
                and archive.replace(b"\r\n", b"\n") == original,
                f"archive differs from source revision: {entry['source']}")
    status_lines = len((ROOT / "STATUS.md").read_text(encoding="utf-8").splitlines())
    require(60 <= status_lines <= 100, "checkpoint must contain 60–100 lines")
    return {"model": config["model"], "auxiliary_slots": 1, "roles": sorted(found),
            "archives_verified": len(manifest["files"]), "status_lines": status_lines}


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Agent setup validation failed: {error}", file=sys.stderr)
        sys.exit(1)
