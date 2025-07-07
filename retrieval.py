from colpali_rag.documents.algorithms.map_question_chapter import map_question_chapter
from colpali_rag.llm.litellm_client import LitellmClient
from colpali_rag.retrieval.strategies.custom_qdrant.retriever import (
    RetrievalConfig,
)
from colpali_rag.retrieval.strategies.custom_qdrant.search.hybrid import HybridRetriever
from settings import settings

litellm_client = LitellmClient(model_name="openai/gpt-4o")


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
- If you use a table, say “see table in Section 2.5.1”.
- If no clear answer exists, explain why.

Now answer the user’s question based on the content above.
"""


class ManufacturingRetrieval:
    def __init__(self):
        self.config = RetrievalConfig(
            qdrant_host=settings.QDRANT_URL,
            qdrant_api_key=settings.QDRANT_API_KEY,
        )
        self.retriever = HybridRetriever(self.config)

    def retrieve_relevant_points(self, user_question: str):
        sections = []
        possible_chapters = map_question_chapter(litellm_client, user_question)
        for section in possible_chapters["matched_sections"]:
            sections.append(section["section_number"])

        results = self.retriever.retrieve(
            query=user_question,
            collection_name="service_manual_pages",
            score_threshold=4,
            limit=6,
        )
        return results

    def answer_question(self, relevant_points: str, user_question: str):
        resp = litellm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical assistant that answers a user's question based on the relevant points from a service manual.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANSWER_QUESTION_PROMPT.format(
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
    user_question = "What sequence of checks should be performed if the engine starts but none of the hydraulic functions work?"

    retrieval = ManufacturingRetrieval()

    relevant_points = retrieval.retrieve_relevant_points(user_question)
    print(relevant_points)

    answer = retrieval.answer_question(relevant_points, user_question)
    print(answer)
