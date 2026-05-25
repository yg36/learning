import argparse
import json
from pathlib import Path

from catalog_engine import CatalogEngine
from data_visualizer import DEFAULT_OUTPUT as DEFAULT_VISUALIZATION_OUTPUT
from history_manager import DEFAULT_HISTORY_PATH
from recommendation_service import RecommendationService


DEFAULT_OUTPUT = Path("output.json")
DEFAULT_UI_OUTPUT = Path("ui_response.json")


def parse_history(raw_history):
    if not raw_history:
        return {}

    raw_history = raw_history.strip()
    if not raw_history:
        return {}

    try:
        history_path = Path(raw_history)
        if history_path.exists():
            return json.loads(history_path.read_text(encoding="utf-8"))
    except OSError:
        pass

    try:
        return json.loads(raw_history)
    except json.JSONDecodeError:
        return {"previous_queries": [raw_history]}


def build_parser():
    parser = argparse.ArgumentParser(description="History-aware skincare catalog recommender")
    parser.add_argument("--dataset", default=str(CatalogEngine.DEFAULT_DATASET), help="Catalog CSV path")
    parser.add_argument("--query", help="Skincare query. If omitted, the app prompts for it.")
    parser.add_argument(
        "--history",
        help="Optional explicit history JSON/path/text to merge with saved chatbot history.",
    )
    parser.add_argument("--history-store", default=str(DEFAULT_HISTORY_PATH), help="Saved chatbot history JSON path")
    parser.add_argument("--no-history", action="store_true", help="Ignore saved chatbot history for this run")
    parser.add_argument("--no-save-history", action="store_true", help="Do not update saved chatbot history after this run")
    parser.add_argument(
        "--visualization-output",
        default=str(DEFAULT_VISUALIZATION_OUTPUT),
        help="PDF data visualization output path",
    )
    parser.add_argument("--skip-visualization", action="store_true", help="Skip PDF data visualization")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    parser.add_argument("--ui-output", default=str(DEFAULT_UI_OUTPUT), help="UI-only response JSON path")
    parser.add_argument("--skip-ui-output", action="store_true", help="Do not write UI-only response JSON")
    return parser


def main():
    args = build_parser().parse_args()

    user_query = args.query
    if not user_query:
        user_query = input("\nAsk skincare question:\n").strip()

    explicit_history = parse_history(args.history)

    service = RecommendationService(args.dataset, history_store=args.history_store)
    payload = service.recommend(
        query=user_query,
        history=explicit_history,
        use_saved_history=not args.no_history,
        save_history=not args.no_save_history,
        generate_visualization=not args.skip_visualization,
        visualization_output=args.visualization_output,
    )
    if payload.get("visualization_path"):
        print(f"\nSaved data visualization to {payload['visualization_path']}")

    profile = payload["profile"]
    recommendation = {
        "catalogs": payload["catalogs"],
        "routine": payload["routine"],
        "safety_summary": payload["safety_summary"],
    }
    results = recommendation["catalogs"]

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    ui_output_path = None
    if not args.skip_ui_output:
        ui_output = service.build_ui_response(payload)
        ui_output_path = Path(args.ui_output)
        ui_output_path.write_text(
            json.dumps(ui_output, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    print("\nDetected Profile:")
    print(json.dumps(profile, indent=4))
    print(f"\nSaved response to {output_path}")
    if ui_output_path:
        print(f"Saved UI response to {ui_output_path}")
    if not args.no_history and not args.no_save_history:
        print(f"Updated chatbot history at {args.history_store}")

    print("\nSAFETY SUMMARY")
    for note in recommendation["safety_summary"]["notes"]:
        print("-", note)

    print("\nROUTINE\n")
    for period in ["morning", "night"]:
        print(period.upper())
        for step in recommendation["routine"][period]:
            print(f"- {step['label']}: {step['title']}")
        print()

    print("\nTOP CATALOGS\n")

    for catalog in results:
        print("=" * 50)
        print(catalog["catalog_title"])
        print("Type:", catalog["catalog_type"])
        print("Score:", catalog["score"])
        print("Theme:", catalog["theme"])
        print("Layout:", catalog["layout"])
        print()

        for product in catalog["products"]:
            print("-", product["title"])
            print("  Brand:", product["brand"])
            print("  Type:", product["product_type"])
            print("  Rating:", product["rating"])
            print("  Price:", product["price"])
            print("  Score:", product["scores"]["overall"])
            print("  Reason:", product["recommendation_reason"])
            print("  Tags:", ", ".join(product["tags"][:8]))
            print()


if __name__ == "__main__":
    main()
