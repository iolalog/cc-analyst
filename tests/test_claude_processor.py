"""Tests for claude_processor module."""

from unittest.mock import Mock, patch

import pytest

from claude_processor import ClaudeQueryProcessor


class TestClaudeQueryProcessor:
    """Test cases for ClaudeQueryProcessor."""

    def test_init_without_api_key(self, monkeypatch):
        """Test initialization fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(Exception):
            ClaudeQueryProcessor()

    def test_init_with_api_key(self, mock_env_vars):
        """Test successful initialization with API key."""
        processor = ClaudeQueryProcessor()
        assert processor.client is not None

    @patch("claude_processor.Anthropic")
    def test_parse_user_query_success(self, mock_anthropic, mock_env_vars):
        """Test successful query parsing."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='{"dataset_type": "interest_rates", "specific_rates": ["MRR"], "time_period": "1Y"}'
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        result = processor.parse_user_query(
            "Show me ECB interest rates for the last year"
        )

        assert result["success"] is True
        assert "parsed_query" in result
        assert result["parsed_query"]["dataset_type"] == "interest_rates"
        assert "MRR" in result["parsed_query"]["specific_rates"]

    @patch("claude_processor.Anthropic")
    def test_parse_user_query_invalid_json(self, mock_anthropic, mock_env_vars):
        """Test query parsing with invalid JSON response."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Invalid JSON response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        result = processor.parse_user_query("Show me ECB interest rates")

        assert result["success"] is False
        assert "error" in result

    @patch("claude_processor.Anthropic")
    def test_parse_user_query_api_error(self, mock_anthropic, mock_env_vars):
        """Test query parsing with API error."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        result = processor.parse_user_query("Show me ECB interest rates")

        assert result["success"] is False
        assert "API Error" in result["error"]

    @patch("claude_processor.Anthropic")
    def test_analyze_data_results_success(
        self, mock_anthropic, mock_env_vars, sample_ecb_data
    ):
        """Test successful data analysis."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(text="The ECB interest rates show an upward trend over the period.")
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        result = processor.analyze_data_results(
            sample_ecb_data, "Show me ECB interest rates"
        )

        assert result["success"] is True
        assert "analysis" in result
        assert "upward trend" in result["analysis"]

    @patch("claude_processor.Anthropic")
    def test_analyze_data_results_api_error(
        self, mock_anthropic, mock_env_vars, sample_ecb_data
    ):
        """Test data analysis with API error."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        result = processor.analyze_data_results(
            sample_ecb_data, "Show me ECB interest rates"
        )

        assert result["success"] is False
        assert "API Error" in result["error"]

    @patch("claude_processor.Anthropic")
    def test_generate_visualization_suggestions_success(
        self, mock_anthropic, mock_env_vars, sample_ecb_data
    ):
        """Test successful visualization suggestions."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="- Line chart showing trends over time\n- Bar chart for comparisons"
            )
        ]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        suggestions = processor.generate_visualization_suggestions(
            sample_ecb_data, "Analysis text"
        )

        assert len(suggestions) > 0
        assert any("line chart" in s.lower() for s in suggestions)

    @patch("claude_processor.Anthropic")
    def test_generate_visualization_suggestions_api_error(
        self, mock_anthropic, mock_env_vars, sample_ecb_data
    ):
        """Test visualization suggestions with API error."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        processor = ClaudeQueryProcessor()
        suggestions = processor.generate_visualization_suggestions(
            sample_ecb_data, "Analysis text"
        )

        # Should return default suggestions on error
        assert len(suggestions) == 2
        assert any("line chart" in s.lower() for s in suggestions)
