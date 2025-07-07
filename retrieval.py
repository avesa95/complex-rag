import logging
from pathlib import Path

from colpali_rag.documents.algorithms.user_query_decomposition import (
    user_query_decomposition,
)
from colpali_rag.llm.litellm_client import LitellmClient
from colpali_rag.retrieval.strategies.custom_qdrant.retriever import (
    RetrievalConfig,
)
from colpali_rag.retrieval.strategies.custom_qdrant.search.hybrid import (
    HybridRetriever,
)
from settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

litellm_client = LitellmClient(model_name="anthropic/claude-3-7-sonnet-20250219")


ANSWER_QUESTION_PROMPT = """
You are a highly technical assistant. The user has a question related to a service manual.

You have access to a collection of **extracted points** from the manual, including text blocks, tables (as HTML), and figures (described and labeled). Each point comes with detailed metadata, such as section titles, component type, applicable models, and cross-page relationships.

Your goal is to:
1. **Understand the user question** and identify the most relevant point(s).
2. **Extract an accurate answer** based only on those points.
3. **If necessary, refer to tables, diagrams, or instructions** using their section or figure identifiers.
4. **Preserve factual and technical fidelity. Do not guess.** If the answer is unclear or missing, say so.

---

### User Question:
{user_question}

---

### Relevant Points (from the manual):
{relevant_points}

---

### Instructions for you:
- Only use the information from the relevant points.
- When referencing something visual (like a diagram), use the figure label, e.g., "see Figure 3.2".
- If you use a table, say "see table in Section 2.5.1".
- If no clear answer exists, explain why.

Now answer the user's question based on the content above.
"""

ANSWER_QUESTION_PROMPT_GEMINI = """
You are a highly technical assistant specialized in interpreting service manuals.

You are given:
- A **user question**, which may contain multiple components or sub-questions.
- A list of **relevant points**, each derived from the manual (text blocks, tables in HTML, or described figures).
- Each point includes metadata: section title, component type, applicable models, and cross-references.

Your task is to **analyze all relevant points**, extract accurate, fact-based answers,
and **clearly address each aspect of the user's question**.

---

### User Question:
{user_question}

---

### Relevant Points:
{relevant_points}

---

### Instructions:

1. **Carefully read the user's question** and determine whether it contains one or
more sub-questions or topics.
2. **Structure your answer** to clearly address each part of the question. You may
number or bullet the responses if needed.
3. **Base your response strictly on the provided points.**
   - Do not speculate or hallucinate.
   - If a claim or value is not found in the content, clearly state:
     _"The manual does not provide enough information to answer this part of the question."_ 
4. **Cite sources when relevant**:
   - Refer to figures as _"See Figure 3.2"_
   - Refer to tables as _"see table in Section 2.5.1"_ or
     _"refer to the HTML table under Axle Specifications"_
5. **Preserve the technical language and specificity of the original manual**.
   Your answer should be professional, precise, and suitable for a technician or
   engineer.
6. **If multiple models are mentioned**, explicitly differentiate them in your answer.
7. **If useful, summarize multiple references** (e.g., if capacities differ slightly
   across models, summarize differences clearly and concisely).

---

Now generate the best possible answer using only the content above.
"""


def correlate_references_with_files(
    references, scratch_path="scratch/service_manual_long"
):
    """
    Correlate table and figure references with their actual files on disk.

    Args:
        references: Dictionary with 'tables' and 'figures' lists
        scratch_path: Path to the scratch directory containing page folders

    Returns:
        Updated references with file paths added
    """
    scratch_dir = Path(scratch_path)

    # Correlate tables
    for table in references["tables"]:
        page_number = table.get("page_number")
        element_id = table.get("element_id")

        if page_number and element_id:
            # Construct file paths
            page_dir = scratch_dir / f"page_{page_number}"
            table_png_path = page_dir / "tables" / f"{element_id}.png"
            table_html_path = page_dir / "tables" / f"{element_id}.html"

            # Check if files exist and add paths
            if table_png_path.exists():
                table["png_file"] = str(table_png_path)
            if table_html_path.exists():
                table["html_file"] = str(table_html_path)

    # Correlate figures
    for figure in references["figures"]:
        page_number = figure.get("page_number")
        label = figure.get("label")

        if page_number and label:
            # Construct file paths
            page_dir = scratch_dir / f"page_{page_number}"

            # Try different naming conventions for figure files
            possible_paths = [
                page_dir / "images" / f"{label}.png",  # Original label
                page_dir
                / "images"
                / f"image-{page_number}-{label.split('-')[-1]}.png",  # Convert figure-X-Y to image-X-Y
            ]

            # Check if any of the possible paths exist
            for figure_png_path in possible_paths:
                if figure_png_path.exists():
                    figure["png_file"] = str(figure_png_path)
                    break

    return references


def deduplicate_references(references):
    """
    Remove duplicate tables and figures based on their unique identifiers.

    Args:
        references: Dictionary with 'tables' and 'figures' lists

    Returns:
        Dictionary with deduplicated 'tables' and 'figures' lists
    """
    # Deduplicate tables based on element_id and page_number
    seen_tables = set()
    unique_tables = []

    for table in references["tables"]:
        table_key = f"{table.get('element_id')}_{table.get('page_number')}"
        if table_key not in seen_tables:
            seen_tables.add(table_key)
            unique_tables.append(table)

    # Deduplicate figures based on label and page_number
    seen_figures = set()
    unique_figures = []

    for figure in references["figures"]:
        figure_key = f"{figure.get('label')}_{figure.get('page_number')}"
        if figure_key not in seen_figures:
            seen_figures.add(figure_key)
            unique_figures.append(figure)

    return {"tables": unique_tables, "figures": unique_figures}


