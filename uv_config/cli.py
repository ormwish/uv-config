# uv_config/cli.py
"""
cli.py — Typer CLI для работы с конфигом uv
"""
from pathlib import Path
import sys
import inspect
import textwrap

import typer
from dynaconf import Dynaconf

from uv_config.core import load_any, dump_toml, ToolUv, Pyproject

app = typer.Typer(add_completion=False)
from typing import List
from tomlkit import dumps, item


@app.command(help="Проверить конфигурацию на валидность")
def validate(
    path: Path = typer.Argument(..., help="pyproject.(toml|yaml|json)")
):
    try:
        data = load_any(path)
        py = Pyproject(**data)  # проверка вложенной секции uv
        typer.echo("✅ Конфигурация валидна!")
        typer.echo(f"resolution = {py.uv.resolution}")
    except Exception as exc:
        typer.echo("❌ Ошибка конфигурации:", err=True)
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)


@app.command(help="Установить/изменить параметр в [tool.uv]")
def set(
    path: Path = typer.Argument(...),
    key: str = typer.Argument(..., help="например: resolution"),
    value: str = typer.Argument(..., help="новое значение"),
):
    data = load_any(path)
    data.setdefault("tool", {}).setdefault("uv", {})[key] = value
    ToolUv(**data["tool"]["uv"])  # валидация
    if path.suffix == ".toml":
        dump_toml(data, path)
    else:
        dump_toml(data, path.with_suffix(".toml"))
    typer.echo("✅ Параметр установлен")


@app.command(help="Сгенерировать pyproject.toml с дефолтами")
def init(
    dest: Path = Path("pyproject.toml")
):
    defaults = ToolUv(
        package=True,
        resolution="highest"
    ).model_dump(exclude_none=True, by_alias=True)
    dump_toml({"tool": {"uv": defaults}}, dest)
    typer.echo(f"Создан файл {dest}")


@app.command(help="Показать справку по параметру uv")
def param(name: str):
    field = ToolUv.model_fields.get(name) or ToolUv.model_fields.get(name.replace("-", "_"))
    if not field:
        typer.echo("❌ Нет такого параметра")
        raise typer.Exit(code=1)
    typer.echo(f"{name}: {field.annotation}")
    if hasattr(field.annotation, "__members__"):
        choices = ", ".join(field.annotation.__members__)
        typer.echo(f"Возможные значения: {choices}")
    doc = inspect.getdoc(field.annotation) or inspect.getdoc(field.field_info.alias) or ""
    if doc:
        typer.echo(textwrap.dedent(doc))


@app.command(help="Слить defaults + YAML ➜ pyproject.toml")
def merge(
    yaml_file: Path = typer.Argument(..., exists=True, help="pyproject.yaml"),
    toml_file: Path = typer.Argument("pyproject.toml", help="целевой TOML-файл"),
    merge_enabled: bool = typer.Option(True, help="использовать правила dynaconf merge"),
):
    # defaults
    defaults = ToolUv(
        package=True,
        resolution="highest"
    ).model_dump(exclude_none=True, by_alias=True)

    # dynaconf merge
    settings = Dynaconf(
        settings_files=[yaml_file],
        merge_enabled=merge_enabled
    )
    overrides = settings.get("tool", {}).get("uv", {}) or {}

    merged = {**defaults, **overrides}
    ToolUv(**merged)  # валидация

    dump_toml({"tool": {"uv": merged}}, toml_file)
    typer.echo(f"✅ Конфигурация записана в {toml_file}")

@app.command(help="Вывести текущую [tool.uv] с аннотациями описаний")
def annotate(
    path: Path = typer.Argument("pyproject.toml", help="путь к pyproject.toml")
):
    """
    Показывает все поля tool.uv, текущие значения и их описание (из docstring моделей).
    """
    data = load_any(path)
    uv_cfg = data.get("tool", {}).get("uv", {})

    schema = ToolUv.model_json_schema(by_alias=True)
    props = schema["properties"]

    lines: List[str] = ["# Annotated [tool.uv] configuration\n"]
    for key, meta in props.items():
        title = meta.get("title", key)
        desc = meta.get("description", "").strip()
        enum = meta.get("enum")
        default = ToolUv.model_fields.get(key.replace("-", "_")).default
        val = uv_cfg.get(key, default)

        lines.append(f"## {title}")
        if desc:
            for dline in desc.splitlines():
                lines.append(f"# {dline}")
        if enum:
            lines.append(f"# допустимые: {enum}")
        if default is not None:
            lines.append(f"# значение по умолчанию: {default}")

        # Сериализуем текущее значение
        if isinstance(val, (dict, list)):
            from tomlkit import dumps, item
            repr_val = dumps(item(val)).strip()
        else:
            repr_val = repr(val)
        lines.append(f"{key} = {repr_val}\n")

    typer.echo("\n".join(lines))


if __name__ == "__main__":
    app()
