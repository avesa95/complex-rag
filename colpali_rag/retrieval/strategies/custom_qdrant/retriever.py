# qdrant_retriever.py
from typing import Any, Dict, List, Optional

from openai import OpenAI

from colpali_rag.retrieval.strategies.base import (
    RetrievalConfig,
    RetrieverStrategy,
)
from colpali_rag.retrieval.types import SearchType


class QdrantRetrieverStrategy(RetrieverStrategy):
    """
    A unified Qdrant retriever that delegates to specialized retrievers based on search type.
    Uses factory pattern to create appropriate retrievers on demand.
    """

    def __init__(
        self,
        config: RetrievalConfig,
        openai_client: Optional[OpenAI] = None,
        dense_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        sparse_model_name: str = "Qdrant/bm42-all-minilm-l6-v2-attentions",
        colbert_model_name: str = "colbert-ir/colbertv2.0",
    ) -> None:
        """
        Initialize QdrantRetrieverStrategy with configuration and optional models.

        Args:
            config: QdrantConfig containing connection details
            openai_client: Optional OpenAI client for matrioska search
            dense_model_name: Name of the dense embedding model
            sparse_model_name: Name of the sparse embedding model
            colbert_model_name: Name of the ColBERT model
        """
        self.config = config
        self.openai_client = openai_client
        self.model_config = {
            "dense_model_name": dense_model_name,
            "sparse_model_name": sparse_model_name,
            "colbert_model_name": colbert_model_name,
        }

        # Initialize retrievers dict
        self._retrievers = {}

    def _get_retriever(self, search_type: SearchType):
        """
        Get or create a retriever for the specified search type.
        Uses lazy initialization to create retrievers only when needed.
        """
        if search_type not in self._retrievers:
            if search_type == SearchType.COLBERT:
                from colpali_rag.retrieval.strategies.custom_qdrant.search.colbert import (
                    ColbertRetriever,
                )

                self._retrievers[search_type] = ColbertRetriever(
                    config=self.config,
                    model_name=self.model_config["colbert_model_name"],
                )
            elif search_type == SearchType.HYBRID:
                from colpali_rag.retrieval.strategies.custom_qdrant.search.hybrid import (
                    HybridRetriever,
                )

                self._retrievers[search_type] = HybridRetriever(
                    config=self.config, **self.model_config
                )
            elif search_type == SearchType.MATRIOSKA:
                if not self.openai_client:
                    raise ValueError("OpenAI client required for matrioska search")
                from colpali_rag.retrieval.strategies.custom_qdrant.search.matrioska import (
                    MatrioskaRetriever,
                )

                self._retrievers[search_type] = MatrioskaRetriever(
                    config=self.config, openai_client=self.openai_client
                )
            elif search_type == SearchType.FUSION:
                if not self.openai_client:
                    raise ValueError("OpenAI client required for fusion search")
                from colpali_rag.retrieval.strategies.custom_qdrant.search.fusion import (
                    FusionybridRetriever,
                )

                self._retrievers[search_type] = FusionybridRetriever(
                    config=self.config, openai_client=self.openai_client
                )

            else:
                raise ValueError(f"Unknown search type: {search_type}")

        return self._retrievers[search_type]

    def retrieve(
        self,
        query: str,
        search_type: Optional[SearchType] = SearchType.HYBRID,
        limit: int = 10,
        prefetch_limit: int = 20,
        collection_name: str = None,
        score_threshold: Optional[int] = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using the specified search strategy.

        Args:
            query: The search query string
            search_type: Type of search to perform
            limit: Maximum number of results to return
            prefetch_limit: Maximum number of results to prefetch in hybrid searches

        Returns:
            List of dictionaries containing search results with scores and payloads

        Raises:
            ValueError: If an invalid search type is provided or if required client is missing
        """
        search_type = search_type or SearchType.HYBRID
        retriever = self._get_retriever(search_type)

        return retriever.retrieve(
            query=query,
            limit=limit,
            prefetch_limit=prefetch_limit,
            collection_name=collection_name,
            score_threshold=score_threshold,
        )

    def close(self):
        """Close all active retrievers and their connections."""
        for retriever in self._retrievers.values():
            if hasattr(retriever, "close"):
                retriever.close()
        self._retrievers.clear()


if __name__ == "__main__":
    import json

    from settings import settings

    openai_client = OpenAI()
    collection_name = "service_manual_pages"

    retrieval_config = RetrievalConfig(
        qdrant_host=settings.QDRANT_URL,
        qdrant_api_key=settings.QDRANT_API_KEY,
        timeout=60,
    )

    # Initialize the unified retriever
    retriever = QdrantRetrieverStrategy(
        config=retrieval_config, openai_client=openai_client
    )

    # Example query
    query = "When should I consider replacing my boom chains?"

    # Try different search types
    try:
        # Hybrid search
        hybrid_results = retriever.retrieve(
            query=query,
            search_type=SearchType.HYBRID,
            limit=10,
            prefetch_limit=20,
            collection_name=collection_name,
            score_threshold=4,
        )
        print(hybrid_results)

        with open("hybrid_results.json", "w") as f:
            json.dump(hybrid_results, f)
        # matryoska_results = retriever.retrieve(
        #     query=query,
        #     search_type=SearchType.MATRIOSKA,
        #     limit=10,
        #     prefetch_limit=20,
        #     collection_name=collection_name,
        # )

        # colbert_results = retriever.retrieve(
        #     query=query,
        #     search_type=SearchType.COLBERT,
        #     limit=10,
        #     collection_name=collection_name,
        # )

        # fusion_results = retriever.retrieve(
        #     query=query,
        #     search_type=SearchType.FUSION,
        #     limit=10,
        #     collection_name=collection_name,
        # )

        # print("Hybrid results:", len(hybrid_results))
        # print("Matryoska results", len(matryoska_results))
        # print("Colbert results", len(colbert_results))
        # print("Fusion results", len(fusion_results))

        # # sources = list(set([node["payload"]["name"] for node in hybrid_results]))
        # hybrid_scores = [
        #     (node["payload"]["document_type"], node["score"]) for node in hybrid_results
        # ]

        # matrioska_scores = [
        #     (node["payload"]["document_type"], node["score"])
        #     for node in matryoska_results
        # ]

        # colbert_scores = [
        #     (node["payload"]["document_type"], node["score"])
        #     for node in colbert_results
        # ]

        # fusion_scores = [
        #     (node["payload"]["document_type"], node["score"]) for node in fusion_results
        # ]

        # print(hybrid_scores)
        # print("------------")
        # print(matrioska_scores)
        # print("------------")
        # print(colbert_scores)
        # print("------------")
        # print(fusion_scores)

    finally:
        # Clean up resources
        pass
