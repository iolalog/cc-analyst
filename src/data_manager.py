"""
Generic data manager for handling multiple data sources.
This replaces the ECB-specific server with a plugin-based approach.
"""

from typing import Any

try:
    from .data_source_interface import DataSourceInterface, data_source_registry
    from .data_sources.ecb_data_source import ECBDataSource
    from .logger_config import log_data_query, setup_logger
except ImportError:
    from data_source_interface import DataSourceInterface, data_source_registry
    from data_sources.ecb_data_source import ECBDataSource
    from logger_config import log_data_query, setup_logger


class DataManager:
    """Manages multiple data sources and provides unified access."""

    def __init__(self) -> None:
        self.logger = setup_logger(__name__)
        self.registry = data_source_registry

        # Register available data sources
        self._register_default_sources()
        self.logger.info("DataManager initialized with available sources")

    def _register_default_sources(self) -> None:
        """Register default data sources."""
        try:
            # Register ECB data source
            ecb_source = ECBDataSource()
            self.registry.register_source("ecb", ecb_source)
            self.logger.info("Registered ECB data source")
        except Exception as e:
            self.logger.error(f"Failed to register ECB data source: {e}")

    def get_available_sources(self) -> dict[str, str]:
        """Get all available data sources."""
        return self.registry.list_sources()

    def get_source(self, source_id: str) -> DataSourceInterface | None:
        """Get a specific data source."""
        return self.registry.get_source(source_id)

    def get_all_datasets(self) -> dict[str, dict[str, str]]:
        """Get all datasets from all sources."""
        return self.registry.get_all_datasets()

    def query_data(
        self, source_id: str, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query data from a specific source.

        Args:
            source_id: ID of the data source
            dataset_type: Type of dataset to query
            parameters: Query parameters

        Returns:
            Dictionary with query results
        """
        self.logger.info(
            f"Query request: {source_id}.{dataset_type} with parameters {parameters}"
        )

        source = self.registry.get_source(source_id)
        if not source:
            error_msg = f"Data source '{source_id}' not found"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": f"Available sources: {list(self.get_available_sources().keys())}",
            }

        # Validate parameters before querying
        validation = source.validate_parameters(dataset_type, parameters)
        if not validation["valid"]:
            self.logger.warning(
                f"Parameter validation failed for {source_id}.{dataset_type}: {validation['errors']}"
            )
            return {
                "success": False,
                "error": "Parameter validation failed",
                "validation_errors": validation["errors"],
                "suggestions": validation["suggestions"],
                "message": "Please check your parameters and try again",
            }

        # Execute the query
        result = source.query_data(dataset_type, parameters)

        # Log the query result
        record_count = None
        if result.get("success") and "data" in result:
            # Try to count records for logging
            try:
                data = result["data"]
                if isinstance(data, dict):
                    record_count = sum(
                        len(item.get("observations", []))
                        for item in data.values()
                        if isinstance(item, dict)
                    )
            except Exception:
                pass  # Don't fail if we can't count records

        log_data_query(
            self.logger,
            source_id,
            dataset_type,
            parameters,
            result.get("success", False),
            record_count,
            result.get("error"),
        )

        return result

    def search_datasets(
        self, query: str, source_id: str | None = None
    ) -> dict[str, Any]:
        """
        Search for datasets across sources.

        Args:
            query: Search term
            source_id: Optional specific source to search (searches all if None)

        Returns:
            Dictionary with search results
        """
        if source_id:
            # Search specific source
            source = self.registry.get_source(source_id)
            if not source:
                return {
                    "success": False,
                    "error": f"Data source '{source_id}' not found",
                }
            return source.search_datasets(query)

        else:
            # Search all sources
            all_results = {}
            for sid, source in self.registry._sources.items():
                result = source.search_datasets(query)
                if result.get("success"):
                    all_results[sid] = result.get("datasets", {})

            return {
                "success": True,
                "results_by_source": all_results,
                "message": f"Searched {len(self.registry._sources)} data sources for: {query}",
            }

    def get_source_info(self, source_id: str) -> dict[str, Any]:
        """
        Get detailed information about a data source.

        Args:
            source_id: ID of the data source

        Returns:
            Dictionary with source information
        """
        source = self.registry.get_source(source_id)
        if not source:
            return {"success": False, "error": f"Data source '{source_id}' not found"}

        return {
            "success": True,
            "source_id": source_id,
            "name": source.get_name(),
            "description": source.get_description(),
            "supported_datasets": source.get_supported_datasets(),
        }

    def validate_query(
        self, source_id: str, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate a query without executing it.

        Args:
            source_id: ID of the data source
            dataset_type: Type of dataset
            parameters: Query parameters

        Returns:
            Dictionary with validation results
        """
        source = self.registry.get_source(source_id)
        if not source:
            return {
                "valid": False,
                "errors": [f"Data source '{source_id}' not found"],
                "suggestions": [
                    f"Available sources: {list(self.get_available_sources().keys())}"
                ],
            }

        return source.validate_parameters(dataset_type, parameters)


# Backward compatibility: Keep the ECBDataServer interface
class ECBDataServer:
    """
    Backward compatibility wrapper for ECB data access.
    This maintains the old interface while using the new plugin system.
    """

    def __init__(self) -> None:
        self.data_manager = DataManager()

    def get_interest_rates(
        self,
        rate_types: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Fetch ECB interest rates (backward compatibility method)."""
        parameters = {}
        if rate_types:
            parameters["rate_types"] = rate_types
        if start_date:
            parameters["start_date"] = start_date
        if end_date:
            parameters["end_date"] = end_date

        return self.data_manager.query_data("ecb", "interest_rates", parameters)

    def search_datasets(self, query: str) -> dict[str, Any]:
        """Search ECB datasets (backward compatibility method)."""
        return self.data_manager.search_datasets(query, "ecb")
