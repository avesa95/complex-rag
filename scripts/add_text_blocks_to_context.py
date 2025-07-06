#!/usr/bin/env python3
"""
Simple script to add text block content to context metadata files.
"""

import json
from pathlib import Path

# Path to the scratch folder
scratch_path = Path("scratch/service_manual_long")

print(f"Adding text blocks to context metadata files in: {scratch_path}")

# Find all page directories
page_dirs = []
for item in scratch_path.iterdir():
    if item.is_dir() and item.name.startswith("page_"):
        page_dirs.append(item)

# Sort by page number
page_dirs.sort(key=lambda x: int(x.name.split("_")[1]))

print(f"Found {len(page_dirs)} page directories")

# Process each page
for page_dir in page_dirs:
    page_number = page_dir.name.split("_")[1]

    context_file = page_dir / f"context_metadata_page_{page_number}.json"
    text_file = page_dir / "text" / f"page_{page_number}_text.txt"

    if not context_file.exists():
        print(f"Skipping page {page_number} - no context metadata file")
        continue

    # Read context metadata
    with open(context_file, "r") as f:
        context_metadata = json.load(f)

    # Check if page has text blocks
    if not context_metadata.get("has_text_blocks", False):
        continue

    print(f"Processing text blocks for page {page_number}...")

    # Check if text file exists
    if not text_file.exists():
        print(f"  Warning: Text file not found: {text_file}")
        continue

    # Read text content
    with open(text_file, "r") as f:
        text_content = f.read()

    # Add text content to context metadata
    context_metadata["text_content"] = text_content
    context_metadata["text_file"] = str(text_file.name)

    # Save enhanced context metadata
    with open(context_file, "w") as f:
        json.dump(context_metadata, f, indent=2)

    print("  ✓ Added text content to context metadata")

print("Finished!")
