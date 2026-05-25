from pathlib import Path

from catalog_engine import CatalogEngine
from data_visualizer import DEFAULT_OUTPUT as DEFAULT_VISUALIZATION_OUTPUT
from data_visualizer import visualize_dataset
from history_manager import DEFAULT_HISTORY_PATH
from history_manager import load_user_history
from history_manager import merge_histories
from history_manager import update_user_history
from intent_extractor import IntentExtractor
from schemas import RecommendationResponse
from ui_component_builder import UIComponentBuilder
from ui_response_builder import UIResponseBuilder


class RecommendationService:
    """Application service used by CLI, tests, and FastAPI.

    Keeping orchestration here prevents API and CLI code from drifting into two
    different recommendation flows.
    """

    def __init__(self, dataset_path=None, history_store=DEFAULT_HISTORY_PATH):
        self.dataset_path = Path(dataset_path or CatalogEngine.DEFAULT_DATASET)
        self.history_store = Path(history_store)
        self.extractor = IntentExtractor(catalog_path=self.dataset_path)
        self.engine = CatalogEngine(self.dataset_path)
        self.ui_component_builder = UIComponentBuilder()
        self.ui_response_builder = UIResponseBuilder()

    def recommend(
        self,
        query,
        history=None,
        use_saved_history=True,
        save_history=False,
        generate_visualization=False,
        visualization_output=DEFAULT_VISUALIZATION_OUTPUT,
    ):
        merged_history = {}
        if use_saved_history:
            merged_history = load_user_history(self.history_store)
        merged_history = merge_histories(merged_history, history or {})

        visualization_path = None
        if generate_visualization:
            visualization_path = visualize_dataset(self.dataset_path, visualization_output)

        profile = self.extractor.extract(query, history=merged_history)
        recommendation = self.engine.recommend(profile)
        components = self.ui_component_builder.build(profile, recommendation)

        if use_saved_history and save_history:
            update_user_history(merged_history, query, profile, recommendation["catalogs"], self.history_store)

        payload = {
            "profile": profile,
            **recommendation,
            "components": components,
        }
        if visualization_path:
            payload["visualization_path"] = str(visualization_path)

        return RecommendationResponse.model_validate(payload).model_dump(mode="json")

    def build_ui_response(self, recommendation_payload, request_id=None):
        return self.ui_response_builder.build(recommendation_payload, request_id=request_id)

    def recommend_ui(self, *args, request_id=None, **kwargs):
        recommendation_payload = self.recommend(*args, **kwargs)
        return self.build_ui_response(recommendation_payload, request_id=request_id)
