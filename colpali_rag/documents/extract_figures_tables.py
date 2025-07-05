import logging
from pathlib import Path

import fitz
from docling.datamodel.document import PictureItem, TextItem

from colpali_rag.ocr.docling_ocr import (
    DoclingOCRStrategy,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def export_figures_tables_and_text(
    pdf_path: str,
    output_dir: str = "scratch",
):
    logger.info(f"Starting extraction from PDF: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")

    ocr_strategy = DoclingOCRStrategy()

    with fitz.open(pdf_path) as pdf_doc:
        total_pages = pdf_doc.page_count
        logger.info(f"Total pages: {total_pages}")

    # Global counters that don't reset between pages
    global_table_idx = 0
    global_picture_idx = 0
    global_text_blocks = 0

    for page_num in range(1, total_pages + 1):
        logger.info(f"Processing page {page_num}")
        doc = ocr_strategy.perform_ocr_on_pdf_docling_document(
            pdf_path, page_range=[page_num, page_num]
        )

        doc_name = Path(pdf_path).stem
        output_path = Path(output_dir) / doc_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Create page folder
        page_folder = output_path / f"page_{page_num}"
        tables_folder = page_folder / "tables"
        images_folder = page_folder / "images"
        text_folder = page_folder / "text"
        tables_folder.mkdir(parents=True, exist_ok=True)
        images_folder.mkdir(parents=True, exist_ok=True)
        text_folder.mkdir(parents=True, exist_ok=True)

        # Save full page as image
        with fitz.open(pdf_path) as pdf_doc:
            page = pdf_doc[page_num - 1]  # 0-indexed
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )  # 2x zoom for better quality
            full_page_file = page_folder / f"page_{page_num}_full.png"
            pix.save(str(full_page_file))
            logger.info(f"Saved full page: {full_page_file}")

        # Export tables as HTML (and PNG)
        logger.info(f"Found {len(doc.tables)} tables on page {page_num}")
        for table in doc.tables:
            global_table_idx += 1
            logger.info(f"Exporting table {global_table_idx} from page {page_num}")

            html = table.export_to_html(doc=doc)
            html_file = tables_folder / f"table-{global_table_idx}.html"
            html_file.write_text(html)
            logger.info(f"Saved table HTML: {html_file}")

            # Optional: PNG preview
            img = table.get_image(doc)
            png_file = tables_folder / f"table-{global_table_idx}.png"
            img.save(png_file, "PNG")
            logger.info(f"Saved table PNG: {png_file}")

        # Export figures
        logger.info(f"Starting figure extraction for page {page_num}...")
        for item, _ in doc.iterate_items():
            if isinstance(item, PictureItem):
                global_picture_idx += 1

                logger.info(
                    f"Exporting image {global_picture_idx} from page {page_num}"
                )

                img = item.get_image(doc)
                img_file = images_folder / f"image-{global_picture_idx}.png"
                img.save(img_file, "PNG")
                logger.info(f"Saved image: {img_file}")

        # Export text blocks - unify all text from the page into one file
        logger.info(f"Starting text extraction for page {page_num}...")
        page_text_blocks = []
        text_block_count = 0

        for item, _ in doc.iterate_items():
            if isinstance(item, TextItem):
                global_text_blocks += 1
                text_block_count += 1

                logger.info(f"Found text block {text_block_count} on page {page_num}")

                # Extract text content
                text_content = item.text if hasattr(item, "text") else str(item)
                page_text_blocks.append(text_content)

        # Save all text blocks from this page into a single file
        if page_text_blocks:
            unified_text = "\n\n".join(page_text_blocks)
            txt_file = text_folder / f"page_{page_num}_text.txt"
            txt_file.write_text(unified_text, encoding="utf-8")
            logger.info(
                f"Saved unified text file: {txt_file} ({text_block_count} blocks)"
            )
        else:
            logger.info(f"No text blocks found on page {page_num}")

        logger.info(
            f"Page {page_num} complete! Exported {len(doc.tables)} tables, "
            f"{global_picture_idx} total images, and {global_text_blocks} "
            f"total text blocks so far"
        )

    logger.info(
        f"All pages processed successfully! Total: {global_table_idx} tables, "
        f"{global_picture_idx} images, and {global_text_blocks} text blocks"
    )


# Keep the old function name for backward compatibility
def export_figures_and_tables(
    pdf_path: str,
    output_dir: str = "scratch",
):
    """Legacy function - now calls the enhanced version"""
    return export_figures_tables_and_text(pdf_path, output_dir)


if __name__ == "__main__":
    pdf_path = "/Users/vesaalexandru/Workspaces/cube/complex-rag/data/short.pdf"
    export_figures_tables_and_text(pdf_path, output_dir="scratch")
