#!/usr/bin/env python3
"""
Simple script to retry the failed pages from the previous indexing run.
"""

import json
import logging

from qdrant_client import QdrantClient

from indexing_full_pages_with_metadata import QdrantIndexer
from settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)

# Failed pages from the previous run (page numbers, not indices)
FAILED_PAGES = [
    136,
    373,
    374,
    380,
    387,
    390,
    391,
    392,
    393,
    394,
    399,
    407,
    408,
    533,
    565,
]


def main():
    """Retry indexing of failed pages."""
    print("Starting retry of failed pages...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    # Load failed pages
    failed_pages = []
    for page_number in FAILED_PAGES:
        try:
            page_metadata = json.load(
                open(
                    f"/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_{page_number}/context_metadata_page_{page_number}.json"
                )
            )
            failed_pages.append(page_metadata)
            print(f"Loaded failed page {page_number}")
        except FileNotFoundError:
            print(f"Page {page_number} file not found")
            continue
        except Exception as e:
            print(f"Error loading page {page_number}: {str(e)}")
            continue

    print(f"Loaded {len(failed_pages)} failed pages to retry")

    if not failed_pages:
        print("No failed pages to retry")
        return

    # Initialize indexer with retry settings
    indexer = QdrantIndexer(
        page_metadata_list=failed_pages,
        qdrant_client=qdrant_client,
        qdrant_collection="service_manual_pages",
        batch_size=1,  # Process one page at a time
    )

    # Retry indexing
    print("Retrying failed pages...")
    indexer.index_documents()

    # Get final collection info
    collection_info = indexer.get_collection_info()
    print(f"Collection info: {collection_info}")

    print("Retry process completed!")


if __name__ == "__main__":
    main()
