import base64
import json
from pathlib import Path


def encode_image_to_data_uri(image_path: Path) -> str:
    """
    Read a PNG (or other) image from disk and return a data URI string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_image}"


def read_json_file(json_path: Path) -> str:
    """
    Read a JSON file from disk and return the contents as a string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(json_path, "r") as f:
        return json.dumps(json.dumps(json.load(f)))


if __name__ == "__main__":
    import json

    z = read_json_file(
        Path(
            "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/scratch/service_manual_long/page_35/metadata_page_35.json"
        )
    )
    print(z)
