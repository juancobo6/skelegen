"""DTOs and shared types for the metacode agentic system.

Pydantic models used as inputs/outputs by the three agents:
- Input agent → ProjectIdeaDefinition
- DTOs and custom types agent → DtosCustomTypes
- Code skeleton agent → CodeSkeleton
"""

from typing import Any

from pydantic import BaseModel, Field


class ProjectIdeaDefinition(BaseModel):
    """Structured output of the Input agent: concise definition of the project.

    Captures what the user wants to build: title, description, optional goals,
    tech preferences, and constraints. Input for DTOs and Code skeleton agents.
    """

    title: str = Field(
        description="Short, clear title of the project.",
        examples=["E-commerce order API", "CLI task runner", "Dashboard service"],
    )
    description: str = Field(
        description="Purpose, scope, and main features of the project.",
        examples=["REST API for orders and inventory, with auth and webhooks."],
    )
    goals: list[str] = Field(
        default_factory=list,
        description="High-level goals or user stories (e.g. 'Users can place orders').",
        examples=[["Users can register and log in", "Admins can manage products"]],
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Preferred tech: languages, frameworks (e.g. Python, FastAPI).",
        examples=[["Python 3.12", "FastAPI", "PostgreSQL"]],
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Constraints (e.g. 'No external APIs', 'Must run offline').",
        examples=[["Python 3.12+ only", "No external API calls"]],
    )

    def __str__(self) -> str:
        """Return a readable summary of the project idea."""
        desc = self.description[:200] + ("..." if len(self.description) > 200 else "")
        lines = [
            f"ProjectIdeaDefinition(title={self.title!r},",
            f"  description={desc!r},",
            f"  goals=[{', '.join(self.goals) or '(none)'}],",
            f"  tech_stack=[{', '.join(self.tech_stack) or '(none)'}],",
            f"  constraints=[{', '.join(self.constraints) or '(none)'}])",
        ]
        return "\n".join(lines)


class DtoField(BaseModel):
    """A single field inside a DTO: name, type, optionality, default, and examples."""

    name: str = Field(
        description="Name of the field (identifier used in code).",
        examples=["user_id", "email", "created_at"],
    )
    description: str = Field(
        description="Human-readable description of what the field represents.",
        examples=["Unique identifier of the user", "User's email address"],
    )
    type: str = Field(
        description="Field type: str, int, list[str], or DTO/custom type name.",
        examples=["str", "int", "list[ItemDto]", "UUID"],
    )
    optional: bool = Field(
        description="Whether the field can be omitted (optional/None).",
        examples=[False, True],
    )
    default: Any = Field(
        description="Default value when the field is omitted (None if no default).",
    )
    examples: list[Any] = Field(
        description="Example values for documentation or validation.",
        examples=[[1, 2], ["a@b.com", "user@example.com"]],
    )


class Dto(BaseModel):
    """Data Transfer Object: named structure with a list of fields.

    Defines request/response bodies, domain entities, or config shapes
    proposed by the DTOs agent and implemented by the code skeleton agent.
    """

    name: str = Field(
        description="DTO name.",
        examples=["OrderCreate", "UserResponse", "Config"],
    )
    description: str = Field(
        description="Purpose and usage of this DTO in the project.",
        examples=["Payload for creating a new order.", "Public user profile from API."],
    )
    fields: list[DtoField] = Field(
        description="Ordered list of fields that make up this DTO.",
    )


class CustomType(BaseModel):
    """Custom type (alias, enum, or domain type) used across the project.

    Not a plain DTO: enums, type aliases, or named types that scripts and
    DTOs reference by name.
    """

    name: str = Field(
        description="Name of the custom type (e.g. Status, Priority, UserId).",
        examples=["OrderStatus", "Priority", "UserId"],
    )
    description: str = Field(
        description="What the type represents and when to use it.",
        examples=["Order status in workflow.", "Priority level for tasks."],
    )
    type: str = Field(
        description="Underlying type: 'enum', 'Literal', 'TypedDict', or type expr.",
        examples=["enum", "Literal['low', 'medium', 'high']", "str"],
    )
    allowed_values: list[str] | None = Field(
        description="For enums/literals: list of allowed values.",
        examples=[["draft", "confirmed", "shipped", "delivered"]],
    )


