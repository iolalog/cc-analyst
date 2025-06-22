"""
Natural language query processor using Claude API
Converts user questions into ECB data queries and analyzes results
"""

import os
from typing import Dict, List, Optional, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv
import json

load_dotenv()

class ClaudeQueryProcessor:
    """Processes natural language queries using Claude API"""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def parse_user_query(self, user_question: str) -> Dict:
        """
        Parse user's natural language question into structured ECB data request
        
        Args:
            user_question: User's question about ECB data
            
        Returns:
            Dictionary with parsed query parameters
        """
        
        system_prompt = """You are an expert in European Central Bank (ECB) data analysis. 
        Your task is to parse user questions about ECB data and convert them into structured queries.
        
        Available ECB datasets include:
        - Key Interest Rates (MRR, DFR, MLF)
        - Money Market Rates
        - Government Bond Yields
        - Exchange Rates
        - Monetary Aggregates
        
        Return a JSON object with:
        {
          "dataset_type": "interest_rates|money_market|bonds|exchange_rates|monetary",
          "specific_rates": ["MRR", "DFR", "MLF"] (if applicable),
          "time_period": "1Y|2Y|5Y|10Y|custom",
          "start_date": "YYYY-MM-DD" (if specified),
          "end_date": "YYYY-MM-DD" (if specified),
          "analysis_type": "trend|comparison|current|historical",
          "countries": ["EU", "DE", "FR"] (if specified)
        }
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Parse this ECB data question: {user_question}"}
                ]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            # Find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end != -1:
                parsed_query = json.loads(content[start:end])
                return {
                    "success": True,
                    "parsed_query": parsed_query,
                    "original_query": user_question
                }
            else:
                return {
                    "success": False,
                    "error": "Could not parse JSON from Claude response",
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_query": user_question
            }
    
    def analyze_data_results(self, data: Dict, user_question: str) -> Dict:
        """
        Analyze ECB data results and provide natural language insights
        
        Args:
            data: ECB data results
            user_question: Original user question
            
        Returns:
            Dictionary with analysis and insights
        """
        
        system_prompt = """You are an expert ECB data analyst. Analyze the provided ECB data 
        and generate insights that answer the user's question in clear, accessible language.
        
        Focus on:
        - Key trends and patterns
        - Significant changes or events
        - Context for the current economic situation
        - Actionable insights
        
        Keep explanations concise but informative for a general audience.
        """
        
        try:
            data_str = json.dumps(data, indent=2)
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"""
                    User Question: {user_question}
                    
                    ECB Data:
                    {data_str}
                    
                    Please analyze this data and provide insights that answer the user's question.
                    """}
                ]
            )
            
            return {
                "success": True,
                "analysis": response.content[0].text,
                "user_question": user_question
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_question": user_question
            }
    
    def generate_visualization_suggestions(self, data: Dict, analysis: str) -> List[str]:
        """
        Generate suggestions for data visualization based on the data and analysis
        
        Args:
            data: ECB data results
            analysis: Analysis text from analyze_data_results
            
        Returns:
            List of visualization suggestions
        """
        
        system_prompt = """Based on the ECB data and analysis provided, suggest the most 
        appropriate chart types and visualizations. Consider:
        - Time series data -> line charts, area charts
        - Comparisons -> bar charts, grouped charts
        - Correlations -> scatter plots
        - Distributions -> histograms
        
        Return a simple list of specific chart suggestions."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"""
                    Data: {json.dumps(data, indent=2)}
                    Analysis: {analysis}
                    
                    What visualizations would best represent this data?
                    """}
                ]
            )
            
            suggestions = response.content[0].text.split('\n')
            return [s.strip('- ').strip() for s in suggestions if s.strip()]
            
        except Exception as e:
            return ["Line chart showing trends over time", "Bar chart for comparisons"]