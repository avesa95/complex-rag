#!/usr/bin/env python3
"""
PDF Indexing Script

Simple script to index a PDF file and create embeddings in Qdrant.
"""

import os
import sys
from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from tqdm import tqdm

from colpali_rag.qdrant_manager import QdrantManager
from settings import settings


def convert_single_pdf_to_images(pdf_path: str) -> List:
    """
    Convert a single PDF file to images.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        List: List of images from the PDF
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    print(f"Converting PDF to images: {pdf_path}")
    images = convert_from_path(pdf_path)
    print(f"Converted {len(images)} pages to images")
    return images


def index_pdf(
    pdf_path: str, collection_name: str = "colpali_demo", batch_size: int = 16
):
    """
    Index a PDF file by converting it to images and creating embeddings in
    Qdrant.

    Args:
        pdf_path (str): Path to the PDF file
        collection_name (str): Name of the Qdrant collection
        batch_size (int): Batch size for processing
    """
    try:
        # Convert PDF to images
        images = convert_single_pdf_to_images(pdf_path)

        if not images:
            print("No images extracted from PDF")
            return

        # Initialize Qdrant manager
        print(f"Initializing Qdrant manager with collection: {collection_name}")
        qdrant_manager = QdrantManager(
            collection_name=collection_name,
            model_name=settings.COLPALI_MODEL_NAME,
            batch_size=batch_size,
            image_seq_length=settings.IMAGE_SEQ_LENGTH,
        )

        # Get the next available ID
        collection_info = qdrant_manager.get_collection_info()
        next_id = collection_info.get("points_count", 0)

        # Process images in batches
        total_images = len(images)
        print(f"Processing {total_images} images in batches of {batch_size}")

        for i in tqdm(range(0, total_images, batch_size), desc="Processing batches"):
            batch_images = images[i : i + batch_size]
            batch_payloads = []

            for j, image in enumerate(batch_images):
                payload = {
                    "file_name": os.path.basename(pdf_path),
                    "page_number": i + j + 1,
                    "total_pages": total_images,
                    "source_type": "pdf",
                    "batch_id": i // batch_size,
                }
                batch_payloads.append(payload)

            # Upload batch to Qdrant
            success = qdrant_manager.embed_and_upload_batch(
                image_batch=batch_images,
                payload_batch=batch_payloads,
                id_start=next_id + i,
            )

            if not success:
                print(f"Failed to upload batch starting at index {i}")

        print(f"Successfully indexed PDF: {pdf_path}")
        print(f"Total pages indexed: {total_images}")

    except Exception as e:
        print(f"Error indexing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Simple usage - just change the PDF path here

    PDF_PATH = "/Users/vesaalexandru/Workspaces/cube/complex-rag/31211033 - JLG 642, 742, 943, 1043, 1055, 1255-1_removed_removed_removed.pdf"

    # Validate PDF path
    pdf_path = Path(PDF_PATH)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == ".pdf":
        print(f"Error: File must be a PDF: {pdf_path}")
        sys.exit(1)

    print("Starting PDF indexing...")
    print(f"PDF: {pdf_path}")
    print("-" * 50)

    # Run indexing
    index_pdf(pdf_path=str(pdf_path), collection_name="automotive_docs", batch_size=16)
