import base64
from pathlib import Path


def encode_image_to_data_uri(image_path: Path) -> str:
    """
    Read a PNG (or other) image from disk and return a data URI string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_image}"
