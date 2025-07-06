import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.late_interaction import LateInteractionTextEmbedding
from openai import OpenAI
from qdrant_client import QdrantClient, models
from tqdm import tqdm


def build_embedding_text_from_page_metadata(metadata: dict) -> str:
    """Extract structured text from page metadata for embedding generation."""
    doc = metadata.get("document_metadata", {})
    section = metadata.get("section", {})
    page_number = metadata.get("page_number", "")
    content_elements = metadata.get("content_elements", [])

    # Header
    header = [
        f"Document: {doc.get('document_title', '')} ({doc.get('manufacturer', '')}, Revision {doc.get('document_revision', '')})",
        f"Section: {section.get('section_number', '')} {section.get('section_title', '')}",
        f"Subsection: {section.get('subsection_number', '')} {section.get('subsection_title', '')}",
        f"Page: {page_number}",
    ]

    # Text content
    body = []
    for el in content_elements:
        el_type = el.get("type", "")
        title = el.get("title", "")
        summary = el.get("summary", "")
        text = ""
        if el_type == "text_block":
            text += f"Text Block: {title}\nSummary: {summary}\n"
        elif el_type == "figure":
            text += f"Figure: {title} – {summary}\n"
        elif el_type == "table":
            text += f"Table: {title} – {summary}\n"
        body.append(text.strip())

    # Include full text content if available
    if metadata.get("text_content"):
        body.append(f"Full Text Content:\n{metadata.get('text_content')}")

    # Entities and other metadata
    all_entities = set()
    all_keywords = set()
    all_warnings = set()
    all_contexts = set()
    all_models = set()

    for el in content_elements:
        all_entities.update(el.get("entities", []))
        all_keywords.update(el.get("keywords", []))
        all_warnings.update(el.get("warnings", []))
        all_contexts.update(el.get("application_context", []))
        all_models.update(el.get("model_applicability", []))

    tail = [
        f"Entities: {', '.join(sorted(all_entities))}" if all_entities else "",
        f"Warnings: {', '.join(sorted(all_warnings))}" if all_warnings else "",
        f"Keywords: {', '.join(sorted(all_keywords))}" if all_keywords else "",
        f"Model Applicability: {', '.join(sorted(all_models))}" if all_models else "",
        f"Context: {', '.join(sorted(all_contexts))}" if all_contexts else "",
    ]

    # Final embedding text
    full_text = "\n\n".join(part for part in (header + body + tail) if part)
    return full_text


@dataclass
class VectorConfig:
    dense_size: int
    colbert_size: int
    small_embedding_size: int = 128
    large_embedding_size: int = 1024


