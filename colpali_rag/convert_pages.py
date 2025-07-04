# vison language models

import os

import torch
from pdf2image import convert_from_path

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


def convert_pdf_to_images(pdf_dir):
    """
    Converts all PDFs in a directory to images.

    Args:
        pdf_dir (str): Path to the directory containing PDFs.

    Returns:
        dict: A dictionary where keys are file names (without extension),
              and values are lists of images (one list per PDF).
    """
    pdf_list = [pdf for pdf in os.listdir(pdf_dir) if pdf.endswith(".pdf")]
    all_images = {}

    for pdf_file in pdf_list:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        pdf_images = convert_from_path(pdf_path)
        all_images[pdf_file] = pdf_images  # Use file name as key

    return all_images


def convert_single_pdf_to_images(pdf_path):
    """
    Converts a single PDF file to images.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list: List of images from the PDF.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pdf_images = convert_from_path(pdf_path)
    return pdf_images


def save_images_to_disk(images, output_dir):
    """
    Saves images to disk.

    Args:
        images (list): List of images to save.
        output_dir (str): Path to the directory to save the images.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for i, image in enumerate(images):
        image.save(os.path.join(output_dir, f"{i}.png"))


if __name__ == "__main__":
    # For a single PDF file
    pdf_path = "/Users/vesaalexandru/Workspaces/cube/complex-rag/31211033 - JLG 642, 742, 943, 1043, 1055, 1255-1_removed_removed_removed.pdf"

    # Convert single PDF to images
    images = convert_single_pdf_to_images(pdf_path)
    print(f"Converted {len(images)} pages from PDF")

    # Save images to disk
    save_images_to_disk(images, "images")
    print("Images saved to 'images' directory")
