from fastapi import APIRouter

from app.models.schemas import NLPAnalysisRequest, NLPAnalysisResult
from app.nlp import pipeline as nlp_pipeline

router = APIRouter(prefix="/nlp", tags=["nlp"])


@router.post("/analyze", response_model=NLPAnalysisResult)
def analyze(request: NLPAnalysisRequest):
    """Run the baseline NLP pipeline (spaCy NER + rule-based disruption
    classification) on free text. Does not touch the graph."""
    return nlp_pipeline.analyze_text(request.text)
