"""Main script for the skelegen CLI."""

import os
import shutil

from skelegen.src.agents import (
    init_code_skeleton_agent,
    init_dto_agent,
    init_input_agent,
)
from skelegen.src.cli import cli
from skelegen.src.dtos import CodeSkeleton, DtosCustomTypes, ProjectIdeaDefinition
from skelegen.src.output import generate_project


def main() -> None:
    """Main function for the metacode project."""
    if os.getenv("GOOGLE_API_KEY") is None:
        raise ValueError("GOOGLE_API_KEY is not set")

    console_length = shutil.get_terminal_size().columns
    print("\n" + "-" * console_length)
    print("\nDefining project idea, describe what you want to build...")
    input_agent = init_input_agent()
    project_idea_definition: ProjectIdeaDefinition = cli(input_agent)
    print("\nProject idea defined.")
    print("\n" + "-" * console_length)

    print("\nDefining data transfer objects and custom types...")
    dto_agent = init_dto_agent(project_idea_definition)
    dto_custom_types: DtosCustomTypes = cli(
        dto_agent,
        "Please define the data transfer objects and custom types for the project.",
    )
    print("\nData transfer objects and custom types defined.")
    print("\n" + "-" * console_length)

    print("\nDefining code skeleton...")
    code_skeleton_agent = init_code_skeleton_agent(
        project_idea_definition, dto_custom_types
    )
    code_skeleton: CodeSkeleton = cli(
        code_skeleton_agent,
        hot_start="Please define the code skeleton for the project.",
    )
    print("\nCode skeleton defined.")
    print("\n" + "-" * console_length)

    try:
        generate_project(project_idea_definition, dto_custom_types, code_skeleton)
        print("\nProject generated successfully.")
    except Exception as e:
        print(f"Error generating project: {e}")
