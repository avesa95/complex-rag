"""
Qdrant Vector Database Manager

This module provides functionality to manage document embeddings in Qdrant,
including collection creation, embedding upload, and similarity search.
"""

from typing import Any, Dict, List, Optional

import torch
from qdrant_client import QdrantClient
from qdrant_client.models import (
    BinaryQuantization,
    BinaryQuantizationConfig,
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    MultiVectorComparator,
    MultiVectorConfig,
    OptimizersConfigDiff,
    PointStruct,
    VectorParams,
)

from colpali_rag.model import load_colpali_model
from settings import settings


class QdrantManager:
    """
    Manages document embeddings in Qdrant vector database.

    This class handles:
    - Collection creation and management
    - Document embedding upload
    - Similarity search
    - Metadata filtering
    """

    def __init__(
        self,
        collection_name: str = "colpali_demo",
        model_name: str = "vidore/colpali-v1.2",
        batch_size: int = 16,
        image_seq_length: int = 1024,
    ):
        """
        Initialize Qdrant manager.

        Args:
            collection_name: Name of the Qdrant collection
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key (optional)
            model_name: ColPali model name
            batch_size: Batch size for processing
            image_seq_length: Image sequence length parameter
        """
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.image_seq_length = image_seq_length

        # Initialize Qdrant client
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

        # Load ColPali model and processor
        self.colpali_model, self.colpali_processor = load_colpali_model(model_name)

        # Create collection if it doesn't exist
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self._create_collection()
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Using existing collection: {self.collection_name}")

        except Exception as e:
            print(f"Error checking/creating collection: {e}")
            raise

    def _create_collection(self):
        """Create the Qdrant collection with proper configuration."""
        self.client.create_collection(
            collection_name=self.collection_name,
            shard_number=4,
            optimizers_config=OptimizersConfigDiff(
                memmap_threshold=0
            ),  # Vectors always in RAM for speed
            vectors_config={
                "initial": VectorParams(
                    size=128,
                    distance=Distance.COSINE,
                    on_disk=False,  # Vectors always in RAM
                    multivector_config=MultiVectorConfig(
                        comparator=MultiVectorComparator.MAX_SIM
                    ),
                    quantization_config=BinaryQuantization(
                        binary=BinaryQuantizationConfig(always_ram=True),
                    ),
                ),
                "max_pooling": VectorParams(
                    size=128,
                    distance=Distance.COSINE,
                    on_disk=False,  # Vectors always in RAM
                    multivector_config=MultiVectorConfig(
                        comparator=MultiVectorComparator.MAX_SIM
                    ),
                ),
                "mean_pooling": VectorParams(
                    size=128,
                    distance=Distance.COSINE,
                    on_disk=False,  # Vectors always in RAM
                    multivector_config=MultiVectorConfig(
                        comparator=MultiVectorComparator.MAX_SIM
                    ),
                    quantization_config=BinaryQuantization(
                        binary=BinaryQuantizationConfig(always_ram=True),
                    ),
                ),
            },
        )

    def embed_and_upload_batch(
        self, image_batch: List, payload_batch: List[Dict[str, Any]], id_start: int
    ) -> bool:
        """
        Embed a batch of images and upload to Qdrant.

        Args:
            image_batch: List of images to embed
            payload_batch: List of metadata payloads
            id_start: Starting ID for the batch

        Returns:
            bool: True if successful, False otherwise
        """
        batch_size_current = len(image_batch)

        if batch_size_current == 0:
            return True

        try:
            with torch.no_grad():
                batch_images = self.colpali_processor.process_images(image_batch).to(
                    self.colpali_model.device
                )
                image_embeddings = self.colpali_model(**batch_images)

            # Process max and mean pooled embeddings per row of image grid
            special_tokens = image_embeddings[:, self.image_seq_length :, :]

            # Reshape and apply pooling
            reshaped_embeddings = image_embeddings[
                :, : self.image_seq_length, :
            ].reshape((batch_size_current, 32, 32, 128))

            max_pool = torch.cat(
                (torch.max(reshaped_embeddings, dim=2).values, special_tokens), dim=1
            )

            mean_pool = torch.cat(
                (torch.mean(reshaped_embeddings, dim=2), special_tokens), dim=1
            )

            # Prepare points for batch upsert
            points = []
            for i in range(batch_size_current):
                point = PointStruct(
                    id=id_start + i,
                    payload=payload_batch[i],
                    vector={
                        "max_pooling": (max_pool[i].cpu().float().numpy().tolist()),
                        "initial": (image_embeddings[i].cpu().float().numpy().tolist()),
                        "mean_pooling": (mean_pool[i].cpu().float().numpy().tolist()),
                    },
                )
                points.append(point)

            # Batch upsert
            self.client.upsert(collection_name=self.collection_name, points=points)

            return True

        except Exception as e:
            print(f"Error during batch upsert: {e}")
            return False

    def search_similar_documents_text(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.5,
        vector_name: str = "initial",
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using a text query.

        Args:
            query_text: Text query to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            vector_name: Which vector type to use for search
            filter_conditions: Optional filter conditions

        Returns:
            List of search results with scores and metadata
        """
        try:
            # Process query text
            with torch.no_grad():
                processed_text = self.colpali_processor.process_queries(
                    [query_text]
                ).to(self.colpali_model.device)
                query_embedding = self.colpali_model(**processed_text)

            # Get embedding dimensions for debugging
            batch_size, seq_len, embed_dim = query_embedding.shape
            print(f"Text query embedding shape: {query_embedding.shape}")

            # Prepare search vector based on type
            if vector_name == "max_pooling":
                # For text queries, use simpler pooling since they don't have spatial structure
                if seq_len <= self.image_seq_length:
                    # Text query - use max pooling across sequence dimension
                    search_vector = torch.max(query_embedding, dim=1)[0]  # [1, 128]
                else:
                    # Fallback to image-style pooling if sequence is long enough
                    special_tokens = query_embedding[:, self.image_seq_length :, :]
                    spatial_tokens = query_embedding[:, : self.image_seq_length, :]
                    reshaped = spatial_tokens.reshape((batch_size, 32, 32, embed_dim))
                    search_vector = torch.cat(
                        (torch.max(reshaped, dim=2)[0], special_tokens), dim=1
                    )
                search_vector = search_vector[0].cpu().float().numpy().tolist()

            elif vector_name == "mean_pooling":
                # For text queries, use simpler pooling since they don't have spatial structure
                if seq_len <= self.image_seq_length:
                    # Text query - use mean pooling across sequence dimension
                    search_vector = torch.mean(query_embedding, dim=1)  # [1, 128]
                else:
                    # Fallback to image-style pooling if sequence is long enough
                    special_tokens = query_embedding[:, self.image_seq_length :, :]
                    spatial_tokens = query_embedding[:, : self.image_seq_length, :]
                    reshaped = spatial_tokens.reshape((batch_size, 32, 32, embed_dim))
                    search_vector = torch.cat(
                        (torch.mean(reshaped, dim=2), special_tokens), dim=1
                    )
                search_vector = search_vector[0].cpu().float().numpy().tolist()

            else:  # "initial" - use full embedding as multivector
                # For multivector, keep the 2D structure
                search_vector = query_embedding[0].cpu().float().numpy().tolist()

            print(
                f"Search vector type: {vector_name}, dimensions: {len(search_vector) if isinstance(search_vector[0], (int, float)) else f'{len(search_vector)}x{len(search_vector[0])}'}"
            )

            # Prepare filter if provided
            search_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=value))
                    )
                search_filter = Filter(must=conditions)

            # Perform search using the correct API format
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=search_vector,
                limit=limit,
                using=vector_name,
                query_filter=search_filter,
            )

            # Format results
            results = []
            for point in search_result.points:  # Note: access .points attribute
                results.append(
                    {"id": point.id, "score": point.score, "payload": point.payload}
                )

            return results

        except Exception as e:
            print(f"Error during text search: {e}")
            return []

    def search_similar_documents(
        self,
        query_image,
        limit: int = 10,
        score_threshold: float = 0.5,
        vector_name: str = "initial",
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using an image query.

        Args:
            query_image: Image to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            vector_name: Which vector type to use for search
            filter_conditions: Optional filter conditions

        Returns:
            List of search results with scores and metadata
        """
        try:
            # Process query image
            with torch.no_grad():
                processed_image = self.colpali_processor.process_images(
                    [query_image]
                ).to(self.colpali_model.device)
                query_embedding = self.colpali_model(**processed_image)

            # Prepare search vector based on type
            if vector_name == "max_pooling":
                special_tokens = query_embedding[:, self.image_seq_length :, :]
                reshaped = query_embedding[:, : self.image_seq_length, :].reshape(
                    (1, 32, 32, 128)
                )
                search_vector = torch.cat(
                    (torch.max(reshaped, dim=2).values, special_tokens), dim=1
                )
                # For pooled vectors, use flat list
                search_vector = search_vector[0].cpu().float().numpy().tolist()

            elif vector_name == "mean_pooling":
                special_tokens = query_embedding[:, self.image_seq_length :, :]
                reshaped = query_embedding[:, : self.image_seq_length, :].reshape(
                    (1, 32, 32, 128)
                )
                search_vector = torch.cat(
                    (torch.mean(reshaped, dim=2), special_tokens), dim=1
                )
                # For pooled vectors, use flat list
                search_vector = search_vector[0].cpu().float().numpy().tolist()

            else:  # "initial" - use full embedding as multivector
                # For multivector, keep the 2D structure
                search_vector = query_embedding[0].cpu().float().numpy().tolist()

            # Prepare filter if provided
            search_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=value))
                    )
                search_filter = Filter(must=conditions)

            # Perform search using the correct API format
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=search_vector,
                limit=limit,
                using=vector_name,
                query_filter=search_filter,
            )

            # Format results
            results = []
            for point in search_result.points:  # Note: access .points attribute
                results.append(
                    {"id": point.id, "score": point.score, "payload": point.payload}
                )

            return results

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def delete_collection(self) -> bool:
        """Delete the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vectors": info.config.params.vectors,
                    "optimizers": info.config.optimizer_config,
                },
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}

    def clear_collection(self) -> bool:
        """Clear all points from the collection."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={"filter": Filter(must=[])},
            )
            print(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
