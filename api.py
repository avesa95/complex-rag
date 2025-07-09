import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from retrieval import ManufacturingRetrieval

# Configure logging
logging.basicConfig(
    level=logging.INFO, format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service Manual Q&A API",
    description="API for answering questions about service manuals using RAG",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'scratch' directory
app.mount("/scratch", StaticFiles(directory="scratch"), name="scratch")

# Initialize the retrieval system
retrieval = ManufacturingRetrieval()


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    references: Dict[str, Any]


@app.post("/answer", response_model=QuestionResponse)
async def answer_question(request: QuestionRequest):
    """
    Answer a question about the service manual using RAG.

    Args:
        request: QuestionRequest containing the user's question

    Returns:
        QuestionResponse containing the answer and references
    """
    try:
        logger.info(f"Received question: {request.question}")

        # Retrieve relevant points
        relevant_points = retrieval.retrieve_relevant_points(request.question)

        # Get answer with references
        result = retrieval.answer_question(relevant_points, request.question)

        logger.info("Successfully generated answer")

        return QuestionResponse(
            answer=result["answer"], references=result["references"]
        )

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Service Manual Q&A API is running"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Service Manual Q&A API",
        "version": "1.0.0",
        "endpoints": {
            "POST /answer": "Answer a question about the service manual",
            "GET /health": "Health check",
            "GET /": "API information",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
