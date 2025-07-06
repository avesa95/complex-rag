#!/usr/bin/env python3
"""
Simple script to enhance all context metadata files in the scratch folder.
"""

import sys
from pathlib import Path

from colpali_rag.core.utils import enhance_context_metadata_file

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))


# Path to the scratch folder
scratch_path = Path("scratch/service_manual_long")

print(f"Enhancing context metadata files in: {scratch_path}")

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
    basic_file = page_dir / f"metadata_page_{page_number}.json"

    if context_file.exists() and basic_file.exists():
        print(f"Enhancing page {page_number}...", end=" ")
        try:
            enhance_context_metadata_file(context_file, basic_file)
            print("✓ Done")
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print(f"Skipping page {page_number} - missing files")

print("Finished!")
