#!/usr/bin/env python3
"""
Check which pages are missing from the Qdrant collection.
"""

from qdrant_client import QdrantClient

from settings import settings


def main():
    """Check which pages are missing from the collection."""
    print("Checking which pages are missing from the collection...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    # Get all points from the collection
    collection_name = "service_manual_pages"

    try:
        # Get collection info
        collection_info = qdrant_client.get_collection(collection_name)
        total_points = collection_info.points_count
        print(f"Total points in collection: {total_points}")

        # Get all points with their payloads
        all_points = qdrant_client.scroll(
            collection_name=collection_name, limit=total_points, with_payload=True
        )[0]

        # Extract page numbers from the indexed pages
        indexed_pages = set()
        for point in all_points:
            payload = point.payload
            if "page_number" in payload:
                indexed_pages.add(payload["page_number"])

        print(f"Found {len(indexed_pages)} indexed pages")

        # Check which pages from 4-565 are missing
        expected_pages = set(range(4, 566))
        missing_pages = expected_pages - indexed_pages

        print(f"Missing pages: {sorted(missing_pages)}")
        print(f"Total missing: {len(missing_pages)}")

        return sorted(missing_pages)

    except Exception as e:
        print(f"Error checking collection: {str(e)}")
        return []


if __name__ == "__main__":
    missing = main()