class DtosCustomTypes(BaseModel):
    """Output of the DTOs agent: all DTOs and custom types for the project.

    Consumed by the Code skeleton agent to generate modules and functions.
    """

    dtos: list[Dto] = Field(
        default_factory=list,
        description="DTOs (structures) defined for the project.",
    )
    custom_types: list[CustomType] = Field(
        description="Custom types (enums, aliases) defined for the project.",
    )

    def __str__(self) -> str:
        """Return a readable summary of DTO and custom type names."""
        dto_names = [d.name for d in self.dtos]
        type_names = [t.name for t in self.custom_types]
        return (
            f"DtosCustomTypes(\n"
            f"  dtos=[{', '.join(dto_names) or '(none)'}],\n"
            f"  custom_types=[{', '.join(type_names) or '(none)'}]\n"
            f")"
        )


class Function(BaseModel):
    """A function in a script: name, description, parameters, return type.

    Parameter/return types reference DTOs or custom types by name. The code
    skeleton agent turns these into real function signatures.
    """

    name: str = Field(
        description="Function name (snake_case for Python).",
        examples=["create_order", "get_user_by_id", "validate_config"],
    )
    description: str = Field(
        description="What the function does and when to use it.",
        examples=["Creates and persists an order.", "Fetches user by ID or raises."],
    )
    parameters: list[str] | str | None = Field(
        description="Input parameters, must be a DTO or custom type name.",
        examples=["OrderCreate", "ItemDto", "None"],
    )
    return_type: str | None = Field(
        description="Return type, must be a DTO or custom type name.",
        examples=["OrderResponse", "list[ItemDto]", "None"],
    )


class Script(BaseModel):
    """A script file: one file with a list of functions.

    Maps to one Python module (e.g. orders.py, auth.py) generated by the
    code skeleton agent.
    """

    name: str = Field(
        description="Script/module name (file name without extension).",
        examples=["orders", "auth", "config"],
    )
    description: str = Field(
        description="Role of this script (e.g. order creation and queries).",
        examples=["Order create/update/retrieval.", "Auth and token handling."],
    )
    functions: list[Function] = Field(
        description="Functions in this script.",
    )


class Module(BaseModel):
    """Logical module: group of related scripts (package or folder).

    A subdomain or layer (e.g. api, domain, db) containing one or more scripts.
    """

    name: str = Field(
        description="Module/package name (folder or namespace).",
        examples=["api", "domain", "db", "services"],
    )
    description: str = Field(
        description="Purpose of this module in the project.",
        examples=["REST API entrypoints.", "Domain models and business logic."],
    )
    scripts: list[Script] = Field(
        description="Scripts (files) in this module.",
    )


class CodeSkeleton(BaseModel):
    """Output of the Code skeleton agent: full module/script/function layout.

    Defines modules, their scripts, and each script's functions. Used to
    generate or fill in actual code files.
    """

    modules: list[Module] = Field(
        default_factory=list,
        description="Modules (packages/folders), each with scripts and functions.",
    )

    def __str__(self) -> str:
        """Return a readable tree of modules, scripts, and functions."""
        lines = ["CodeSkeleton("]
        for mod in self.modules:
            lines.append(f"  {mod.name}/")
            for script in mod.scripts:
                lines.append(f"    {script.name}.py")
                for fn in script.functions:
                    lines.append(f"      - {fn.name}()")
        if not self.modules:
            lines.append("  (no modules)")
        lines.append(")")
        return "\n".join(lines)
