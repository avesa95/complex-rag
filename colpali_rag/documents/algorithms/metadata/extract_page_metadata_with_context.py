from pathlib import Path

from colpali_rag.core.utils import encode_image_to_data_uri, read_json_file
from colpali_rag.documents.algorithms.metadata.prompts import METADATA_PROMPT
from colpali_rag.llm.litellm_client import LitellmClient


def extract_metadata_from_page(
    litellm_client: LitellmClient,
    image_path_n: str,
    image_path_n_1: str,
    image_path_n_plus_1: str,
    metadata_page_n_1_path: str,
    metadata_page_n_path: str,
    metadata_page_n_plus_1_path: str,
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

    metadata_page_n_1 = str(read_json_file(Path(metadata_page_n_1_path)))
    metadata_page_n = str(read_json_file(Path(metadata_page_n_path)))
    metadata_page_n_plus_1 = str(read_json_file(Path(metadata_page_n_plus_1_path)))

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": METADATA_PROMPT.replace(
                            "{metadata_page_n_1}", metadata_page_n_1
                        )
                        .replace("{metadata_page_n}", metadata_page_n)
                        .replace("{metadata_page_n_plus_1}", metadata_page_n_plus_1),
                    },
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
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_35/page_35_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_36/page_36_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_37/page_37_full.png",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_35/metadata_page_35.json",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_36/metadata_page_36.json",
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_37/metadata_page_37.json",
    )

    print(metadata)
