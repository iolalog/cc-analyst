"""
ECB (European Central Bank) data source implementation.
This is a plugin that implements the DataSourceInterface for ECB data.
"""

import json
import time
from datetime import datetime
from typing import Any

import requests

try:
    from ..data_source_interface import DataSourceInterface
    from ..logger_config import log_api_call, setup_logger
except ImportError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data_source_interface import DataSourceInterface
    from logger_config import log_api_call, setup_logger


class ECBDataSource(DataSourceInterface):
    """ECB data source implementation using their Statistical Data Warehouse API."""

    BASE_URL: str = "https://data-api.ecb.europa.eu/service/data"

    def __init__(self) -> None:
        self.logger = setup_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.sdmx.data+json",
                "User-Agent": "analytics-assistant/1.0",
            }
        )

        # ECB dataset mappings
        self._rate_mappings: dict[str, str] = {
            "MRR": "FM/B.U2.EUR.4F.KR.MRR_FR.LEV",  # Main Refinancing Rate
            "DFR": "FM/B.U2.EUR.4F.KR.DFR.LEV",  # Deposit Facility Rate
            "MLF": "FM/B.U2.EUR.4F.KR.MLFR_FR.LEV",  # Marginal Lending Facility Rate
        }
        
        # ECB inflation dataset mappings
        self._inflation_mappings: dict[str, str] = {
            "HICP": "ICP/M.U2.N.000000.4.ANR",  # Harmonised Index of Consumer Prices - Total
            "CORE": "ICP/M.U2.N.XEF000.4.ANR",  # Core inflation (excluding energy, food)
        }

        self.logger.info("ECB data source initialized")

    def get_name(self) -> str:
        """Return the name of this data source."""
        return "European Central Bank Statistical Data Warehouse"

    def get_description(self) -> str:
        """Return a description of this data source."""
        return "Official statistical data from the European Central Bank, including interest rates, monetary policy indicators, and economic statistics."

    def get_supported_datasets(self) -> dict[str, str]:
        """Return supported ECB datasets."""
        return {
            "interest_rates": "ECB Key Interest Rates (MRR, DFR, MLF)",
            "inflation_rates": "Harmonised Index of Consumer Prices (HICP)",
            "money_market": "Money Market Rates",
            "government_bonds": "Government Bond Yields",
            "exchange_rates": "Euro Exchange Rates",
            "monetary_aggregates": "Monetary Aggregates",
        }

    def query_data(
        self, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query ECB data based on dataset type and parameters.

        Args:
            dataset_type: Type of dataset ('interest_rates', 'money_market', etc.)
            parameters: Query parameters including:
                - rate_types: List of rate types for interest_rates
                - start_date: Start date in YYYY-MM-DD format
                - end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with ECB data results
        """
        try:
            self.logger.info(
                f"Querying ECB {dataset_type} with parameters: {parameters}"
            )

            if dataset_type == "interest_rates":
                return self._get_interest_rates(parameters)
            elif dataset_type == "inflation_rates":
                return self._get_inflation_rates(parameters)
            else:
                error_msg = f"Dataset type '{dataset_type}' not yet implemented"
                self.logger.warning(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "Only interest_rates and inflation_rates datasets are currently supported",
                }

        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                f"Failed to query ECB data for {dataset_type}: {error_msg}"
            )
            return {
                "success": False,
                "error": error_msg,
                "message": f"Failed to query ECB data for {dataset_type}",
            }

    def _get_interest_rates(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Fetch ECB interest rates data."""
        rate_types = parameters.get("rate_types", ["MRR", "DFR", "MLF"])
        start_date = parameters.get("start_date")
        end_date = parameters.get("end_date")

        results: dict[str, Any] = {}

        for rate_type in rate_types:
            if rate_type in self._rate_mappings:
                dataset_id = self._rate_mappings[rate_type]

                params = {"format": "jsondata"}
                if start_date:
                    params["startPeriod"] = start_date
                if end_date:
                    params["endPeriod"] = end_date

                url = f"{self.BASE_URL}/{dataset_id}"

                start_time = time.time()
                self.logger.debug(
                    f"Fetching {rate_type} from {url} with params {params}"
                )

                try:
                    response = self.session.get(url, params=params)
                    duration = time.time() - start_time

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            results[rate_type] = self._parse_ecb_json_data(data)
                            log_api_call(
                                self.logger, "ecb", f"fetch_{rate_type}", True, duration
                            )
                        except json.JSONDecodeError:
                            # Try CSV format if JSON fails
                            self.logger.warning(
                                f"JSON decode failed for {rate_type}, trying CSV format"
                            )
                            params["format"] = "csvdata"
                            response = self.session.get(url, params=params)
                            if response.status_code == 200:
                                results[rate_type] = self._parse_ecb_csv_data(
                                    response.text
                                )
                                log_api_call(
                                    self.logger,
                                    "ecb",
                                    f"fetch_{rate_type}_csv",
                                    True,
                                    duration,
                                )
                            else:
                                error_msg = (
                                    f"CSV fetch failed: HTTP {response.status_code}"
                                )
                                results[rate_type] = {"error": error_msg}
                                log_api_call(
                                    self.logger,
                                    "ecb",
                                    f"fetch_{rate_type}_csv",
                                    False,
                                    duration,
                                    error_msg,
                                )
                    else:
                        error_msg = (
                            f"Failed to fetch {rate_type}: HTTP {response.status_code}"
                        )
                        results[rate_type] = {"error": error_msg}
                        log_api_call(
                            self.logger,
                            "ecb",
                            f"fetch_{rate_type}",
                            False,
                            duration,
                            error_msg,
                        )

                except Exception as e:
                    duration = time.time() - start_time
                    error_msg = f"Request failed for {rate_type}: {str(e)}"
                    results[rate_type] = {"error": error_msg}
                    log_api_call(
                        self.logger,
                        "ecb",
                        f"fetch_{rate_type}",
                        False,
                        duration,
                        error_msg,
                    )

        return {
            "success": True,
            "data": results,
            "message": f"Successfully fetched ECB rates: {', '.join(rate_types)}",
        }

    def _get_inflation_rates(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Fetch ECB inflation data."""
        inflation_types = parameters.get("inflation_types", ["HICP"])
        start_date = parameters.get("start_date")
        end_date = parameters.get("end_date")

        results: dict[str, Any] = {}

        for inflation_type in inflation_types:
            if inflation_type in self._inflation_mappings:
                dataset_id = self._inflation_mappings[inflation_type]

                params = {"format": "jsondata"}
                if start_date:
                    params["startPeriod"] = start_date
                if end_date:
                    params["endPeriod"] = end_date

                url = f"{self.BASE_URL}/{dataset_id}"

                start_time = time.time()
                self.logger.debug(
                    f"Fetching {inflation_type} from {url} with params {params}"
                )

                try:
                    response = self.session.get(url, params=params)
                    duration = time.time() - start_time

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            results[inflation_type] = self._parse_ecb_json_data(data)
                            log_api_call(
                                self.logger, "ecb", f"fetch_{inflation_type}", True, duration
                            )
                        except json.JSONDecodeError:
                            # Try CSV format if JSON fails
                            self.logger.warning(
                                f"JSON decode failed for {inflation_type}, trying CSV format"
                            )
                            params["format"] = "csvdata"
                            response = self.session.get(url, params=params)
                            if response.status_code == 200:
                                results[inflation_type] = self._parse_ecb_csv_data(
                                    response.text
                                )
                                log_api_call(
                                    self.logger,
                                    "ecb",
                                    f"fetch_{inflation_type}_csv",
                                    True,
                                    duration,
                                )
                            else:
                                error_msg = (
                                    f"CSV fetch failed: HTTP {response.status_code}"
                                )
                                results[inflation_type] = {"error": error_msg}
                                log_api_call(
                                    self.logger,
                                    "ecb",
                                    f"fetch_{inflation_type}_csv",
                                    False,
                                    duration,
                                    error_msg,
                                )
                    else:
                        error_msg = (
                            f"Failed to fetch {inflation_type}: HTTP {response.status_code}"
                        )
                        results[inflation_type] = {"error": error_msg}
                        log_api_call(
                            self.logger,
                            "ecb",
                            f"fetch_{inflation_type}",
                            False,
                            duration,
                            error_msg,
                        )

                except Exception as e:
                    duration = time.time() - start_time
                    error_msg = f"Request failed for {inflation_type}: {str(e)}"
                    results[inflation_type] = {"error": error_msg}
                    log_api_call(
                        self.logger,
                        "ecb",
                        f"fetch_{inflation_type}",
                        False,
                        duration,
                        error_msg,
                    )

        return {
            "success": True,
            "data": results,
            "message": f"Successfully fetched ECB inflation data: {', '.join(inflation_types)}",
        }

    def _parse_ecb_json_data(self, json_data: dict[str, Any]) -> dict[str, Any]:
        """Parse ECB JSON response into structured data."""
        try:
            if "dataSets" in json_data and json_data["dataSets"]:
                dataset = json_data["dataSets"][0]
                series_data = dataset.get("series", {})
                
                # Find the first (and usually only) series key
                observations = {}
                if series_data:
                    first_series_key = next(iter(series_data.keys()))
                    observations = series_data[first_series_key].get("observations", {})

                # Extract time periods and values
                time_periods = json_data["structure"]["dimensions"]["observation"][0][
                    "values"
                ]

                data_points = []
                for idx, obs in observations.items():
                    time_period = time_periods[int(idx)]
                    value = obs[0] if obs and obs[0] is not None else None
                    data_points.append({"date": time_period["id"], "value": value})

                return {"observations": data_points, "count": len(data_points)}
            else:
                return {"observations": [], "count": 0}

        except Exception as e:
            return {"error": f"Failed to parse JSON data: {str(e)}"}

    def _parse_ecb_csv_data(self, csv_text: str) -> dict[str, Any]:
        """Parse ECB CSV response into structured data."""
        try:
            lines = csv_text.strip().split("\n")
            if len(lines) < 2:
                return {"observations": [], "count": 0}

            # Skip header line
            data_points = []
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) >= 2:
                    date = parts[0].strip('"')
                    try:
                        value = (
                            float(parts[1]) if parts[1] and parts[1] != "." else None
                        )
                    except ValueError:
                        value = None

                    data_points.append({"date": date, "value": value})

            return {"observations": data_points, "count": len(data_points)}

        except Exception as e:
            return {"error": f"Failed to parse CSV data: {str(e)}"}

    def search_datasets(self, query: str) -> dict[str, Any]:
        """Search for ECB datasets."""
        # Simple search implementation
        all_datasets = self.get_supported_datasets()
        query_lower = query.lower()

        matching_datasets = {
            dataset_id: description
            for dataset_id, description in all_datasets.items()
            if query_lower in dataset_id.lower() or query_lower in description.lower()
        }

        return {
            "success": True,
            "datasets": matching_datasets,
            "message": f"Found {len(matching_datasets)} ECB datasets matching: {query}",
        }

    def validate_parameters(
        self, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate parameters for ECB datasets."""
        errors = []
        suggestions = []

        if dataset_type == "interest_rates":
            rate_types = parameters.get("rate_types", [])
            if rate_types:
                invalid_rates = [
                    rate for rate in rate_types if rate not in self._rate_mappings
                ]
                if invalid_rates:
                    errors.append(f"Invalid rate types: {invalid_rates}")
                    suggestions.append(
                        f"Valid rate types are: {list(self._rate_mappings.keys())}"
                    )

        elif dataset_type == "inflation_rates":
            inflation_types = parameters.get("inflation_types", [])
            if inflation_types:
                invalid_inflation = [
                    rate for rate in inflation_types if rate not in self._inflation_mappings
                ]
                if invalid_inflation:
                    errors.append(f"Invalid inflation types: {invalid_inflation}")
                    suggestions.append(
                        f"Valid inflation types are: {list(self._inflation_mappings.keys())}"
                    )

        else:
            errors.append(f"Dataset type '{dataset_type}' not supported")
            suggestions.append(
                f"Supported datasets: {list(self.get_supported_datasets().keys())}"
            )

        # Validate date format for all dataset types
        for date_param in ["start_date", "end_date"]:
            if date_param in parameters and parameters[date_param] is not None:
                try:
                    datetime.strptime(parameters[date_param], "%Y-%m-%d")
                except ValueError:
                    errors.append(
                        f"Invalid {date_param} format: {parameters[date_param]}"
                    )
                    suggestions.append(
                        f"{date_param} should be in YYYY-MM-DD format"
                    )

        return {"valid": len(errors) == 0, "errors": errors, "suggestions": suggestions}
