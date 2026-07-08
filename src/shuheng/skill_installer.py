"""Install Shuheng-owned shared skills for local agent interoperability."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
import os
from pathlib import Path
from typing import Mapping


SHARED_SKILL_ROOT_ENV = "SHUHENG_SHARED_SKILL_ROOT"
SHUHENG_AGENT_GATEWAY_SKILL_NAME = "shuheng-agent-gateway"
SHUHENG_AGENT_GATEWAY_TEMPLATE_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
)


@dataclass(frozen=True)
class InstalledSkill:
    """Result of installing a bundled Shuheng skill template."""

    name: str
    destination: Path
    files: tuple[Path, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "schema_version": "shuheng.skill_install.v1",
            "status": "installed",
            "name": self.name,
            "destination": str(self.destination),
            "files": [str(path) for path in self.files],
        }


def shared_skill_root(path: str | os.PathLike[str] | None = None, *, env: Mapping[str, str] | None = None) -> Path:
    """Resolve the shared multi-agent skill root."""

    env = env or os.environ
    raw = str(path or env.get(SHARED_SKILL_ROOT_ENV) or "~/.agents/skills")
    return Path(raw).expanduser()


def _template_resource(relative_path: str):
    resource = resources.files("shuheng").joinpath("builtin_skills", SHUHENG_AGENT_GATEWAY_SKILL_NAME)
    for part in relative_path.split("/"):
        resource = resource.joinpath(part)
    return resource


def install_agent_gateway_skill(skill_root: str | os.PathLike[str] | None = None) -> InstalledSkill:
    """Install or update Shuheng's shared local agent gateway skill."""

    root = shared_skill_root(skill_root)
    destination = root / SHUHENG_AGENT_GATEWAY_SKILL_NAME
    written: list[Path] = []
    for relative_path in SHUHENG_AGENT_GATEWAY_TEMPLATE_FILES:
        resource = _template_resource(relative_path)
        if not resource.is_file():
            raise FileNotFoundError(f"bundled Shuheng skill template is missing: {relative_path}")
        target = destination / Path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = resource.read_bytes()
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
        written.append(target)
    return InstalledSkill(name=SHUHENG_AGENT_GATEWAY_SKILL_NAME, destination=destination, files=tuple(written))
