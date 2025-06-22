#!/usr/bin/env python3
"""
MCP Server for ECB Statistical Data Warehouse API
Provides tools for fetching ECB economic data
"""

import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

class ECBDataServer:
    """MCP Server for ECB data access"""
    
    BASE_URL = "https://data-api.ecb.europa.eu/service/data"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.sdmx.data+json',
            'User-Agent': 'cc-analyst/1.0'
        })
    
    def get_interest_rates(self, rate_types: List[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Fetch ECB key interest rates
        
        Args:
            rate_types: List of rate types ['MRR', 'DFR', 'MLF'] 
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with interest rate data
        """
        try:
            # Default to all key rates if none specified
            if not rate_types:
                rate_types = ['MRR', 'DFR', 'MLF']
            
            results = {}
            
            # ECB Key Interest Rates mappings
            rate_mappings = {
                'MRR': 'FM/B.U2.EUR.4F.KR.MRR_FR.LEV',  # Main Refinancing Rate
                'DFR': 'FM/B.U2.EUR.4F.KR.DFR.LEV',     # Deposit Facility Rate  
                'MLF': 'FM/B.U2.EUR.4F.KR.MLFR_FR.LEV'  # Marginal Lending Facility Rate
            }
            
            for rate_type in rate_types:
                if rate_type in rate_mappings:
                    dataset_id = rate_mappings[rate_type]
                    
                    params = {'format': 'jsondata'}
                    if start_date:
                        params['startPeriod'] = start_date
                    if end_date:
                        params['endPeriod'] = end_date
                    
                    url = f"{self.BASE_URL}/{dataset_id}"
                    response = self.session.get(url, params=params)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            results[rate_type] = self._parse_ecb_json_data(data)
                        except json.JSONDecodeError:
                            # Try CSV format if JSON fails
                            params['format'] = 'csvdata'
                            response = self.session.get(url, params=params)
                            if response.status_code == 200:
                                results[rate_type] = self._parse_ecb_csv_data(response.text)
                    else:
                        results[rate_type] = {
                            "error": f"Failed to fetch {rate_type}: HTTP {response.status_code}"
                        }
            
            return {
                "success": True,
                "data": results,
                "message": f"Successfully fetched ECB rates: {', '.join(rate_types)}"
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to fetch ECB data"
            }
    
    def _parse_ecb_json_data(self, json_data: Dict) -> Dict:
        """Parse ECB JSON response into structured data"""
        try:
            if 'dataSets' in json_data and json_data['dataSets']:
                dataset = json_data['dataSets'][0]
                observations = dataset.get('series', {}).get('0:0:0:0:0:0:0', {}).get('observations', {})
                
                # Extract time periods and values
                time_periods = json_data['structure']['dimensions']['observation'][0]['values']
                
                data_points = []
                for idx, obs in observations.items():
                    time_period = time_periods[int(idx)]
                    value = obs[0] if obs and obs[0] is not None else None
                    data_points.append({
                        'date': time_period['id'],
                        'value': value
                    })
                
                return {
                    'observations': data_points,
                    'count': len(data_points)
                }
            else:
                return {'observations': [], 'count': 0}
                
        except Exception as e:
            return {'error': f'Failed to parse JSON data: {str(e)}'}
    
    def _parse_ecb_csv_data(self, csv_text: str) -> Dict:
        """Parse ECB CSV response into structured data"""
        try:
            lines = csv_text.strip().split('\n')
            if len(lines) < 2:
                return {'observations': [], 'count': 0}
            
            # Skip header line
            data_points = []
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 2:
                    date = parts[0].strip('"')
                    try:
                        value = float(parts[1]) if parts[1] and parts[1] != '.' else None
                    except ValueError:
                        value = None
                    
                    data_points.append({
                        'date': date,
                        'value': value
                    })
            
            return {
                'observations': data_points,
                'count': len(data_points)
            }
            
        except Exception as e:
            return {'error': f'Failed to parse CSV data: {str(e)}'}
    
    def search_datasets(self, query: str) -> Dict:
        """
        Search for available ECB datasets
        
        Args:
            query: Search term for datasets
            
        Returns:
            Dictionary with search results
        """
        # This would implement dataset search functionality
        # For now, return common interest rate datasets
        common_datasets = {
            "FM": "Financial Markets - Interest Rates",
            "IRS": "ECB Interest Rate Statistics", 
            "RTD": "Real Time Database",
            "BSI": "Balance Sheet Items"
        }
        
        return {
            "success": True,
            "datasets": common_datasets,
            "message": f"Found datasets related to: {query}"
        }

def main():
    """Main MCP server entry point"""
    server = ECBDataServer()
    
    # Example usage - this would be replaced with proper MCP protocol handling
    print("ECB MCP Server initialized")
    print("Available tools:")
    print("- get_interest_rates")
    print("- search_datasets")

if __name__ == "__main__":
    main()