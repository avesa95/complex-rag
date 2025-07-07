#!/usr/bin/env python3
"""
Script to extract text block metadata and add it to context metadata files.
"""

import json
from pathlib import Path

from colpali_rag.core.utils import encode_image_to_data_uri
from colpali_rag.documents.prompts import (
    GENERATE_TEXT_METADATA_PROMPT,
)
from colpali_rag.documents.schemas import TextMetadataResponse
from colpali_rag.llm.litellm_client import LitellmClient


def generate_text_metadata(
    litellm_client: LitellmClient, text_content: str, pdf_page: str
) -> dict:
    """Generate metadata for a text block."""
    image_data_uri = encode_image_to_data_uri(pdf_page)

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": GENERATE_TEXT_METADATA_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                    {
                        "type": "text",
                        "text": f"Text content:\n{text_content}",
                    },
                ],
            },
        ],
        response_format=TextMetadataResponse,
        temperature=0.0,
    )
    metadata_resp_string = resp.choices[0].message.content
    metadata_resp_json = json.loads(metadata_resp_string)
    return metadata_resp_json


def process_all_text_blocks(scratch_path: Path = None):
    """Process all text blocks in pages where has_text_blocks is true."""
    if scratch_path is None:
        scratch_path = Path("scratch/service_manual_long")

    litellm_client = LitellmClient(model_name="openai/gpt-4o")

    # Find all page directories
    page_dirs = []
    for item in scratch_path.iterdir():
        if item.is_dir() and item.name.startswith("page_"):
            page_dirs.append(item)

    # Sort by page number
    page_dirs.sort(key=lambda x: int(x.name.split("_")[1]))

    print(f"Found {len(page_dirs)} page directories")

    for page_dir in page_dirs:
        page_number = page_dir.name.split("_")[1]

        # Check if this page has text blocks
        context_file = page_dir / f"context_metadata_page_{page_number}.json"
        basic_file = page_dir / f"metadata_page_{page_number}.json"

        if not context_file.exists() or not basic_file.exists():
            print(f"Skipping page {page_number} - missing metadata files")
            continue

        # Read context metadata to check if has_text_blocks is true
        with open(context_file, "r") as f:
            context_metadata = json.load(f)

        if not context_metadata.get("has_text_blocks", False):
            continue

        print(f"Processing text blocks for page {page_number}...")

        # Get text files
        text_dir = page_dir / "text"
        if not text_dir.exists():
            print(f"  No text directory found for page {page_number}")
            continue

        text_files = list(text_dir.glob("page_*_text.txt"))
        if not text_files:
            print(f"  No text files found for page {page_number}")
            continue

        # Process each text file
        text_metadata_list = []
        for text_file in sorted(text_files):
            text_name = text_file.stem  # e.g., "page_15_text"
            print(f"  Processing {text_name}...")

            try:
                # Read text content
                with open(text_file, "r") as f:
                    text_content = f.read()

                # Get corresponding page image
                page_image = page_dir / f"page_{page_number}_full.png"
                if not page_image.exists():
                    print(f"    Warning: Page image not found for {text_name}")
                    continue

                # Generate text metadata
                text_metadata = generate_text_metadata(
                    litellm_client, text_content, page_image
                )

                # Add text identifier
                text_metadata["text_id"] = text_name
                text_metadata["text_file"] = str(text_file.name)

                text_metadata_list.append(text_metadata)
                print(f"    ✓ Generated metadata for {text_name}")

            except Exception as e:
                print(f"    ✗ Error processing {text_name}: {e}")

        # Add text metadata to context metadata
        if text_metadata_list:
            context_metadata["text_metadata"] = text_metadata_list

            # Save enhanced context metadata
            with open(context_file, "w") as f:
                json.dump(context_metadata, f, indent=2)

            print(
                f"  ✓ Added {len(text_metadata_list)} text block(s) to context metadata"
            )
        else:
            print(f"  No text metadata generated for page {page_number}")


if __name__ == "__main__":
    # Process all text blocks
    process_all_text_blocks()
