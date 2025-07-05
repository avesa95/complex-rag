from pathlib import Path

from colpali_rag.core.utils import encode_image_to_data_uri
from colpali_rag.documents.algorithms.metadata.prompts import METADATA_PROMPT
from colpali_rag.llm.litellm_client import LitellmClient


def extract_metadata_from_page(
    litellm_client: LitellmClient,
    image_path_n: str,
    image_path_n_1: str,
    image_path_n_plus_1: str,
) -> str:
    """
    Answer a specific question by reading a technical manual page

    Args:
        litellm_client: LitellmClient instance
        image_path: Path to the image file
        question: Specific question to answer

    Returns:
        Answer extracted from the image
    """
    image_data_uri = encode_image_to_data_uri(Path(image_path_n))
    image_data_uri_n_1 = encode_image_to_data_uri(Path(image_path_n_1))
    image_data_uri_n_plus_1 = encode_image_to_data_uri(Path(image_path_n_plus_1))

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": METADATA_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                    {"type": "image_url", "image_url": {"url": image_data_uri_n_1}},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_uri_n_plus_1},
                    },
                ],
            },
        ],
        response_format=None,
    )

    return resp.choices[0].message.content


if __name__ == "__main__":
    litellm_client = LitellmClient(model_name="openai/gpt-4o")

    metadata = extract_metadata_from_page(
        litellm_client,
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/short/page_35/page_35_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/short/page_36/page_36_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/short/page_37/page_37_full.png",
    )

    print(metadata)
