"""Agents for the metacode agentic system."""

from pydantic_ai import Agent

from .dtos import CodeSkeleton, DtosCustomTypes, ProjectIdeaDefinition
from .prompts import (
    get_code_skeleton_agent_prompt,
    get_dto_agent_prompt,
    get_input_agent_prompt,
)

MODEL = "google-gla:gemini-2.5-flash"


def init_input_agent() -> Agent[None, str | ProjectIdeaDefinition]:
    """Initialize the input agent.

    The input agent is responsible for gathering the project idea from the user.
    """
    return Agent[None, ProjectIdeaDefinition | str](
        model=MODEL,
        instructions=get_input_agent_prompt(),
        output_type=str | ProjectIdeaDefinition,
        output_retries=3,
    )


def init_dto_agent(
    project_idea_definition: ProjectIdeaDefinition,
) -> Agent[None, DtosCustomTypes]:
    """Initialize the DTO agent.

    The DTO agent is responsible for defining the data shapes and types for the project.
    """
    return Agent[None, DtosCustomTypes](
        model=MODEL,
        instructions=get_dto_agent_prompt(project_idea_definition),
        output_type=DtosCustomTypes,
        output_retries=3,
    )


def init_code_skeleton_agent(
    project_idea_definition: ProjectIdeaDefinition, dto_custom_types: DtosCustomTypes
) -> Agent[None, CodeSkeleton]:
    """Initialize the code skeleton agent.

    The code skeleton agent is responsible for defining the code skeleton for the project.
    """
    return Agent[None, CodeSkeleton](
        model=MODEL,
        instructions=get_code_skeleton_agent_prompt(
            project_idea_definition, dto_custom_types
        ),
        output_type=CodeSkeleton,
        output_retries=3,
    )
