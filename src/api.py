from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from src.app_state import AppState
from src.pipeline import ask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str
    ground_truth_pmids: list[str] | None = None


class QueryResponse(BaseModel):
    answer: dict
    metrics: dict


# Lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting Med-RAG API...")
    try:
        app.state.med_rag = AppState()
        app.state.med_rag.build_index()
        logger.info("Index built successfully")
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        raise

    yield

    logger.info("Shutting down Med-RAG API...")


app = FastAPI(
    title="Med-RAG API",
    description="Retrieval-Augmented Generation system for evidence-based medical Q&A",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "index_ready": app.state.med_rag.store is not None
    }


@app.post("/query", response_model=QueryResponse)
def query_medrag(request: QueryRequest):
    """
    Answer a medical question using retrieval-augmented generation.

    Args:
        request: QueryRequest containing the question and optional ground truth PMIDs

    Returns:
        QueryResponse with answer and evaluation metrics
    """
    try:
        if app.state.med_rag.store is None:
            raise HTTPException(
                status_code=503,
                detail="Index not ready. Please wait for startup to complete."
            )

        logger.info(f"Processing query: {request.question}")

        result = ask(
            question=request.question,
            store=app.state.med_rag.store,
            embedder=app.state.med_rag.embedder,
            llm_client=app.state.med_rag.llm_client,
            ground_truth_pmids=request.ground_truth_pmids
        )

        return QueryResponse(
            answer=result["result"].dict(),
            metrics=result["metrics"]
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))