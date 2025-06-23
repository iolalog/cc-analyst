# Analytics Assistant 📊

A Streamlit web application for natural language analytics and visualization based on various data sources using MCP (Model Context Protocol). Ask questions in plain English and get AI-powered insights with interactive visualizations.

Currently configured with European Central Bank (ECB) data as the primary example data source.

## Features

- **Natural Language Queries**: Ask questions about data in plain English
- **Multiple Data Sources**: Extensible architecture for connecting to various data sources via MCP
- **AI-Powered Analysis**: Claude AI provides insights and explanations
- **Interactive Visualizations**: Dynamic charts with Plotly
- **Current Data Source**: European Central Bank (ECB) Statistical Data Warehouse
  - Key Interest Rates: Main Refinancing Rate (MRR), Deposit Facility Rate (DFR), Marginal Lending Facility Rate (MLF)

## Architecture

- **Frontend**: Streamlit for user interface
- **Data Sources**: Multiple data source connections via MCP (Model Context Protocol)
- **AI Processing**: Claude API for natural language understanding and analysis
- **Visualization**: Plotly for interactive charts
- **Data Handling**: Pandas for data manipulation
- **Current Implementation**: ECB Statistical Data Warehouse API as example data source

## Prerequisites

- Python 3.12+
- uv package manager
- Anthropic API key (Claude)

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/iolalog/analytics-assistant.git
   cd analytics-assistant
   ```

2. **Set up environment**:
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env
   
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate
   uv sync
   ```

3. **Configure API access**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Run the application**:
   ```bash
   source .venv/bin/activate && PYTHONPATH=src streamlit run src/app.py
   ```

5. **Open your browser** to http://localhost:8501

## Usage Examples

### Sample Questions You Can Ask:

- "Show me ECB interest rate developments over the last 2 years"
- "What are the current deposit facility rates?"
- "Compare all three key ECB rates over time"
- "Display main refinancing rate trends since 2020"

### How It Works:

1. **Ask**: Enter your question in natural language
2. **Parse**: Claude AI interprets your question and identifies the data needed
3. **Fetch**: The app retrieves real-time data from ECB's API
4. **Analyze**: Claude AI analyzes the data and provides insights
5. **Visualize**: Interactive charts display the results

## Project Structure

```
analytics-assistant/
├── src/
│   ├── app.py                 # Main Streamlit application
│   ├── claude_processor.py    # Claude API integration
│   └── mcp_ecb_server.py     # ECB data fetching (example data source)
├── tests/                     # Comprehensive test suite
│   ├── test_claude_processor.py
│   ├── test_mcp_ecb_server.py
│   ├── test_app.py
│   └── test_integration.py
├── .env.example              # Environment variables template
├── .mcp.json                # MCP server configuration
├── CLAUDE.md                # Claude Code instructions
├── pyproject.toml           # Project dependencies
├── test_runner.py           # Test runner script
└── README.md               # This file
```

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# Required: Claude API key
ANTHROPIC_API_KEY=your_api_key_here

# Optional: ECB API base URL (default provided)
ECB_API_BASE_URL=https://data-api.ecb.europa.eu
```

### Available ECB Data

The app currently supports:
- **Main Refinancing Rate (MRR)**: ECB's primary policy rate
- **Deposit Facility Rate (DFR)**: Rate for overnight deposits
- **Marginal Lending Facility Rate (MLF)**: Rate for overnight lending

## Development

### Common Commands

All commands should be run from the project root directory and require activating the uv environment first:

```bash
# Activate virtual environment (run this first for each new terminal session)
source .venv/bin/activate

# Run the app
PYTHONPATH=src streamlit run src/app.py

# Sync dependencies (after pulling changes or updating pyproject.toml)
uv sync

# Add new dependency
uv add <package>

# Commit changes
git add . && git commit -m "message" && git push
```

**Note**: The `source $HOME/.local/bin/env` command activates the uv environment and should be run once per terminal session before running other uv commands.

### Testing

The project includes comprehensive tests for all components:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies
uv sync --extra dev

# Run all tests with coverage
PYTHONPATH=src pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
PYTHONPATH=src pytest tests/test_claude_processor.py -v

# Run tests with HTML coverage report
PYTHONPATH=src pytest tests/ --cov=src --cov-report=html

# Use the test runner script (recommended)
python test_runner.py
```

**Test Coverage**: The test suite covers:
- Claude API integration and query parsing
- ECB data server functionality and error handling
- Integration workflows from query to analysis
- Data parsing and validation
- Error scenarios and edge cases

### Linting and Code Quality

```bash
# Run code formatting and linting
ruff check src/ tests/
ruff format src/ tests/

# Run type checking
mypy src/
```

### Adding New Data Sources

The application uses the MCP (Model Context Protocol) for data source integration. To add a new data source:

1. Create a new MCP server class (following the pattern in `src/mcp_ecb_server.py`)
2. Update query parsing in `src/claude_processor.py` to handle new data types
3. Add visualization support in `src/app.py`
4. Update `.mcp.json` configuration to include the new server

**Current Example**: ECB data integration in `src/mcp_ecb_server.py`

## API References

- **ECB Statistical Data Warehouse**: https://data.ecb.europa.eu/
- **ECB API Documentation**: https://data-api.ecb.europa.eu/help/
- **Anthropic Claude API**: https://docs.anthropic.com/

## Security

- Never commit API keys to the repository
- Use environment variables for sensitive configuration
- The ECB API is public and requires no authentication
- All data processing focuses on defensive security practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and research purposes. Please respect the terms of service for both ECB and Anthropic APIs.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the ECB API documentation for data-related questions
- Refer to Anthropic's documentation for Claude API issues

---

**Powered by**: ECB Statistical Data Warehouse + Claude AI