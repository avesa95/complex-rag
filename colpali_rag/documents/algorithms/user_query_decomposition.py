import json

from colpali_rag.documents.prompts.query_decomposition import (
    USER_QUESTION_DECOMPOSITION_PROMPT,
)
from colpali_rag.documents.schemas import QueryDecompositionResponse
from colpali_rag.llm.litellm_client import LitellmClient


def user_query_decomposition(litellm_client: LitellmClient, user_question: str) -> str:
    resp = litellm_client.chat(
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant that decomposes a user's question into a list of sub-questions.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": USER_QUESTION_DECOMPOSITION_PROMPT.format(
                            user_question=user_question
                        ),
                    },
                ],
            },
        ],
        response_format=QueryDecompositionResponse,
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    from colpali_rag.llm.litellm_client import LitellmClient

    litellm_client = LitellmClient(model_name="openai/gpt-4o")
    user_question = "What sequence of checks should be performed if the engine starts but none of the hydraulic functions work?"
    questions = user_query_decomposition(litellm_client, user_question)

    for question in questions["decomposed_questions"]:
        print(question["sub_question"])
