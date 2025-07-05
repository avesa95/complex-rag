"""
ColPali RAG Model Management

Simple module for loading and managing ColPali vision-language models.
"""

import torch
from colpali_engine.models import ColPali, ColPaliProcessor


def get_device() -> torch.device:
    """Get the best available device (CUDA if available, else CPU)."""
    return torch.device("cuda" if torch.cuda.is_available() else "mps")


def load_colpali_model(
    model_name: str = "vidore/colpali-v1.2", torch_dtype: torch.dtype = torch.bfloat16
) -> tuple[ColPali, ColPaliProcessor]:
    """
    Load ColPali model and processor.

    Args:
        model_name: Name of the model to load
        torch_dtype: Torch data type for the model

    Returns:
        Tuple of (model, processor)

    Raises:
        RuntimeError: If model loading fails
    """
    try:
        device = get_device()

        # Load processor
        processor = ColPaliProcessor.from_pretrained(model_name)

        # Load model
        model = ColPali.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            device_map=device,
        ).eval()

        return model, processor

    except Exception as e:
        raise RuntimeError(f"Failed to load model {model_name}: {e}") from e
