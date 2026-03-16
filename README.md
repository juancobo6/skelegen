# skelegen

**Skelegen** is a CLI tool that generates skeleton code for your projects. Describe what you want to build in natural language; it uses AI to define your project idea, data shapes (DTOs and custom types), and code structure, then writes a Python project with modules, Pydantic models, and function stubs ready for you to implement.

## How it works

Skelegen runs a three-step, conversational flow powered by [pydantic-ai](https://ai.pydantic.dev/) and **Google Gemini**:

1. **Project idea** — You describe what you want to build. The tool asks follow-up questions until it has a clear title, description, goals, tech stack, and constraints.

2. **DTOs and custom types** — From that idea, it proposes Data Transfer Objects (request/response bodies, domain entities, configs) and custom types (enums, type aliases). You can confirm or ask for changes.

3. **Code skeleton** — It then proposes a module/script/function layout (packages, files, and function signatures) that use those DTOs and types. Again you confirm or refine.

After you approve each step, Skelegen generates a project directory:

- A **`models.py`** with Pydantic `BaseModel` DTOs and custom types (enums, `Literal`, etc.).
- **Packages and scripts** — one folder per module, one `.py` file per script, with function stubs that reference the generated models. Each function has a `...  # TODO: implement` body so you can fill in logic.

The result is a consistent, type-hinted skeleton you can extend rather than starting from a blank slate.

## Requirements

- **Python 3.12+**
- **Google API key** — Set the `GOOGLE_API_KEY` environment variable (used for Gemini).

## Installation

From the project root (or from PyPI once published):

```bash
pip install -e .
```

Or install in a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e .
```

## Usage

1. Set your API key:

   ```bash
   set GOOGLE_API_KEY=your_key_here
   ```

2. Run the CLI:

   ```bash
   skelegen
   ```

3. Follow the prompts:
   - Describe your project (e.g. “A REST API for orders and inventory with auth”).
   - Answer any clarifying questions until the tool shows a **ProjectIdeaDefinition**; confirm with `y` if it looks good.
   - Review the proposed **DTOs and custom types**; confirm or describe changes.
   - Review the proposed **code skeleton** (modules, scripts, functions); confirm or describe changes.

4. Skelegen creates a directory named after your project title (e.g. `order_api`) in the current working directory, containing:
   - `models.py` — all DTOs and custom types.
   - One subfolder per module (e.g. `api/`, `domain/`), each with an `__init__.py` and script files (e.g. `orders.py`, `auth.py`) with stubbed functions.

You can then open the generated project and implement the `# TODO` sections.

## Example

```
Defining project idea, describe what you want to build...

> You: A small CLI to track daily habits with categories and optional notes.

> Agent: Do you want to persist data (e.g. file or DB) or keep it in memory for now?
> You: SQLite is fine.

> Agent: [outputs ProjectIdeaDefinition]
> Are you okay with this output? (y/n): y

Defining data transfer objects and custom types...
[outputs DtosCustomTypes]
> Are you okay with this output? (y/n): y

Defining code skeleton...
[outputs CodeSkeleton]
> Are you okay with this output? (y/n): y

Project generated successfully.
```

A new folder (e.g. `habit_tracker`) will appear with `models.py` and modules/scripts ready to implement.

## License

MIT. See the project license file for details.
