from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from colpali_rag.core.utils import (
    encode_image_to_data_uri,
    read_json_file,
    read_text_file,
)
from colpali_rag.documents.algorithms.metadata.extract_page_metadata_with_context import (
    extract_metadata_from_page_with_response,
)
from colpali_rag.llm.litellm_client import LitellmClient


@dataclass
class PageData:
    """Data structure for a single page's information"""

    page_number: int
    image_path: Path
    image_data_uri: str
    metadata_path: Path
    metadata_content: str
    text_path: Path
    text_content: str


@dataclass
class PageContext:
    """Data structure containing n-1, n, and n+1 page information"""

    previous_page: Optional[PageData]
    current_page: PageData
    next_page: Optional[PageData]


def get_page_context(page_number: int, pdf_base_path: Path) -> PageContext:
    """
    Get the context for a specific page including n-1, n, and n+1 pages.

    Args:
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory (e.g., scratch/service_manual_long/)

    Returns:
        PageContext containing data for previous, current, and next pages

    Raises:
        FileNotFoundError: If the current page doesn't exist
        ValueError: If page_number is less than 1
    """
    if page_number < 1:
        raise ValueError("Page number must be at least 1")

    # Current page paths
    current_page_dir = pdf_base_path / f"page_{page_number}"
    current_image_path = current_page_dir / f"page_{page_number}_full.png"
    current_metadata_path = current_page_dir / f"metadata_page_{page_number}.json"
    current_text_path = current_page_dir / "text" / f"page_{page_number}_text.txt"

    # Verify current page exists
    if not current_page_dir.exists():
        raise FileNotFoundError(
            f"Page {page_number} directory not found at {current_page_dir}"
        )

    # Load current page data
    current_page = PageData(
        page_number=page_number,
        image_path=current_image_path,
        image_data_uri=encode_image_to_data_uri(current_image_path),
        metadata_path=current_metadata_path,
        metadata_content=str(read_json_file(current_metadata_path)),
        text_path=current_text_path,
        text_content=str(read_text_file(current_text_path)),
    )

    # Previous page (n-1)
    previous_page = None
    if page_number > 1:
        prev_page_dir = pdf_base_path / f"page_{page_number - 1}"
        if prev_page_dir.exists():
            prev_image_path = prev_page_dir / f"page_{page_number - 1}_full.png"
            prev_metadata_path = prev_page_dir / f"metadata_page_{page_number - 1}.json"
            prev_text_path = prev_page_dir / "text" / f"page_{page_number - 1}_text.txt"

            previous_page = PageData(
                page_number=page_number - 1,
                image_path=prev_image_path,
                image_data_uri=encode_image_to_data_uri(prev_image_path),
                metadata_path=prev_metadata_path,
                metadata_content=str(read_json_file(prev_metadata_path)),
                text_path=prev_text_path,
                text_content=str(read_text_file(prev_text_path)),
            )

    # Next page (n+1)
    next_page = None
    next_page_dir = pdf_base_path / f"page_{page_number + 1}"
    if next_page_dir.exists():
        next_image_path = next_page_dir / f"page_{page_number + 1}_full.png"
        next_metadata_path = next_page_dir / f"metadata_page_{page_number + 1}.json"
        next_text_path = next_page_dir / "text" / f"page_{page_number + 1}_text.txt"

        next_page = PageData(
            page_number=page_number + 1,
            image_path=next_image_path,
            image_data_uri=encode_image_to_data_uri(next_image_path),
            metadata_path=next_metadata_path,
            metadata_content=str(read_json_file(next_metadata_path)),
            text_path=next_text_path,
            text_content=str(read_text_file(next_text_path)),
        )

    return PageContext(
        previous_page=previous_page, current_page=current_page, next_page=next_page
    )


def extract_metadata_with_context(
    litellm_client: LitellmClient,
    page_number: int,
    pdf_base_path: Path,
) -> str:
    """
    Extract metadata for a specific page using its context (n-1, n, n+1).

    This is a convenience function that combines get_page_context() with
    extract_metadata_from_page() to provide a simpler interface.

    Args:
        litellm_client: LitellmClient instance
        page_number: The target page number
        pdf_base_path: Base path to the processed PDF directory

    Returns:
        Extracted metadata as a string

    Raises:
        FileNotFoundError: If the current page doesn't exist
        ValueError: If page_number is less than 1 or if context pages are missing
    """
    context = get_page_context(page_number, pdf_base_path)

    # Check if we have the required context pages
    if not context.previous_page:
        raise ValueError(f"Previous page {page_number - 1} not found")
    if not context.next_page:
        raise ValueError(f"Next page {page_number + 1} not found")

    return extract_metadata_from_page_with_response(
        litellm_client=litellm_client,
        image_path_n=str(context.current_page.image_path),
        image_path_n_1=str(context.previous_page.image_path),
        image_path_n_plus_1=str(context.next_page.image_path),
        metadata_page_n_1_path=str(context.previous_page.metadata_path),
        metadata_page_n_path=str(context.current_page.metadata_path),
        metadata_page_n_plus_1_path=str(context.next_page.metadata_path),
        page_n_1_text_path=str(context.previous_page.text_path),
        page_n_text_path=str(context.current_page.text_path),
        page_n_plus_1_text_path=str(context.next_page.text_path),
    )


if __name__ == "__main__":
    import json

    from litellm import completion_cost

    # Example usage
    pdf_base_path = Path(
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long"
    )

    # Example 1: Get page context
    context = get_page_context(28, pdf_base_path)

    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    response = extract_metadata_with_context(litellm_client, 148, pdf_base_path)

    # Extract the content from the response
    metadata_content = response.choices[0].message.content

    # Get cost information using LiteLLM's completion_cost function
    cost = completion_cost(completion_response=response)
    print(f"💰 API Call Cost: ${cost:.6f}")

    # Get token usage information
    if hasattr(response, "usage"):
        usage = response.usage
        print("📊 Token Usage:")
        print(f"   Prompt tokens: {getattr(usage, 'prompt_tokens', 'N/A')}")
        print(f"   Completion tokens: {getattr(usage, 'completion_tokens', 'N/A')}")
        print(f"   Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")

    # Alternative: Get cost from response._hidden_params if available
    if (
        hasattr(response, "_hidden_params")
        and "response_cost" in response._hidden_params
    ):
        hidden_cost = response._hidden_params["response_cost"]
        print(f"💰 Hidden Cost: ${hidden_cost:.6f}")

    clean_json_str = (
        metadata_content.strip().removeprefix("```json").removesuffix("```").strip()
    )
    parsed_data = json.loads(clean_json_str)

    # Step 3: Save to JSON file properly
    with open("page_148_metadata.json", "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
