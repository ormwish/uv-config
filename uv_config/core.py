# uv_config/core.py
"""
core.py — Pydantic-модели для [tool.uv] + утилиты работы с конфигами
"""
from __future__ import annotations
from typing import Optional, List, Dict, Union
from enum import Enum
from pathlib import Path
import json
import tomlkit
import ruamel.yaml as _yaml
from pydantic import BaseModel, Field, ConfigDict, ValidationError

# ---------- ENUMS ----------
class Resolution(str, Enum):
    highest = "highest"
    lowest = "lowest"
    lowest_direct = "lowest-direct"

class Prerelease(str, Enum):
    allow = "allow"
    disallow = "disallow"
    if_necessary = "if-necessary"
    explicit = "explicit"

class PythonPreference(str, Enum):
    managed = "managed"
    system = "system"
    only_managed = "only-managed"
    only_system = "only-system"

# ---------- SOURCES ----------
class GitSource(BaseModel):
    git: str
    tag: Optional[str] = None
    branch: Optional[str] = None
    rev: Optional[str] = None
    subdirectory: Optional[str] = None
    marker: Optional[str] = None

class UrlSource(BaseModel):
    url: str
    marker: Optional[str] = None

class PathSource(BaseModel):
    path: str
    editable: Optional[bool] = None
    package: Optional[bool] = None
    marker: Optional[str] = None

class WorkspaceSource(BaseModel):
    workspace: bool = True
    marker: Optional[str] = None

class IndexSource(BaseModel):
    index: str
    extra: Optional[str] = None
    marker: Optional[str] = None

Source = Union[
    GitSource,
    UrlSource,
    PathSource,
    WorkspaceSource,
    IndexSource,
    List[Union[GitSource, UrlSource, PathSource, WorkspaceSource, IndexSource]],
]

# ---------- MAIN MODEL ----------
class ToolUv(BaseModel):
    """
    Полная модель для секции [tool.uv] pyproject.toml
    """
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True
    )

    package: Optional[bool] = None
    managed: Optional[bool] = None
    required_version: Optional[str] = Field(None, alias="required-version")
    resolution: Optional[Resolution] = None
    prerelease: Optional[Prerelease] = None
    python_preference: Optional[PythonPreference] = Field(None, alias="python-preference")
    sources: Optional[Dict[str, Source]] = None

    # Все остальные поля можно добавить аналогично...
    # dev_dependencies, default_groups, cache_dir, etc.

class Pyproject(BaseModel):
    """
    Обёртка для всего pyproject.toml, чтобы удобно доставать ToolUv
    """
    tool: Dict[str, dict]

    @property
    def uv(self) -> ToolUv:
        cfg = self.tool.get("uv")
        if cfg is None:
            raise ValueError("[tool.uv] section not found")
        return ToolUv(**cfg)

# ---------- IO HELPERS ----------
def load_any(path: Path) -> dict:
    """
    Загружает TOML, YAML или JSON в Python dict
    """
    suffix = path.suffix.lower()
    if suffix == ".toml":
        return tomlkit.parse(path.read_text("utf-8"))
    if suffix in {".yml", ".yaml"}:
        yaml = _yaml.YAML(typ="safe")
        return yaml.load(path.read_text("utf-8"))
    if suffix == ".json":
        return json.loads(path.read_text("utf-8"))
    raise ValueError("Unsupported file type, use .toml/.yaml/.yml/.json")

def dump_toml(data: dict, dest: Path) -> None:
    """
    Сохраняет Python dict в TOML-файл с помощью tomlkit
    """
    doc = tomlkit.document()
    doc.update(data)
    dest.write_text(tomlkit.dumps(doc), "utf-8")
