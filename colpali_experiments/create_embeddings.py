"""
Create Document Embeddings

This module provides functionality to convert PDF documents into embeddings
using a pre-trained model.
"""

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from colpali_rag.convert_pages import convert_pdf_to_images


def create_document_embeddings(pdf_dir, model, processor, batch_size=2):
    """
    Converts all PDFs in a directory into embeddings with metadata.

    Args:
        pdf_dir (str): Directory containing PDF files.
        model: Pre-trained model for generating embeddings.
        processor: Preprocessor for the model (e.g., to process images).
        batch_size (int): Batch size for inference.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
            - "embedding": The embedding tensor.
            - "doc_id": The document ID (int).
            - "page_id": The page index within the document.
            - "file_name": The name of the source PDF file.
    """
    all_images = convert_pdf_to_images(pdf_dir)
    all_embeddings_with_metadata = []

    for doc_id, (file_name, pdf_images) in enumerate(all_images.items()):
        dataloader = DataLoader(
            dataset=pdf_images,
            batch_size=batch_size,
            shuffle=False,
            collate_fn=lambda x: processor.process_images(x),
        )

        page_counter = 0
        for batch in tqdm(dataloader, desc=f"Processing {file_name}"):
            with torch.no_grad():
                batch = {k: v.to(model.device) for k, v in batch.items()}
                batch_embeddings = model(**batch)
                batch_embeddings = list(torch.unbind(batch_embeddings.to("cpu")))

                for embedding in batch_embeddings:
                    all_embeddings_with_metadata.append(
                        {
                            "embedding": embedding,
                            "doc_id": doc_id,
                            "page_id": page_counter,
                            "file_name": file_name,  # Correctly use the file name
                        }
                    )
                    page_counter += 1

    return all_embeddings_with_metadata
