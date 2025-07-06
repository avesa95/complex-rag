#!/usr/bin/env python3
"""
Script to find HTML tables in each page folder, flatten them, and save both
the flattened table and original HTML table to context metadata files.
"""

import json
import sys
from pathlib import Path

from colpali_rag.documents.algorithms.flatten_table import flatten_table
from colpali_rag.llm.litellm_client import LitellmClient

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))


# Path to the scratch folder
scratch_path = Path("scratch/service_manual_long")

print(f"Flattening tables in context metadata files in: {scratch_path}")

# Initialize the LLM client
try:
    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    print("✓ LLM client initialized")
except Exception as e:
    print(f"✗ Failed to initialize LLM client: {e}")
    sys.exit(1)

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

    if not context_file.exists():
        print(f"Skipping page {page_number} - no context metadata file")
        continue

    # Read context metadata
    with open(context_file, "r") as f:
        context_metadata = json.load(f)

    # Check if page has tables
    if not context_metadata.get("has_tables", False):
        continue

    print(f"Processing tables for page {page_number}...")

    # Check if tables directory exists
    tables_dir = page_dir / "tables"
    if not tables_dir.exists():
        print(f"  Warning: Tables directory not found: {tables_dir}")
        continue

    # Find all HTML table files
    html_tables = list(tables_dir.glob("*.html"))

    if not html_tables:
        print(f"  No HTML table files found in {tables_dir}")
        continue

    print(f"  Found {len(html_tables)} HTML table(s)")

    # Initialize flattened_tables list if it doesn't exist
    if "flattened_tables" not in context_metadata:
        context_metadata["flattened_tables"] = []

    # Process each HTML table
    for html_file in html_tables:
        table_id = html_file.stem  # e.g., "table-564-1"

        print(f"    Processing {table_id}...")

        # Read HTML content
        with open(html_file, "r") as f:
            html_content = f.read()

        try:
            # Flatten the table
            flattened_content = flatten_table(litellm_client, html_content)

            # Create table entry
            table_entry = {
                "table_id": table_id,
                "html_file": html_file.name,
                "html_content": html_content,
                "flattened_content": flattened_content,
            }

            # Add to context metadata
            context_metadata["flattened_tables"].append(table_entry)

            print(f"    ✓ Flattened {table_id}")

        except Exception as e:
            print(f"    ✗ Failed to flatten {table_id}: {e}")
            continue

    # Save enhanced context metadata
    with open(context_file, "w") as f:
        json.dump(context_metadata, f, indent=2)

    print(f"  ✓ Updated context metadata for page {page_number}")

print("Finished!")