class QdrantIndexer:
    def __init__(
        self,
        page_metadata_list: List[
            Dict[str, Any]
        ],  # Changed from 'nodes' to be more specific
        qdrant_client: QdrantClient,
        qdrant_collection: str,
        batch_size: int = 4,
        openai_client: Optional[OpenAI] = None,
        include_full_metadata: bool = True,  # New parameter
    ):
        # Store client
        self.qdrant_client = qdrant_client
        self.qdrant_collection = qdrant_collection
        self.batch_size = batch_size
        self.include_full_metadata = include_full_metadata

        self.openai_client = openai_client or OpenAI()

        # Initialize embedding models
        self.dense_embedding_model = TextEmbedding(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.sparse_embedding_model = SparseTextEmbedding(
            "Qdrant/bm42-all-minilm-l6-v2-attentions"
        )
        self.late_interaction_model = LateInteractionTextEmbedding(
            "colbert-ir/colbertv2.0"
        )

        # Process page metadata into documents and metadata
        self._process_page_metadata(page_metadata_list)

        logging.info(f"QdrantIndexer initialized with {len(page_metadata_list)} pages")

    def _process_page_metadata(self, page_metadata_list: List[Dict[str, Any]]) -> None:
        """Extract text and metadata from page metadata."""

        self.ids = []
        self.documents = []
        self.metadata = []

        for i, page_metadata in enumerate(page_metadata_list):
            try:
                # Generate embedding text using your function
                embedding_text = build_embedding_text_from_page_metadata(page_metadata)

                # Create ID from document info and page number
                doc_info = page_metadata.get("document_metadata", {})
                page_num = page_metadata.get("page_number", i)
                doc_id = doc_info.get("document_id", "unknown")
                # Create a hash-based integer ID for Qdrant compatibility
                point_id_str = f"{doc_id}_page_{page_num}"
                point_id = (
                    hash(point_id_str) & 0x7FFFFFFFFFFFFFFF
                )  # Convert to positive 64-bit integer

                self.ids.append(point_id)
                self.documents.append(embedding_text)

                # Create structured metadata for easier filtering and retrieval
                structured_metadata = {
                    "page_number": page_metadata.get("page_number"),
                    "document_id": doc_info.get("document_id"),
                    "document_title": doc_info.get("document_title"),
                    "document_type": doc_info.get("document_type"),
                    "manufacturer": doc_info.get("manufacturer"),
                    "models_covered": doc_info.get("models_covered", []),
                    "section_number": page_metadata.get("section", {}).get(
                        "section_number"
                    ),
                    "section_title": page_metadata.get("section", {}).get(
                        "section_title"
                    ),
                    "subsection_number": page_metadata.get("section", {}).get(
                        "subsection_number"
                    ),
                    "subsection_title": page_metadata.get("section", {}).get(
                        "subsection_title"
                    ),
                    "has_tables": page_metadata.get("has_tables", False),
                    "has_figures": page_metadata.get("has_figures", False),
                    "table_count": page_metadata.get("table_count", 0),
                    "figure_count": page_metadata.get("figure_count", 0),
                    "text_block_count": page_metadata.get("text_block_count", 0),
                    "page_visual_description": page_metadata.get(
                        "page_visual_description"
                    ),
                }

                # Extract aggregated entities, keywords, etc. for easier filtering
                all_entities = set()
                all_keywords = set()
                all_warnings = set()
                all_contexts = set()
                all_models = set()
                all_component_types = set()

                for el in page_metadata.get("content_elements", []):
                    all_entities.update(el.get("entities", []))
                    all_keywords.update(el.get("keywords", []))
                    all_warnings.update(el.get("warnings", []))
                    all_contexts.update(el.get("application_context", []))
                    all_models.update(el.get("model_applicability", []))
                    if el.get("component_type"):
                        all_component_types.add(el.get("component_type"))

                structured_metadata.update(
                    {
                        "entities": list(all_entities),
                        "keywords": list(all_keywords),
                        "warnings": list(all_warnings),
                        "application_contexts": list(all_contexts),
                        "applicable_models": list(all_models),
                        "component_types": list(all_component_types),
                    }
                )

                # Include full metadata if requested (useful for reconstruction)
                if self.include_full_metadata:
                    structured_metadata["full_page_metadata"] = page_metadata

                self.metadata.append(structured_metadata)

            except Exception as e:
                logging.error(f"Error processing page metadata {i}: {str(e)}")
                # Use fallback values with integer ID
                self.ids.append(i)  # Use simple integer as fallback ID
                self.documents.append(f"Error processing page {i}")
                self.metadata.append({"error": str(e), "page_index": i})

    def create_collection(self) -> None:
        """Create collection with vector configurations if it doesn't exist."""

        if self.qdrant_client.collection_exists(self.qdrant_collection):
            logging.info(f"Collection '{self.qdrant_collection}' already exists")
            return

        # Get sample embeddings to determine dimensions
        sample_text = self.documents[0] if self.documents else "Sample text"
        dense_embedding = list(self.dense_embedding_model.embed([sample_text]))[0]
        late_interaction_embedding = list(
            self.late_interaction_model.embed([sample_text])
        )[0]

        # Create collection with vector configurations
        self.qdrant_client.create_collection(
            collection_name=self.qdrant_collection,
            vectors_config={
                "dense": models.VectorParams(
                    size=len(dense_embedding),
                    distance=models.Distance.COSINE,
                ),
                "colbert": models.VectorParams(
                    size=len(late_interaction_embedding[0]),
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                ),
                "small-embedding": models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE,
                    datatype=models.Datatype.FLOAT16,
                ),
                "large-embedding": models.VectorParams(
                    size=1024,
                    distance=models.Distance.COSINE,
                    datatype=models.Datatype.FLOAT16,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=False,
                    ),
                )
            },
        )
        logging.info(f"Created collection '{self.qdrant_collection}'")

    def _get_embeddings(self, text: str) -> Dict[str, Any]:
        """Generate all types of embeddings for a given text."""

        try:
            return {
                "dense": list(self.dense_embedding_model.embed([text]))[0].tolist(),
                "colbert": list(self.late_interaction_model.embed([text]))[0].tolist(),
                "small-embedding": self._get_small_embedding(text),
                "large-embedding": self._get_large_embedding(text),
                "sparse": self._create_sparse_vector(text),
            }
        except Exception as e:
            logging.error(f"Error generating embeddings: {str(e)}")
            raise

    def _get_small_embedding(self, text: str) -> List[float]:
        """Generate small embedding using OpenAI API."""

        try:
            response = self.openai_client.embeddings.create(
                input=text, model="text-embedding-3-small", dimensions=128
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error getting small embedding: {str(e)}")
            raise

    def _get_large_embedding(self, text: str) -> List[float]:
        """Generate large embedding using OpenAI API."""

        try:
            response = self.openai_client.embeddings.create(
                input=text, model="text-embedding-3-large", dimensions=1024
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error getting large embedding: {str(e)}")
            raise

    def _create_sparse_vector(self, text: str) -> models.SparseVector:
        """Create sparse vector from text."""

        try:
            embeddings = list(self.sparse_embedding_model.embed([text]))[0]

            if not (hasattr(embeddings, "indices") and hasattr(embeddings, "values")):
                raise ValueError("Invalid sparse embeddings format")

            return models.SparseVector(
                indices=embeddings.indices.tolist(), values=embeddings.values.tolist()
            )
        except Exception as e:
            logging.error(f"Error creating sparse vector: {str(e)}")
            raise

    def create_point(
        self, id, text: str, metadata: Dict[str, Any]
    ) -> models.PointStruct:
        """Create a single point with all vector types and metadata."""

        try:
            vectors = self._get_embeddings(text)

            # Include the embedding text in payload for reference
            payload = {"embedding_text": text, **metadata}

            return models.PointStruct(id=id, vector=vectors, payload=payload)
        except Exception as e:
            logging.error(f"Error creating point for id {id}: {str(e)}")
            raise

    def index_documents(self) -> None:
        """Index all pages in batches with progress tracking."""

        total_docs = len(self.documents)
        processed = 0
        failed_batches = []

        with tqdm(total=total_docs, desc="Indexing pages") as pbar:
            while processed < total_docs:
                end_idx = min(processed + self.batch_size, total_docs)
                batch_ids = self.ids[processed:end_idx]
                batch_docs = self.documents[processed:end_idx]
                batch_metadata = self.metadata[processed:end_idx]

                try:
                    points = [
                        self.create_point(id=id, text=doc, metadata=metadata)
                        for id, doc, metadata in zip(
                            batch_ids, batch_docs, batch_metadata
                        )
                    ]

                    self.qdrant_client.upsert(
                        collection_name=self.qdrant_collection, points=points
                    )

                except Exception as e:
                    logging.error(
                        f"Error processing batch {processed}-{end_idx}: {str(e)}"
                    )
                    failed_batches.append((processed, end_idx))

                batch_size = end_idx - processed
                pbar.update(batch_size)
                processed = end_idx

        if failed_batches:
            logging.warning(
                f"Failed to process {len(failed_batches)} batches: {failed_batches}"
            )
        else:
            logging.info(f"Successfully processed all {total_docs} pages")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the indexed collection."""
        try:
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            return {
                "collection_name": self.qdrant_collection,
                "points_count": collection_info.points_count,
                "vectors_config": collection_info.config.params.vectors,
                "sparse_vectors_config": collection_info.config.params.sparse_vectors,
            }
        except Exception as e:
            logging.error(f"Error getting collection info: {str(e)}")
            return {"error": str(e)}


# Example usage:
if __name__ == "__main__":
    # Example of how to use the modified indexer
    import json

    from settings import settings

    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    # Load your page metadata files
    page_metadata_list = []

    for page_number in range(4, 566):
        try:
            page_metadata_list.append(
                json.load(
                    open(
                        f"/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_{page_number}/context_metadata_page_{page_number}.json"
                    )
                )
            )
        except FileNotFoundError:
            print(f"Page {page_number} not found")
            continue

    # Initialize the indexer
    indexer = QdrantIndexer(
        page_metadata_list=page_metadata_list,
        qdrant_client=qdrant_client,
        qdrant_collection="service_manual_pages",
        batch_size=1,
    )

    # Create collection and index documents
    indexer.create_collection()
    indexer.index_documents()
    print(indexer.get_collection_info())
