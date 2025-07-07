import logging

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
                    table_ref = {
                        "element_id": element.get("element_id"),
                        "title": element.get("title"),
                        "summary": element.get("summary"),
                        "page_number": result.get("page_number"),
                        "section_title": result.get("section_title"),
                        "subsection_title": result.get("subsection_title"),
                        "table_id": element.get("table_id"),
                        "table_file": element.get("table_file"),
                        "table_image": element.get("table_image"),
                        "flattened_content": element.get("flattened_content"),
                        "html_content": element.get("html_content"),
                        "sub_question": sub_question,
                    }
                    all_tables.append(table_ref)

                elif element.get("type") == "figure":
                    # Only add figure if it has a proper identifier
                    figure_id = element.get("figure_id")
                    if figure_id and figure_id != "None":
                        figure_ref = {
                            "element_id": element.get("element_id"),
                            "title": element.get("title"),
                            "summary": element.get("summary"),
                            "page_number": result.get("page_number"),
                            "section_title": result.get("section_title"),
                            "subsection_title": result.get("subsection_title"),
                            "figure_id": figure_id,
                            "figure_file": element.get("figure_file"),
                            "sub_question": sub_question,
                        }
                        all_figures.append(figure_ref)

            # Extract flattened tables if available
            flattened_tables = result.get("flattened_tables", [])
            for table in flattened_tables:
                table_ref = {
                    "table_id": table.get("table_id"),
                    "html_file": table.get("html_file"),
                    "html_content": table.get("html_content"),
                    "flattened_content": table.get("flattened_content"),
                    "page_number": result.get("page_number"),
                    "section_title": result.get("section_title"),
                    "subsection_title": result.get("subsection_title"),
                    "sub_question": sub_question,
                }
                all_tables.append(table_ref)

            # Extract table metadata if available
            table_metadata = result.get("table_metadata", [])
            for table in table_metadata:
                table_ref = {
                    "table_id": table.get("table_id"),
                    "title": table.get("title"),
                    "summary": table.get("summary"),
                    "keywords": table.get("keywords", []),
                    "entities": table.get("entities", []),
                    "component_type": table.get("component_type"),
                    "model_name": table.get("model_name"),
                    "application_context": table.get("application_context", []),
                    "related_figures": table.get("related_figures", []),
                    "table_file": table.get("table_file"),
                    "table_image": table.get("table_image"),
                    "page_number": result.get("page_number"),
                    "section_title": result.get("section_title"),
                    "subsection_title": result.get("subsection_title"),
                    "sub_question": sub_question,
                }
                all_tables.append(table_ref)

            # Extract figures from content_summary if available
            content_summary = result.get("content_summary", {})
            figures = content_summary.get("figures", [])
            for figure in figures:
                # Only add figure if it has a proper identifier
                if figure and figure != "None":
                    figure_ref = {
                        "figure_id": figure,
                        "page_number": result.get("page_number"),
                        "section_title": result.get("section_title"),
                        "subsection_title": result.get("subsection_title"),
                        "sub_question": sub_question,
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
                            "label": label,
                            "description": figure.get("description"),
                            "page_number": result.get("page_number"),
                            "section_title": result.get("section_title"),
                            "subsection_title": result.get("subsection_title"),
                            "sub_question": sub_question,
                        }
                        all_figures.append(figure_ref)

    return {"tables": all_tables, "figures": all_figures}


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

    def answer_question(self, relevant_points: str, user_question: str):
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
        return resp.choices[0].message.content


if __name__ == "__main__":
    user_question = (
        "After replacing the electronic control module on a 943, what sequence "
        "of recalibrations is required for both frame tilt and joystick sensors "
        "to ensure accurate and safe operation? Include expected sensor ranges "
        "or offset behavior."
    )
    retrieval = ManufacturingRetrieval()

    relevant_points = retrieval.retrieve_relevant_points(user_question)

    # Extract tables and figures references
    references = extract_tables_and_figures_references(relevant_points)

    print("Tables found:")
    for table in references["tables"]:
        title = table.get("title", table.get("table_id", "Unknown"))
        page = table.get("page_number", "Unknown")
        print(f"  - {title} (Page {page})")

    print(f"\nFigures found ({len(references['figures'])} total):")
    for figure in references["figures"]:
        # Try different possible identifiers for figures
        figure_id = (
            figure.get("label")
            or figure.get("figure_id")
            or figure.get("element_id")
            or "Unknown"
        )
        page = figure.get("page_number", "Unknown")
        description = figure.get("description", "")
        if description:
            print(f"  - {figure_id} (Page {page}): {description}")
        else:
            print(f"  - {figure_id} (Page {page})")

    # answer = retrieval.answer_question(relevant_points, user_question)

    # with open("q&a.json", "a") as f:
    #     f.write(json.dumps({"question": user_question, "answer": answer}))

    # print(answer)
