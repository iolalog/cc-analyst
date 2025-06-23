"""Tests for mcp_ecb_server module."""

import json
from unittest.mock import Mock, patch

from mcp_ecb_server import ECBDataServer


class TestECBDataServer:
    """Test cases for ECBDataServer."""

    def test_init(self):
        """Test ECBDataServer initialization."""
        server = ECBDataServer()
        assert server.BASE_URL == "https://data-api.ecb.europa.eu/service/data"
        assert server.session is not None

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_success(self, mock_session_class):
        """Test successful interest rates retrieval."""
        # Setup mock
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
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates(rate_types=["MRR"])

        assert result["success"] is True
        assert "MRR" in result["data"]
        assert len(result["data"]["MRR"]["observations"]) == 3
        assert result["data"]["MRR"]["observations"][0]["value"] == 2.50

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_default_types(self, mock_session_class):
        """Test interest rates retrieval with default rate types."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dataSets": [{"series": {"0:0:0:0:0:0:0": {"observations": {}}}}],
            "structure": {"dimensions": {"observation": [{"values": []}]}},
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates()  # No rate_types specified

        assert result["success"] is True
        # Should fetch all three default rate types
        assert len(result["data"]) == 3
        assert "MRR" in result["data"]
        assert "DFR" in result["data"]
        assert "MLF" in result["data"]

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_with_date_range(self, mock_session_class):
        """Test interest rates retrieval with date range."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dataSets": [{"series": {"0:0:0:0:0:0:0": {"observations": {}}}}],
            "structure": {"dimensions": {"observation": [{"values": []}]}},
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates(
            rate_types=["MRR"], start_date="2023-01-01", end_date="2023-12-31"
        )

        assert result["success"] is True
        # Verify date parameters were passed to the API call
        call_args = mock_session.get.call_args
        assert "startPeriod" in call_args[1]["params"]
        assert "endPeriod" in call_args[1]["params"]

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_http_error(self, mock_session_class):
        """Test interest rates retrieval with HTTP error."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates(rate_types=["MRR"])

        assert result["success"] is True  # Function still succeeds
        assert "MRR" in result["data"]
        assert "error" in result["data"]["MRR"]
        assert "HTTP 404" in result["data"]["MRR"]["error"]

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_json_fallback_to_csv(self, mock_session_class):
        """Test fallback to CSV when JSON fails."""
        # Setup mock
        mock_session = Mock()

        # First call (JSON) returns invalid JSON
        json_response = Mock()
        json_response.status_code = 200
        json_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        # Second call (CSV) returns valid CSV
        csv_response = Mock()
        csv_response.status_code = 200
        csv_response.text = '"Date","Value"\n"2023-01-01",2.50\n"2023-02-01",2.75'

        mock_session.get.side_effect = [json_response, csv_response]
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates(rate_types=["MRR"])

        assert result["success"] is True
        assert "MRR" in result["data"]
        assert len(result["data"]["MRR"]["observations"]) == 2

    @patch("mcp_ecb_server.requests.Session")
    def test_get_interest_rates_exception(self, mock_session_class):
        """Test interest rates retrieval with exception."""
        # Setup mock
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session_class.return_value = mock_session

        server = ECBDataServer()
        result = server.get_interest_rates(rate_types=["MRR"])

        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_parse_ecb_json_data_success(self):
        """Test successful JSON data parsing."""
        server = ECBDataServer()
        json_data = {
            "dataSets": [
                {
                    "series": {
                        "0:0:0:0:0:0:0": {
                            "observations": {"0": [2.50], "1": [2.75], "2": [None]}
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

        result = server._parse_ecb_json_data(json_data)

        assert result["count"] == 3
        assert len(result["observations"]) == 3
        assert result["observations"][0]["value"] == 2.50
        assert result["observations"][2]["value"] is None

    def test_parse_ecb_json_data_empty(self):
        """Test JSON data parsing with empty data."""
        server = ECBDataServer()
        json_data = {"dataSets": []}

        result = server._parse_ecb_json_data(json_data)

        assert result["count"] == 0
        assert result["observations"] == []

    def test_parse_ecb_json_data_malformed(self):
        """Test JSON data parsing with malformed data."""
        server = ECBDataServer()
        json_data = {"invalid": "structure"}

        result = server._parse_ecb_json_data(json_data)

        assert "error" in result

    def test_parse_ecb_csv_data_success(self):
        """Test successful CSV data parsing."""
        server = ECBDataServer()
        csv_text = (
            '"Date","Value"\n"2023-01-01",2.50\n"2023-02-01",2.75\n"2023-03-01",.'
        )

        result = server._parse_ecb_csv_data(csv_text)

        assert result["count"] == 3
        assert len(result["observations"]) == 3
        assert result["observations"][0]["value"] == 2.50
        assert result["observations"][2]["value"] is None  # '.' becomes None

    def test_parse_ecb_csv_data_empty(self):
        """Test CSV data parsing with empty data."""
        server = ECBDataServer()
        csv_text = '"Date","Value"'

        result = server._parse_ecb_csv_data(csv_text)

        assert result["count"] == 0
        assert result["observations"] == []

    def test_parse_ecb_csv_data_malformed(self):
        """Test CSV data parsing with malformed data."""
        server = ECBDataServer()
        csv_text = "invalid\ndata"  # Header with only one column, insufficient

        result = server._parse_ecb_csv_data(csv_text)

        assert "error" in result

    def test_search_datasets(self):
        """Test dataset search functionality."""
        server = ECBDataServer()
        result = server.search_datasets("interest rates")

        assert result["success"] is True
        assert "datasets" in result
        assert len(result["datasets"]) > 0
        assert "FM" in result["datasets"]
