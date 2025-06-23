# Claude Instructions for analytics-assistant

## Environment Setup
- **Local OS**: Ubuntu Linux
- **Remote**: GitHub for code repository and CI/CD
- **Version Control**: Git with GitHub CLI locally
- **Python Environment**: Always use virtual environments with `uv` for Python package management

## Project Overview
Building a Streamlit application for writing natural language analytics and displaying results by connecting to various data sources using MCP (Model Context Protocol).

## Development Workflow
- Use `uv` to create and manage Python virtual environments
- Leverage GitHub CLI (`gh`) for repository operations
- Set up CI/CD pipelines through GitHub Actions
- Focus on defensive security practices only
- **ALWAYS run tests after making code changes** - especially after major modifications
- Run linting and type checking before committing

## Common Commands
- `source .venv/bin/activate && PYTHONPATH=src streamlit run src/app.py` - Run Streamlit app
- `source .venv/bin/activate && uv sync` - Sync dependencies
- `source .venv/bin/activate && uv add <package>` - Add new dependency
- `git add . && git commit -m "message" && git push` - Commit and push changes

## Testing Commands (REQUIRED after code changes)
- `source .venv/bin/activate && python test_runner.py` - Run all tests with coverage
- `source .venv/bin/activate && uv run pytest tests/` - Run tests directly
- `source .venv/bin/activate && uv run ruff check src/` - Run linting
- `source .venv/bin/activate && uv run mypy src/` - Run type checking

## Application Architecture
- **Frontend**: Streamlit for user interface
- **Analytics**: Natural language processing for analytics queries
- **Data Sources**: Multiple data source connections via MCP
- **Visualization**: Results display and visualization within Streamlit

## Security Guidelines
- Implement defensive security measures only
- No malicious code or tools
- Focus on security analysis, detection rules, and defensive capabilities