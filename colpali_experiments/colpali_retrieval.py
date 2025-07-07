"""
Simple integration with your current code
Just replace your current workflow with this
"""

import base64
from pathlib import Path

from colpali_rag.llm.litellm_client import LitellmClient
from colpali_rag.qdrant_manager import QdrantManager


def encode_image_to_data_uri(image_path: Path) -> str:
    """
    Read a PNG (or other) image from disk and return a data URI string.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{base64_image}"


def answer_question_from_manual(
    litellm_client: LitellmClient, image_path: str, question: str
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
    image_data_uri = encode_image_to_data_uri(Path(image_path))

    # Improved prompt for your specific use case
    prompt = f"""You are reading a technical manual page. Please answer this specific question based on what you see in the image.

QUESTION: {question}

INSTRUCTIONS:
1. Read all text visible in this manual page carefully
2. Look for information that directly answers the question
3. If you find the answer:
   - Quote the exact text from the manual
   - Provide a clear, specific answer
   - Include any relevant details like frequencies, procedures, or warnings
4. If you find related information but not the exact answer:
   - Explain what related information you found
   - Indicate what might be missing
5. If this page doesn't contain the answer:
   - Say "This page does not contain the answer to this question"
   - Briefly mention what information IS on this page

Focus on maintenance schedules, operating procedures, safety instructions, and technical specifications.

Be precise and factual. Quote the manual text when possible."""

    resp = litellm_client.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_uri}},
                ],
            },
        ],
        response_format=None,
    )

    return resp.choices[0].message.content


# Your current workflow - Enhanced version
if __name__ == "__main__":
    # Initialize everything
    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    qdrant_manager = QdrantManager(collection_name="colpali_docs_index")

    # Your question
    question = "My front axle brakes will not release in my JLG 1055. How do I get them to release?"

    print("🔍 Enhanced RAG Pipeline")
    print(f"❓ Question: {question}")
    print("=" * 60)

    # Step 1: Retrieve with ColPali (your current working code)
    print("📖 Step 1: Retrieving relevant pages...")
    results = qdrant_manager.search_similar_documents_text(
        query_text=question,
        limit=20,
        vector_name="initial",  # or "cascade" if you're using enhanced_search
    )

    print(f"✅ Found {len(results)} relevant pages")
    for i, result in enumerate(results, 1):
        print(
            f"  {i}. Page {result['payload']['page_number']} (Score: {result['score']:.4f})"
        )

    # Step 2: Read the top pages with VLM
    print("\n🤖 Step 2: Reading pages with GPT-4V...")

    images_folder = "scratch/service_manual_long"

    # Try the top 3 pages
    for i, result in enumerate(results, 1):
        page_number = result["payload"]["page_number"]
        score = result["score"]

        # Try to find the image file
        page_dir = f"{images_folder}/page_{page_number}"
        image_path = f"{page_dir}/page_{page_number}_full.png"

        if Path(image_path).exists():
            print(f"\n📄 Reading Page {page_number} (Score: {score:.4f})")
            print("-" * 40)

            answer = answer_question_from_manual(
                litellm_client=litellm_client, image_path=image_path, question=question
            )

            print(f"Answer from Page {page_number}:")
            print(answer)
            print("-" * 40)

            # If we got a good answer, we can stop
            if "does not contain" not in answer.lower():
                print(f"\n✅ Found the answer on Page {page_number}!")
                break
        else:
            print(f"⚠️ Image not found for page {page_number}: {image_path}")

    print("\n" + "=" * 60)
    print("🎯 RAG COMPLETE!")
    print("=" * 60)
