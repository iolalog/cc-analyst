"""
Natural language query processor using Claude API
Converts user questions into ECB data queries and analyzes results
"""

import json
import os
import time
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

try:
    from .logger_config import log_api_call, setup_logger
except ImportError:
    from logger_config import log_api_call, setup_logger

load_dotenv()


class ClaudeQueryProcessor:
    """Processes natural language queries using Claude API"""

    def __init__(self) -> None:
        self.logger = setup_logger(__name__)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.logger.error("ANTHROPIC_API_KEY environment variable not found")
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.client = Anthropic(api_key=api_key)
        self.logger.info("ClaudeQueryProcessor initialized successfully")

    def parse_user_query(self, user_question: str) -> dict[str, Any]:
        """
        Parse user's natural language question into structured ECB data request

        Args:
            user_question: User's question about ECB data

        Returns:
            Dictionary with parsed query parameters
        """

        system_prompt = """You are an expert data analyst for multiple data sources. 
        Your task is to parse user questions about data and convert them into structured queries.
        
        Available data sources and datasets include:
        - ECB (European Central Bank): Interest Rates, Inflation Rates
        - Other sources can be added as plugins
        
        Return a JSON object with:
        {
          "data_source": "ecb|other_source_id",
          "dataset_type": "interest_rates|inflation_rates",
          "specific_rates": ["MRR", "DFR", "MLF"] (if applicable to ECB interest rates),
          "time_period": "1Y|2Y|3Y|5Y|10Y|custom",
          "start_date": "YYYY-MM-DD" (if specified),
          "end_date": "YYYY-MM-DD" (if specified),
          "analysis_type": "trend|comparison|current|historical",
          "countries": ["EU", "DE", "FR"] (if specified)
        }
        
        Important: For inflation-related queries, use "inflation_rates" as the dataset_type.
        
        If the user doesn't specify a data source, default to "ecb" for financial/economic data.
        """

        start_time = time.time()

        try:
            self.logger.info(f"Parsing user query: {user_question[:100]}...")

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Parse this data question: {user_question}",
                    }
                ],
            )

            duration = time.time() - start_time

            # Extract JSON from response
            content = response.content[0].text
            # Find JSON in the response
            start = content.find("{")
            end = content.rfind("}") + 1

            if start != -1 and end != -1:
                parsed_query = json.loads(content[start:end])

                log_api_call(self.logger, "claude", "parse_query", True, duration)
                self.logger.debug(f"Parsed query result: {parsed_query}")

                return {
                    "success": True,
                    "parsed_query": parsed_query,
                    "original_query": user_question,
                }
            else:
                error_msg = "Could not parse JSON from Claude response"
                log_api_call(
                    self.logger, "claude", "parse_query", False, duration, error_msg
                )

                return {"success": False, "error": error_msg, "raw_response": content}

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            log_api_call(
                self.logger, "claude", "parse_query", False, duration, error_msg
            )

            return {
                "success": False,
                "error": error_msg,
                "original_query": user_question,
            }

    def analyze_data_results(
        self, data: dict[str, Any], user_question: str
    ) -> dict[str, Any]:
        """
        Analyze ECB data results and provide natural language insights

        Args:
            data: ECB data results
            user_question: Original user question

        Returns:
            Dictionary with analysis and insights
        """

        system_prompt = """You are an expert data analyst. Analyze the provided data 
        and generate insights that answer the user's question in clear, accessible language.
        
        Focus on:
        - Key trends and patterns
        - Significant changes or events
        - Context for the current situation
        - Actionable insights
        - Data source context when relevant
        
        Keep explanations concise but informative for a general audience.
        """

        start_time = time.time()

        try:
            self.logger.info(f"Analyzing data for query: {user_question[:100]}...")

            data_str = json.dumps(data, indent=2)

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                    User Question: {user_question}
                    
                    Data:
                    {data_str}
                    
                    Please analyze this data and provide insights that answer the user's question.
                    """,
                    }
                ],
            )

            duration = time.time() - start_time
            analysis_text = response.content[0].text

            log_api_call(self.logger, "claude", "analyze_data", True, duration)
            self.logger.debug(f"Analysis generated: {len(analysis_text)} characters")

            return {
                "success": True,
                "analysis": analysis_text,
                "user_question": user_question,
            }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            log_api_call(
                self.logger, "claude", "analyze_data", False, duration, error_msg
            )

            return {
                "success": False,
                "error": error_msg,
                "user_question": user_question,
            }

    def generate_visualization_suggestions(
        self, data: dict[str, Any], analysis: str
    ) -> list[str]:
        """
        Generate suggestions for data visualization based on the data and analysis

        Args:
            data: ECB data results
            analysis: Analysis text from analyze_data_results

        Returns:
            List of visualization suggestions
        """

        system_prompt = """Based on the data and analysis provided, suggest the most 
        appropriate chart types and visualizations. Consider:
        - Time series data -> line charts, area charts
        - Comparisons -> bar charts, grouped charts
        - Correlations -> scatter plots
        - Distributions -> histograms
        - Geographic data -> maps, choropleth charts
        
        Return a simple list of specific chart suggestions."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                    Data: {json.dumps(data, indent=2)}
                    Analysis: {analysis}
                    
                    What visualizations would best represent this data?
                    """,
                    }
                ],
            )

            suggestions = response.content[0].text.split("\n")
            return [s.strip("- ").strip() for s in suggestions if s.strip()]

        except Exception:
            return ["Line chart showing trends over time", "Bar chart for comparisons"]
