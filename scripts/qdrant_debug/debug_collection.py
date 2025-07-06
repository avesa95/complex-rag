#!/usr/bin/env python3
"""
Debug script to see what's actually in the Qdrant collection.
"""

from qdrant_client import QdrantClient

from settings import settings


def main():
    """Debug what's in the collection."""
    print("Debugging collection contents...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

    collection_name = "service_manual_pages"

    try:
        # Get collection info
        collection_info = qdrant_client.get_collection(collection_name)
        total_points = collection_info.points_count
        print(f"Total points in collection: {total_points}")

        # Get first few points to see their structure
        points = qdrant_client.scroll(
            collection_name=collection_name, limit=5, with_payload=True
        )[0]

        print("\nFirst 5 points in collection:")
        for i, point in enumerate(points):
            print(f"\nPoint {i + 1}:")
            print(f"  ID: {point.id}")
            print(f"  Payload keys: {list(point.payload.keys())}")

            # Show some key fields
            if "page_number" in point.payload:
                print(f"  page_number: {point.payload['page_number']}")
            if "document_id" in point.payload:
                print(f"  document_id: {point.payload['document_id']}")
            if "document_title" in point.payload:
                print(f"  document_title: {point.payload['document_title']}")

        # Check if there are any points with page_number
        all_points = qdrant_client.scroll(
            collection_name=collection_name, limit=total_points, with_payload=True
        )[0]

        pages_with_number = 0
        pages_without_number = 0

        for point in all_points:
            if "page_number" in point.payload:
                pages_with_number += 1
            else:
                pages_without_number += 1

        print(f"\nPoints with page_number: {pages_with_number}")
        print(f"Points without page_number: {pages_without_number}")

        # Show a few examples of page numbers if they exist
        if pages_with_number > 0:
            print("\nSample page numbers found:")
            count = 0
            for point in all_points:
                if "page_number" in point.payload and count < 10:
                    print(f"  {point.payload['page_number']}")
                    count += 1

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
