"""
Abstract interface for data sources in the analytics assistant.
This defines the contract that all data source plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Any


class DataSourceInterface(ABC):
    """Abstract base class for data source implementations."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this data source."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return a description of this data source."""
        pass

    @abstractmethod
    def get_supported_datasets(self) -> dict[str, str]:
        """
        Return a dictionary mapping dataset IDs to their descriptions.

        Returns:
            Dictionary where keys are dataset IDs and values are descriptions
        """
        pass

    @abstractmethod
    def query_data(
        self, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query data from this source.

        Args:
            dataset_type: Type of dataset to query
            parameters: Query parameters (varies by data source)

        Returns:
            Dictionary with query results in standardized format:
            {
                "success": bool,
                "data": dict,  # Actual data results
                "message": str,  # Success/error message
                "error": str (optional)  # Error details if success=False
            }
        """
        pass

    @abstractmethod
    def search_datasets(self, query: str) -> dict[str, Any]:
        """
        Search for available datasets in this data source.

        Args:
            query: Search term

        Returns:
            Dictionary with search results
        """
        pass

    @abstractmethod
    def validate_parameters(
        self, dataset_type: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate parameters for a given dataset type.

        Args:
            dataset_type: Type of dataset
            parameters: Parameters to validate

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": List[str],  # List of validation errors
                "suggestions": List[str]  # Suggestions for fixing errors
            }
        """
        pass


class DataSourceRegistry:
    """Registry for managing data source plugins."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSourceInterface] = {}

    def register_source(self, source_id: str, source: DataSourceInterface) -> None:
        """
        Register a data source.

        Args:
            source_id: Unique identifier for the source
            source: Data source implementation
        """
        self._sources[source_id] = source

    def get_source(self, source_id: str) -> DataSourceInterface | None:
        """
        Get a registered data source.

        Args:
            source_id: ID of the source to retrieve

        Returns:
            Data source implementation or None if not found
        """
        return self._sources.get(source_id)

    def list_sources(self) -> dict[str, str]:
        """
        List all registered data sources.

        Returns:
            Dictionary mapping source IDs to their names
        """
        return {
            source_id: source.get_name() for source_id, source in self._sources.items()
        }

    def get_all_datasets(self) -> dict[str, dict[str, str]]:
        """
        Get all datasets from all registered sources.

        Returns:
            Dictionary mapping source IDs to their datasets
        """
        return {
            source_id: source.get_supported_datasets()
            for source_id, source in self._sources.items()
        }


# Global registry instance
data_source_registry = DataSourceRegistry()