def extract_tables_and_figures_references(relevant_points):
    """
    Extract all tables and figures as references from the relevant points structure.

    Args:
        relevant_points: Dictionary containing retrieved points with metadata

    Returns:
        Dictionary with 'tables' and 'figures' lists containing reference information
    """
    all_tables = []
    all_figures = []

    # Process each sub-question's results
    for sub_question, results in relevant_points.items():
        for result in results:
            # Extract tables and figures from content_elements
            content_elements = result.get("content_elements", [])
            for element in content_elements:
                if element.get("type") == "table":
                    # Only add table if it has a proper identifier
                    element_id = element.get("element_id")
                    if element_id and element_id != "None":
                        table_ref = {
                            "sub_question": sub_question,
                            "element_id": element_id,
                            "page_number": result.get("page_number"),
                        }
                        all_tables.append(table_ref)

                elif element.get("type") == "figure":
                    # Only add figure if it has a proper identifier
                    figure_id = element.get("figure_id")
                    if figure_id and figure_id != "None":
                        figure_ref = {
                            "sub_question": sub_question,
                            "label": figure_id,
                            "page_number": result.get("page_number"),
                        }
                        all_figures.append(figure_ref)

            # Extract flattened tables if available
            flattened_tables = result.get("flattened_tables", [])
            for table in flattened_tables:
                table_id = table.get("table_id")
                if table_id and table_id != "None":
                    table_ref = {
                        "sub_question": sub_question,
                        "element_id": table_id,
                        "page_number": result.get("page_number"),
                    }
                    all_tables.append(table_ref)

            # Extract table metadata if available
            table_metadata = result.get("table_metadata", [])
            for table in table_metadata:
                table_id = table.get("table_id")
                if table_id and table_id != "None":
                    table_ref = {
                        "sub_question": sub_question,
                        "element_id": table_id,
                        "page_number": result.get("page_number"),
                    }
                    all_tables.append(table_ref)

            # Extract figures from content_summary if available
            content_summary = result.get("content_summary", {})
            figures = content_summary.get("figures", [])
            for figure in figures:
                # Only add figure if it has a proper identifier
                if figure and figure != "None":
                    figure_ref = {
                        "sub_question": sub_question,
                        "label": figure,
                        "page_number": result.get("page_number"),
                    }
                    all_figures.append(figure_ref)

            # Extract related figures from within_page_relations
            content_elements = result.get("content_elements", [])
            for element in content_elements:
                within_page_relations = element.get("within_page_relations", {})
                related_figures = within_page_relations.get("related_figures", [])
                for figure in related_figures:
                    # Only add figure if it has a proper label
                    label = figure.get("label")
                    if label and label != "None":
                        figure_ref = {
                            "sub_question": sub_question,
                            "label": label,
                            "page_number": result.get("page_number"),
                        }
                        all_figures.append(figure_ref)

    references = {"tables": all_tables, "figures": all_figures}

    # Correlate with actual files on disk
    references = correlate_references_with_files(references)

    # Deduplicate references to remove duplicates across sub-questions
    references = deduplicate_references(references)

    return references


class ManufacturingRetrieval:
    def __init__(self):
        logger.info("Initializing ManufacturingRetrieval")
        self.config = RetrievalConfig(
            qdrant_host=settings.QDRANT_URL,
            qdrant_api_key=settings.QDRANT_API_KEY,
        )
        self.retriever = HybridRetriever(self.config)
        logger.info("ManufacturingRetrieval initialized successfully")

    def retrieve_relevant_points(self, user_question: str):
        # sections = []
        # possible_chapters = map_question_chapter(litellm_client, user_question)
        # for section in possible_chapters["matched_sections"]:
        #     sections.append(section["section_number"])

        questions = user_query_decomposition(litellm_client, user_question)

        all_questions_points = {}

        for question in questions["decomposed_questions"]:
            results = self.retriever.retrieve(
                query=question["sub_question"],
                collection_name="service_manual_pages",
                score_threshold=4,
                limit=4,
            )
            all_questions_points[question["sub_question"]] = results

        return all_questions_points

    def answer_question(self, relevant_points, user_question: str):
        # Extract references
        references = extract_tables_and_figures_references(relevant_points)

        # Get the answer
        resp = litellm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a technical assistant that answers a user's "
                        "question based on the relevant points from a service manual."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANSWER_QUESTION_PROMPT_GEMINI.format(
                                user_question=user_question,
                                relevant_points=relevant_points,
                            ),
                        },
                    ],
                },
            ],
            response_format=None,
            temperature=0.0,
            max_tokens=10000,
        )
        answer = resp.choices[0].message.content

        return {"answer": answer, "references": references}


if __name__ == "__main__":
    import json

    user_question = "Let's discuss about Engine exhaust system"

    retrieval = ManufacturingRetrieval()

    relevant_points = retrieval.retrieve_relevant_points(user_question)

    # Get answer with references
    result = retrieval.answer_question(relevant_points, user_question)

    with open("result.json", "w") as f:
        json.dump(result, f)
