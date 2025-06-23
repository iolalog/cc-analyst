"""Pytest configuration and shared fixtures."""

import os
import sys
from unittest.mock import Mock

import pytest

# Add src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text='{"dataset_type": "interest_rates", "specific_rates": ["MRR"], "time_period": "1Y", "analysis_type": "trend"}'
        )
    ]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_ecb_data():
    """Sample ECB data for testing."""
    return {
        "MRR": {
            "observations": [
                {"date": "2023-01-01", "value": 2.50},
                {"date": "2023-02-01", "value": 2.75},
                {"date": "2023-03-01", "value": 3.00},
            ],
            "count": 3,
        }
    }


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing."""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "dataSets": [
            {
                "series": {
                    "0:0:0:0:0:0:0": {
                        "observations": {"0": [2.50], "1": [2.75], "2": [3.00]}
                    }
                }
            }
        ],
        "structure": {
            "dimensions": {
                "observation": [
                    {
                        "values": [
                            {"id": "2023-01-01"},
                            {"id": "2023-02-01"},
                            {"id": "2023-03-01"},
                        ]
                    }
                ]
            }
        },
    }
    mock_session.get.return_value = mock_response
    return mock_session


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("ECB_API_BASE_URL", "https://data-api.ecb.europa.eu")
