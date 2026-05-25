import json
from pathlib import Path

from recommendation_service import RecommendationService
from schemas import UIResponse


SAMPLES_DIR = Path("samples")
SCHEMA_PATH = Path("ui_response.schema.json")


SAMPLE_QUERIES = {
    "retinol_query_ui_response.json": "tell me retinols to use . My current age is 20",
    "sunscreen_query_ui_response.json": "oily skin sunscreen for summer under 800",
    "pregnancy_safe_ui_response.json": "pregnancy safe dark spot treatment without retinol",
}


def write_schema():
    schema = UIResponse.model_json_schema()
    SCHEMA_PATH.write_text(json.dumps(schema, indent=4, ensure_ascii=False), encoding="utf-8")
    return SCHEMA_PATH


def write_samples():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    service = RecommendationService()
    written = []

    for index, (filename, query) in enumerate(SAMPLE_QUERIES.items(), start=1):
        payload = service.recommend(
            query,
            use_saved_history=False,
            save_history=False,
            generate_visualization=False,
        )
        ui_response = service.build_ui_response(payload, request_id=f"sample_{index:02d}")
        path = SAMPLES_DIR / filename
        path.write_text(json.dumps(ui_response, indent=4, ensure_ascii=False), encoding="utf-8")
        written.append(path)

    no_result = {
        "schema_version": "1.0",
        "response_type": "ui_components",
        "request_id": "sample_empty",
        "generated_at": "2026-05-22T00:00:00+00:00",
        "query": {
            "raw": "no matching skincare product",
            "normalized": "no matching skincare product",
            "intent": "search",
            "language": "english",
        },
        "detected_context": {
            "skin_type": None,
            "user_age": None,
            "age_group": None,
            "product_type": None,
            "skin_concerns": [],
            "requested_ingredients": [],
            "avoided_ingredients": [],
            "safety_flags": {
                "pregnancy_safe_required": False,
                "vegan_preference": False,
                "cruelty_free_preference": False,
            },
        },
        "summary": {
            "component_count": 1,
            "primary_component_id": "no-results",
            "safety_severity": None,
        },
        "components": [
            {
                "component_id": "no-results",
                "component_type": "empty_state",
                "title": "No exact match found",
                "priority": 1,
                "layout": "centered_message",
                "message": "Showing fallback skincare picks when available.",
            }
        ],
    }
    no_result = UIResponse.model_validate(no_result).model_dump(mode="json")
    path = SAMPLES_DIR / "no_result_ui_response.json"
    path.write_text(json.dumps(no_result, indent=4, ensure_ascii=False), encoding="utf-8")
    written.append(path)

    return written


def main():
    schema_path = write_schema()
    sample_paths = write_samples()
    print(f"Wrote {schema_path}")
    for path in sample_paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
