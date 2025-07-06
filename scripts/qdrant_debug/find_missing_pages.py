#!/usr/bin/env python3
"""
Find the exact page numbers that are missing from the collection.
"""

from qdrant_client import QdrantClient

from settings import settings


def main():
    """Find missing page numbers."""
    print("Finding missing page numbers...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    collection_name = "service_manual_pages"

    try:
        # Get collection info first
        collection_info = qdrant_client.get_collection(collection_name)
        total_points = collection_info.points_count
        print(f"Total points in collection: {total_points}")

        # Get all points
        all_points = qdrant_client.scroll(
            collection_name=collection_name, limit=total_points, with_payload=True
        )[0]

        print(f"Retrieved {len(all_points)} points")

        # Extract all page numbers as integers
        indexed_pages = set()
        for point in all_points:
            if "page_number" in point.payload:
                try:
                    indexed_pages.add(int(point.payload["page_number"]))
                except Exception:
                    pass

        print(f"Total indexed pages: {len(indexed_pages)}")
        print(f"Sample indexed pages: {sorted(list(indexed_pages))[:10]}")

        # Expected pages (4-565)
        expected_pages = set(range(4, 566))
        missing_pages = expected_pages - indexed_pages

        print(f"Missing pages: {sorted(missing_pages)}")
        print(f"Total missing: {len(missing_pages)}")

        return sorted(missing_pages)

    except Exception as e:
        print(f"Error: {str(e)}")
        return []


if __name__ == "__main__":
    missing = main()
