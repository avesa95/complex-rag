from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient


@dataclass
class RetrievalConfig:
    qdrant_host: str
    qdrant_api_key: str
    timeout: int = 30


class RetrieverStrategy(ABC):
    @abstractmethod
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        pass


class FilterStrategy(ABC):
    @abstractmethod
    def apply(self, nodes: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        pass


class BaseQdrantRetriever(ABC):
    def __init__(self, config: RetrievalConfig):
        """Initialize base retriever with Qdrant configuration."""
        self.config = config
        self.client = QdrantClient(
            url=self.config.qdrant_host,
            api_key=self.config.qdrant_api_key,
            timeout=self.config.timeout,
        )

    @abstractmethod
    def retrieve(
        self,
        query: str,
        limit: int = 10,
        prefetch_limit: Optional[int] = None,
        score_threshold: Optional[int] = 10,
    ) -> List[Dict[str, Any]]:
        """Abstract method for retrieval implementation."""
        pass

    def _format_results(self, results) -> List[Dict[str, Any]]:
        """Format Qdrant results into standard format."""
        return [
            {
                "score": point.score,
                "payload": point.payload,
                "id": point.id,
            }
            for point in results.points
        ]
