from fastapi import FastAPI

from catalog_engine import CatalogEngine
from data_contracts import validate_catalog_dataset
from recommendation_service import RecommendationService
from schemas import DataValidationReport
from schemas import RecommendationRequest
from schemas import RecommendationResponse
from schemas import UIResponse


app = FastAPI(
    title="Skincare Recommendation Backend",
    version="1.0.0",
    description="Backend API for skincare recommendations, routine building, and safety checks.",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "skincare-recommender"}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    service = RecommendationService()
    return service.recommend(
        query=request.query,
        history=request.history,
        use_saved_history=request.use_saved_history,
        save_history=request.save_history,
        generate_visualization=request.generate_visualization,
    )


@app.post("/recommend-ui", response_model=UIResponse)
def recommend_ui(request: RecommendationRequest):
    service = RecommendationService()
    return service.recommend_ui(
        query=request.query,
        history=request.history,
        use_saved_history=request.use_saved_history,
        save_history=request.save_history,
        generate_visualization=request.generate_visualization,
    )


@app.get("/validate-data", response_model=DataValidationReport)
def validate_data():
    return validate_catalog_dataset(CatalogEngine.DEFAULT_DATASET)
