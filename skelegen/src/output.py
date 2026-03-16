"""Generate a project directory from ProjectIdeaDefinition, DtosCustomTypes, and CodeSkeleton."""

import re
from pathlib import Path

from .dtos import (
    CodeSkeleton,
    CustomType,
    Dto,
    DtoField,
    DtosCustomTypes,
    Function,
    ProjectIdeaDefinition,
    Script,
)


def _sanitize_dirname(name: str) -> str:
    """Return a filesystem-safe directory name from the project title."""
    name = name.strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[-\s]+", "_", name)
    name = name.lower()
    return name or "project"


def _python_type_hint(field: DtoField) -> str:
    """Convert a DtoField type string to a Python type hint (e.g. for Pydantic)."""
    t = field.type.strip()
    optional = field.optional
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1]
        base = f"list[{inner}]"
    else:
        base = t
    if optional:
        return f"{base} | None"
    return base


def _pydantic_field(field: DtoField) -> str:
    """Generate Field(...) for optional/default, or plain type."""
    if field.optional and field.default is not None:
        return f'Field(default={repr(field.default)}, description="{_esc(field.description)}")'
    if field.optional:
        return f'Field(default=None, description="{_esc(field.description)}")'
    return f'Field(description="{_esc(field.description)}")'


def _esc(s: str) -> str:
    """Escape double quotes for use inside a Python string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _generate_custom_type(ct: CustomType) -> str:
    """Generate Python code for a CustomType (enum or type alias)."""
    if ct.type.lower() == "enum" and ct.allowed_values:
        members = "\n    ".join(
            f"{v.upper().replace('-', '_')} = {repr(v)}" for v in ct.allowed_values
        )
        return (
            f"class {ct.name}(str, Enum):\n"
            f'    """{_esc(ct.description)}"""\n'
            f"    {members}"
        )
    if ct.allowed_values:
        vals = ", ".join(repr(v) for v in ct.allowed_values)
        return f"{ct.name} = Literal[{vals}]  # {_esc(ct.description)}"
    return f"{ct.name} = {ct.type}  # {_esc(ct.description)}"


def _generate_dto(dto: Dto) -> str:
    """Generate Python code for a DTO as a Pydantic BaseModel."""
    lines = [f"class {dto.name}(BaseModel):", f'    """{_esc(dto.description)}"""', ""]
    for f in dto.fields:
        hint = _python_type_hint(f)
        field_def = _pydantic_field(f)
        lines.append(f"    {f.name}: {hint} = {field_def}")
    return "\n".join(lines)


def _generate_models_module(dtos: list[Dto], custom_types: list[CustomType]) -> str:
    """Generate the content of models.py (DTOs and custom types)."""
    parts = [
        '"""Generated models and types."""',
        "",
        "from enum import Enum",
        "from typing import Literal",
        "",
        "from pydantic import BaseModel, Field",
        "",
    ]
    if custom_types:
        parts.append("# Custom types")
        for ct in custom_types:
            parts.append(_generate_custom_type(ct))
            parts.append("")
    if dtos:
        parts.append("# DTOs")
        for dto in dtos:
            parts.append(_generate_dto(dto))
            parts.append("")
    return "\n".join(parts).rstrip()


def _is_valid_param_name(name: str) -> bool:
    """Return True if name is a valid Python parameter name (identifier)."""
    return (
        name.isidentifier()
        and "[" not in name
        and "]" not in name
        and ":" not in name
    )


def _param_name_from_type(type_name: str, index: int) -> str:
    """Suggest a parameter name from a type name. Never returns invalid identifiers."""
    if not type_name or type_name == "None":
        return f"arg{index}"
    name_source = type_name.strip()
    # Strip optional suffix so "str | None" -> "str" for naming.
    for suffix in (" | None", "| None"):
        if name_source.endswith(suffix):
            name_source = name_source[: -len(suffix)].strip()
            break
    # For list[X] / dict[K,V] use inner type for naming so we get valid param names.
    if name_source.startswith("list[") and name_source.endswith("]"):
        name_source = name_source[5:-1].strip()
    elif name_source.startswith("dict[") and name_source.endswith("]"):
        inner = name_source[5:-1].strip()
        name_source = inner.split(",")[-1].strip() if "," in inner else inner
    # OrderCreate -> order_create, UserId -> user_id
    s = re.sub(r"([A-Z])", r"_\1", name_source).strip("_").lower()
    s = s.replace("__", "_") or f"arg{index}"
    if s in ("payload", "data", "request", "item", "config"):
        s = s if index == 0 else f"{s}_{index}"
    # Avoid shadowing builtins: str, int, float, bool, list, dict -> value / value_1
    if s in ("str", "int", "float", "bool", "list", "dict", "type"):
        s = "value" if index == 0 else f"value_{index}"
    s = s or f"arg{index}"
    # If the derived name is still invalid (e.g. agent returned "list[X]" as type), fallback.
    if not _is_valid_param_name(s):
        return f"arg{index}"
    return s


def _parse_parameter_item(raw: str) -> str:
    """Extract type from a parameter string. Handles 'name: type' or plain type."""
    raw = raw.strip()
    if ": " in raw:
        return raw.split(": ", 1)[-1].strip()
    return raw


def _normalize_parameters(func: Function) -> list[tuple[str, str]]:
    """Return list of (param_name, type_name) for the function."""
    p = func.parameters
    if p is None:
        return []
    if isinstance(p, str):
        typ = _parse_parameter_item(p)
        return [(_param_name_from_type(typ, 0), typ)]
    result = []
    for i, raw in enumerate(p):
        typ = _parse_parameter_item(raw)
        name = _param_name_from_type(typ, i)
        result.append((name, typ))
    return result


def _generate_script_content(
    script: Script,
    project_package: str,
) -> str:
    """Generate the content of a script .py file."""
    parts = [
        f'"""{_esc(script.description)}"""',
        "",
        f"from {project_package}.models import *  # noqa: F403, F401",
        "",
    ]
    for fn in script.functions:
        params = _normalize_parameters(fn)
        ret = fn.return_type or "None"
        param_str = ", ".join(f"{name}: {typ}" for name, typ in params)
        parts.append(f"def {fn.name}({param_str}) -> {ret}:")
        parts.append(f'    """{_esc(fn.description)}"""')
        parts.append("    ...  # TODO: implement")
        parts.append("")
    return "\n".join(parts).rstrip()


def generate_project(
    project_idea: ProjectIdeaDefinition,
    dto_custom_types: DtosCustomTypes,
    code_skeleton: CodeSkeleton,
    *,
    output_dir: Path | str = Path.cwd(),
) -> Path:
    """Create a directory named after the project title with Python modules and scripts.

    Writes:
    - <project_title>/models.py — DTOs and custom types from dto_custom_types.
    - <project_title>/<module>/<script>.py — for each module and script in code_skeleton,
      with function stubs that use the generated models.

    Args:
        project_idea: Title and description of the project (title used as dir name).
        dto_custom_types: DTOs and custom types to emit as models.py.
        code_skeleton: Module/script/function layout to emit as packages and .py files.
        output_dir: Parent directory where the project folder is created (default: cwd).

    Returns:
        Path to the created project directory.
    """
    root_name = _sanitize_dirname(project_idea.title)
    base = Path(output_dir) / root_name
    base.mkdir(parents=True, exist_ok=True)

    # Single shared models module at project root
    models_content = _generate_models_module(
        dto_custom_types.dtos,
        dto_custom_types.custom_types,
    )
    (base / "models.py").write_text(models_content, encoding="utf-8")

    project_package = root_name

    for mod in code_skeleton.modules:
        mod_path = base / mod.name
        mod_path.mkdir(parents=True, exist_ok=True)
        (mod_path / "__init__.py").write_text(
            f'"""{_esc(mod.description)}"""\n',
            encoding="utf-8",
        )
        for script in mod.scripts:
            script_content = _generate_script_content(script, project_package)
            (mod_path / f"{script.name}.py").write_text(
                script_content,
                encoding="utf-8",
            )

    return base
