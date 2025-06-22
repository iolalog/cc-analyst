# Claude Instructions for cc-analyst

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

## Common Commands
- `source $HOME/.local/bin/env && cd src && uv run streamlit run app.py` - Run Streamlit app
- `source $HOME/.local/bin/env && uv sync` - Sync dependencies
- `source $HOME/.local/bin/env && uv add <package>` - Add new dependency
- `git add . && git commit -m "message" && git push` - Commit and push changes

## Application Architecture
- **Frontend**: Streamlit for user interface
- **Analytics**: Natural language processing for analytics queries
- **Data Sources**: Multiple data source connections via MCP
- **Visualization**: Results display and visualization within Streamlit

## Security Guidelines
- Implement defensive security measures only
- No malicious code or tools
- Focus on security analysis, detection rules, and defensive capabilities