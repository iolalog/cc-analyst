"""Integration tests for the complete workflow."""

from unittest.mock import Mock, patch


class TestIntegration:
    """Integration tests for the complete analytics workflow."""

    @patch("claude_processor.Anthropic")
    @patch("mcp_ecb_server.requests.Session")
    def test_complete_workflow_success(
        self, mock_session_class, mock_anthropic, mock_env_vars
    ):
        """Test complete workflow from query to visualization."""
        # Setup ECB server mock
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

        # Setup Claude processor mock
        mock_client = Mock()

        # Mock parse_user_query response
        parse_response = Mock()
        parse_response.content = [
            Mock(
                text='{"dataset_type": "interest_rates", "specific_rates": ["MRR"], "time_period": "1Y", "analysis_type": "trend"}'
            )
        ]

        # Mock analyze_data_results response
        analyze_response = Mock()
        analyze_response.content = [
            Mock(
                text="The ECB Main Refinancing Rate shows a steady upward trend from 2.50% to 3.00% over the analyzed period, indicating a tightening monetary policy stance."
            )
        ]

        mock_client.messages.create.side_effect = [parse_response, analyze_response]
        mock_anthropic.return_value = mock_client

        # Import modules after mocking
        from claude_processor import ClaudeQueryProcessor
        from mcp_ecb_server import ECBDataServer

        # Execute complete workflow
        claude_processor = ClaudeQueryProcessor()
        ecb_server = ECBDataServer()

        # Step 1: Parse user query
        user_query = "Show me ECB main refinancing rate trends for the last year"
        parsed_result = claude_processor.parse_user_query(user_query)

        assert parsed_result["success"] is True
        assert parsed_result["parsed_query"]["dataset_type"] == "interest_rates"

        # Step 2: Fetch ECB data
        ecb_result = ecb_server.get_interest_rates(
            rate_types=parsed_result["parsed_query"]["specific_rates"]
        )

        assert ecb_result["success"] is True
        assert "MRR" in ecb_result["data"]
        assert len(ecb_result["data"]["MRR"]["observations"]) == 3

        # Step 3: Analyze data
        analysis_result = claude_processor.analyze_data_results(
            ecb_result["data"], user_query
        )

        assert analysis_result["success"] is True
        assert "upward trend" in analysis_result["analysis"]
        assert "2.50%" in analysis_result["analysis"]
        assert "3.00%" in analysis_result["analysis"]

    @patch("claude_processor.Anthropic")
    @patch("mcp_ecb_server.requests.Session")
    def test_workflow_with_parsing_failure(
        self, mock_session_class, mock_anthropic, mock_env_vars
    ):
        """Test workflow when query parsing fails."""
        # Setup Claude processor mock to fail
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        from claude_processor import ClaudeQueryProcessor

        claude_processor = ClaudeQueryProcessor()

        # Parse user query should fail
        user_query = "Show me ECB interest rates"
        parsed_result = claude_processor.parse_user_query(user_query)

        assert parsed_result["success"] is False
        assert "API Error" in parsed_result["error"]

    @patch("claude_processor.Anthropic")
    @patch("mcp_ecb_server.requests.Session")
    def test_workflow_with_data_fetch_failure(
        self, mock_session_class, mock_anthropic, mock_env_vars
    ):
        """Test workflow when data fetching fails."""
        # Setup ECB server mock to fail
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network Error")
        mock_session_class.return_value = mock_session

        # Setup Claude processor mock to succeed
        mock_client = Mock()
        parse_response = Mock()
        parse_response.content = [
            Mock(
                text='{"dataset_type": "interest_rates", "specific_rates": ["MRR"], "time_period": "1Y"}'
            )
        ]
        mock_client.messages.create.return_value = parse_response
        mock_anthropic.return_value = mock_client

        from claude_processor import ClaudeQueryProcessor
        from mcp_ecb_server import ECBDataServer

        claude_processor = ClaudeQueryProcessor()
        ecb_server = ECBDataServer()

        # Parse should succeed
        parsed_result = claude_processor.parse_user_query("Show me ECB interest rates")
        assert parsed_result["success"] is True

        # Fetch should fail
        ecb_result = ecb_server.get_interest_rates(rate_types=["MRR"])
        assert ecb_result["success"] is False
        assert "Network Error" in ecb_result["error"]

    @patch("claude_processor.Anthropic")
    @patch("mcp_ecb_server.requests.Session")
    def test_workflow_with_analysis_failure(
        self, mock_session_class, mock_anthropic, mock_env_vars
    ):
        """Test workflow when analysis fails."""
        # Setup ECB server mock to succeed
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dataSets": [
                {"series": {"0:0:0:0:0:0:0": {"observations": {"0": [2.50]}}}}
            ],
            "structure": {
                "dimensions": {"observation": [{"values": [{"id": "2023-01-01"}]}]}
            },
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Setup Claude processor mock - parse succeeds, analyze fails
        mock_client = Mock()
        parse_response = Mock()
        parse_response.content = [
            Mock(
                text='{"dataset_type": "interest_rates", "specific_rates": ["MRR"], "time_period": "1Y"}'
            )
        ]

        mock_client.messages.create.side_effect = [
            parse_response,
            Exception("Analysis API Error"),
        ]
        mock_anthropic.return_value = mock_client

        from claude_processor import ClaudeQueryProcessor
        from mcp_ecb_server import ECBDataServer

        claude_processor = ClaudeQueryProcessor()
        ecb_server = ECBDataServer()

        # Parse should succeed
        parsed_result = claude_processor.parse_user_query("Show me ECB interest rates")
        assert parsed_result["success"] is True

        # Fetch should succeed
        ecb_result = ecb_server.get_interest_rates(rate_types=["MRR"])
        assert ecb_result["success"] is True

        # Analysis should fail
        analysis_result = claude_processor.analyze_data_results(
            ecb_result["data"], "Show me ECB interest rates"
        )
        assert analysis_result["success"] is False
        assert "Analysis API Error" in analysis_result["error"]

    @patch("claude_processor.Anthropic")
    @patch("mcp_ecb_server.requests.Session")
    def test_multiple_rate_types_workflow(
        self, mock_session_class, mock_anthropic, mock_env_vars
    ):
        """Test workflow with multiple rate types."""
        # Setup ECB server mock for multiple rate types
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dataSets": [
                {
                    "series": {
                        "0:0:0:0:0:0:0": {"observations": {"0": [2.50], "1": [2.75]}}
                    }
                }
            ],
            "structure": {
                "dimensions": {
                    "observation": [
                        {"values": [{"id": "2023-01-01"}, {"id": "2023-02-01"}]}
                    ]
                }
            },
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Setup Claude processor mock
        mock_client = Mock()
        parse_response = Mock()
        parse_response.content = [
            Mock(
                text='{"dataset_type": "interest_rates", "specific_rates": ["MRR", "DFR", "MLF"], "time_period": "1Y", "analysis_type": "comparison"}'
            )
        ]

        analyze_response = Mock()
        analyze_response.content = [
            Mock(
                text="The ECB rates show different levels with MRR being the highest, followed by DFR and MLF."
            )
        ]

        mock_client.messages.create.side_effect = [parse_response, analyze_response]
        mock_anthropic.return_value = mock_client

        from claude_processor import ClaudeQueryProcessor
        from mcp_ecb_server import ECBDataServer

        claude_processor = ClaudeQueryProcessor()
        ecb_server = ECBDataServer()

        # Parse query for multiple rates
        parsed_result = claude_processor.parse_user_query(
            "Compare all ECB interest rates"
        )
        assert parsed_result["success"] is True
        assert len(parsed_result["parsed_query"]["specific_rates"]) == 3

        # Fetch data for multiple rates
        ecb_result = ecb_server.get_interest_rates(
            rate_types=parsed_result["parsed_query"]["specific_rates"]
        )

        assert ecb_result["success"] is True
        assert len(ecb_result["data"]) == 3  # MRR, DFR, MLF

        # Analyze comparative data
        analysis_result = claude_processor.analyze_data_results(
            ecb_result["data"], "Compare all ECB interest rates"
        )

        assert analysis_result["success"] is True
        assert "different levels" in analysis_result["analysis"]
