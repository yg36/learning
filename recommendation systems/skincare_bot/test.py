import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from api import app
from catalog_engine import CatalogEngine
from data_contracts import validate_catalog_dataset
from data_visualizer import visualize_dataset
from dataset_builder import FIELDNAMES, OUTPUT_PATH, write_dataset
from embedding_engine import EmbeddingEngine
from history_manager import load_user_history
from history_manager import update_user_history
from intent_extractor import IntentExtractor
from recommendation_service import RecommendationService
from schemas import UIResponse
from ui_component_builder import UIComponentBuilder


class DatasetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path(OUTPUT_PATH).exists():
            write_dataset()
        cls.df = pd.read_csv(OUTPUT_PATH)

    def test_dataset_size_and_schema(self):
        self.assertGreaterEqual(len(self.df), 700)
        self.assertGreaterEqual(len(self.df.columns), 170)
        self.assertEqual(len(FIELDNAMES), len(self.df.columns))

    def test_dataset_is_skincare_only(self):
        self.assertEqual(set(self.df["product_category"].str.lower()), {"skincare"})
        self.assertEqual(set(self.df["preferred_category"].str.lower()), {"skincare"})
        self.assertEqual(set(self.df["semantic_category"].str.lower()), {"skincare"})

    def test_history_columns_are_present(self):
        expected = {
            "previous_queries",
            "previous_hovered_product_titles",
            "previous_hovered_tags",
            "previous_clicked_product_titles",
            "previous_clicked_tags",
            "hover_count_7d",
            "click_count_7d",
            "history_affinity_score",
            "query_match_score",
        }
        self.assertTrue(expected.issubset(self.df.columns))

    def test_enriched_skincare_columns_are_present(self):
        expected = {
            "semantic_document",
            "active_strength_level",
            "minimum_recommended_age",
            "recommended_frequency",
            "avoid_with_ingredients",
            "routine_compatibility_tags",
            "sunscreen_required_after_use",
            "barrier_support_score",
        }
        self.assertTrue(expected.issubset(self.df.columns))


class RecommendationBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path(OUTPUT_PATH).exists():
            write_dataset()
        cls.extractor = IntentExtractor()
        cls.engine = CatalogEngine(OUTPUT_PATH)

    def test_history_aware_recommendation_uses_prior_clicks(self):
        history = {
            "previous_queries": ["vitamin c for glow", "serum for dull skin"],
            "previous_clicked_product_titles": ["Vitamin C Glow Serum"],
            "previous_clicked_tags": ["vitamin-c|glow|dullness|serum"],
            "previous_hovered_product_titles": ["Snail Mucin Essence"],
            "favorite_ingredients": ["vitamin-c"],
        }
        profile = self.extractor.extract(
            "Need a vitamin c serum for dullness under 1000",
            history=history,
        )
        catalogs = self.engine.get_catalogs(profile)

        self.assertGreater(len(catalogs), 0)
        self.assertIn("history_match", [catalog["catalog_type"] for catalog in catalogs])
        self.assertEqual(catalogs[0]["products"][0]["title"], "Vitamin C Glow Serum")

        top_products = catalogs[0]["products"]
        flattened_terms = " ".join(
            " ".join(product["tags"] + product["ingredients"] + [product["title"].lower()])
            for product in top_products
        )
        self.assertIn("vitamin", flattened_terms)
        self.assertIn("glow", flattened_terms)

    def test_avoided_fragrance_prefers_safe_products(self):
        profile = self.extractor.extract(
            "sensitive skin moisturizer without fragrance for redness"
        )
        catalogs = self.engine.get_catalogs(profile)
        products = [product for catalog in catalogs for product in catalog["products"]]

        self.assertGreater(len(products), 0)
        self.assertTrue(any(product["safety_flags"]["fragrance_free"] for product in products))

    def test_specific_product_phrase_beats_broad_spf_alias(self):
        profile = self.extractor.extract("lip balm with spf for chapped lips")

        self.assertEqual(profile["product_type"], "lip balm")
        self.assertIn("dryness", profile["skin_concerns"])

    def test_query_catalog_keeps_direct_product_type_match(self):
        history = {
            "previous_queries": ["niacinamide serum for pores"],
            "previous_clicked_tags": ["niacinamide|oil-control|pores"],
        }
        profile = self.extractor.extract("oily skin sunscreen for summer under 800", history=history)
        catalogs = self.engine.get_catalogs(profile)
        query_catalog = next(catalog for catalog in catalogs if catalog["catalog_type"] == "query_match")

        self.assertEqual(query_catalog["products"][0]["product_type"], "sunscreen")

    def test_no_history_session_does_not_show_history_catalog(self):
        profile = self.extractor.extract("lip balm with spf for chapped lips")
        catalogs = self.engine.get_catalogs(profile)

        self.assertNotIn("history_match", [catalog["catalog_type"] for catalog in catalogs])
        self.assertEqual(catalogs[0]["products"][0]["product_type"], "lip balm")

    def test_title_match_can_override_generic_popularity(self):
        profile = self.extractor.extract("dry winter barrier repair cream")
        catalogs = self.engine.get_catalogs(profile)
        query_catalog = next(catalog for catalog in catalogs if catalog["catalog_type"] == "query_match")

        self.assertEqual(query_catalog["products"][0]["title"], "Barrier Repair Ceramide Cream")

    def test_without_ingredient_is_treated_as_avoidance(self):
        profile = self.extractor.extract("night treatment without retinol")

        self.assertIn("retinol", profile["avoided_ingredients"])
        self.assertNotIn("retinol", profile["requested_ingredients"])

    def test_pregnancy_safe_query_filters_unsafe_products(self):
        profile = self.extractor.extract("pregnancy safe treatment for dark spots without retinol")
        catalogs = self.engine.get_catalogs(profile)
        products = [product for catalog in catalogs for product in catalog["products"]]

        self.assertGreater(len(products), 0)
        self.assertTrue(all(product["safety_flags"]["pregnancy_safe"] for product in products))
        self.assertTrue(all("retinol" not in product["ingredients"] for product in products))

    def test_catalog_aware_extractor_overrides_generic_cream_alias(self):
        extractor = IntentExtractor(catalog_path=OUTPUT_PATH)
        profile = extractor.extract("kojic acid dark spot cream")

        self.assertEqual(profile["product_type"], "treatment")
        self.assertEqual(profile["matched_catalog_product"], "Kojic Acid Dark Spot Cream")
        self.assertIn("kojic-acid", profile["requested_ingredients"])
        self.assertEqual(profile["intent_model"], "hybrid_catalog_retrieval_intent_v2")

    def test_plural_retinol_age_query_beats_stale_history(self):
        history = {
            "previous_queries": ["oily skin sunscreen for summer under 800"],
            "previous_clicked_product_titles": [
                "Matte Mineral Sunscreen SPF50",
                "Lip Barrier Balm SPF30",
                "Oil Control Niacinamide Serum",
            ],
            "previous_clicked_tags": [
                "spf|matte|oil-control|outdoor|sun protection",
                "lip-care|spf|barrier|travel|sun protection",
                "oil-control|pores|acne|lightweight|niacinamide|oiliness",
            ],
        }
        profile = self.extractor.extract(
            "tell me retinols to use . My current age is 20",
            history=history,
        )
        catalogs = self.engine.get_catalogs(profile)

        self.assertEqual(profile["intent"], "recommendation")
        self.assertEqual(profile["user_age"], 20)
        self.assertEqual(profile["age_group"], "young_adult")
        self.assertIn("retinol", profile["requested_ingredients"])
        self.assertNotIn("sun protection", profile["skin_concerns"])
        self.assertEqual(catalogs[0]["catalog_type"], "query_match")
        self.assertEqual(catalogs[0]["products"][0]["title"], "Retinol Renewal Night Serum")
        self.assertIn("query", catalogs[0]["products"][0]["recommendation_reason"])

    def test_routine_builder_places_retinol_at_night_with_spf_in_morning(self):
        profile = self.extractor.extract("tell me retinols to use . My current age is 20")
        bundle = self.engine.recommend(profile)

        morning_types = {step["product_type"] for step in bundle["routine"]["morning"]}
        morning_protect = [step for step in bundle["routine"]["morning"] if step["step"] == "protect"]
        night_titles = {step["title"] for step in bundle["routine"]["night"]}
        night_ingredients = " ".join(
            " ".join(product["ingredients"])
            for catalog in bundle["catalogs"]
            for product in catalog["products"]
            if product["title"] in night_titles
        )

        self.assertIn("sunscreen", morning_types)
        self.assertEqual(morning_protect[0]["product_type"], "sunscreen")
        self.assertIn("Retinol Renewal Night Serum", night_titles)
        self.assertNotIn("glycolic-acid", night_ingredients)

    def test_teen_retinol_query_uses_safety_guard(self):
        profile = self.extractor.extract("I am 16 tell me retinol serum for acne")
        bundle = self.engine.recommend(profile)
        products = [product for catalog in bundle["catalogs"] for product in catalog["products"]]

        self.assertTrue(bundle["safety_summary"]["hard_constraints_applied"]["teen_retinoid_guard"])
        self.assertTrue(all("retinol" not in product["ingredients"] for product in products))

    def test_semantic_embedding_score_prioritizes_hydration_water_gel(self):
        profile = self.extractor.extract("plump lightweight hydration water gel")
        catalogs = self.engine.get_catalogs(profile)

        self.assertEqual(catalogs[0]["products"][0]["title"], "Hyaluronic Acid Water Gel")
        self.assertGreater(catalogs[0]["products"][0]["scores"]["semantic_similarity"], 0)

    def test_varied_intent_extraction_cases(self):
        cases = [
            (
                "I am 20, suggest beginner retinol night serum",
                {"intent": "recommendation", "user_age": 20, "product_type": "serum", "ingredient": "retinol"},
            ),
            (
                "retinol for acne marks age 20",
                {"user_age": 20, "ingredient": "retinol", "concerns": {"acne", "dark spots"}},
            ),
            (
                "pregnancy safe dark spot treatment without retinol",
                {"intent": "safety_check", "avoid": "retinol", "pregnancy_safe_required": True},
            ),
            (
                "teenage acne routine age 16",
                {"intent": "routine_building", "user_age": 16, "age_group": "teen", "concerns": {"acne"}},
            ),
            (
                "compare retinol and vitamin c",
                {"intent": "comparison", "ingredients": {"retinol", "vitamin-c"}},
            ),
            (
                "daag ke liye kojic acid treatment",
                {"query_language": "hinglish", "ingredient": "kojic-acid", "concerns": {"dark spots"}},
            ),
        ]

        for query, expected in cases:
            with self.subTest(query=query):
                profile = self.extractor.extract(query)
                for key in ["intent", "user_age", "age_group", "product_type", "query_language"]:
                    if key in expected:
                        self.assertEqual(profile.get(key), expected[key])
                if "ingredient" in expected:
                    self.assertIn(expected["ingredient"], profile["requested_ingredients"])
                if "ingredients" in expected:
                    self.assertTrue(expected["ingredients"].issubset(set(profile["requested_ingredients"])))
                if "avoid" in expected:
                    self.assertIn(expected["avoid"], profile["avoided_ingredients"])
                if "pregnancy_safe_required" in expected:
                    self.assertEqual(profile["pregnancy_safe_required"], expected["pregnancy_safe_required"])
                if "concerns" in expected:
                    self.assertTrue(expected["concerns"].issubset(set(profile["skin_concerns"])))


class VisualizationTests(unittest.TestCase):
    def test_visualized_pdf_is_created(self):
        if not Path(OUTPUT_PATH).exists():
            write_dataset()

        output_path = Path("visualizedData.pdf")
        result = visualize_dataset(OUTPUT_PATH, output_path)

        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 1000)
        self.assertEqual(result.read_bytes()[:4], b"%PDF")


class ChatbotFlowTests(unittest.TestCase):
    def test_history_is_saved_and_loaded_automatically(self):
        history_path = Path(tempfile.gettempdir()) / "skincare_bot_test_history.json"
        if history_path.exists():
            history_path.unlink()

        profile = IntentExtractor().extract("vitamin c serum for glow")
        catalogs = CatalogEngine(OUTPUT_PATH).get_catalogs(profile)
        update_user_history({}, "vitamin c serum for glow", profile, catalogs, history_path)
        loaded = load_user_history(history_path)

        self.assertIn("vitamin c serum for glow", loaded["previous_queries"])
        self.assertGreater(len(loaded["previous_clicked_product_titles"]), 0)

    def test_cli_query_does_not_prompt_for_optional_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            history_path = temp_path / "history.json"
            output_path = temp_path / "output.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--query",
                    "lip balm with spf for chapped lips",
                    "--skip-visualization",
                    "--history-store",
                    str(history_path),
                    "--output",
                    str(output_path),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=20,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Optional previous history", result.stdout)
            self.assertTrue(history_path.exists())
            self.assertTrue(output_path.exists())
            self.assertGreater(len(json.loads(output_path.read_text(encoding="utf-8"))), 0)


class BackendUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path(OUTPUT_PATH).exists():
            write_dataset()

    def test_recommendation_service_returns_typed_response_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RecommendationService(
                dataset_path=OUTPUT_PATH,
                history_store=Path(temp_dir) / "history.json",
            )
            payload = service.recommend(
                "tell me retinols to use . My current age is 20",
                use_saved_history=False,
            )

        self.assertIn("profile", payload)
        self.assertIn("catalogs", payload)
        self.assertIn("routine", payload)
        self.assertIn("safety_summary", payload)
        self.assertIn("components", payload)
        self.assertEqual(payload["catalogs"][0]["products"][0]["title"], "Retinol Renewal Night Serum")

    def test_embedding_engine_uses_sklearn_backend(self):
        df = pd.read_csv(OUTPUT_PATH).head(20)
        engine = EmbeddingEngine(df)
        result = engine.add_similarity_scores(
            df,
            {
                "query": "hydrating gel cream",
                "normalized_query": "hydrating gel cream",
                "skin_concerns": ["dryness"],
                "requested_ingredients": ["hyaluronic-acid"],
            },
        )

        self.assertEqual(set(result["semantic_backend"]), {"sklearn_tfidf_vectorizer_v1"})
        self.assertIn("semantic_similarity_score", result.columns)

    def test_data_contract_accepts_current_dataset(self):
        report = validate_catalog_dataset(OUTPUT_PATH)

        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.row_count, 760)
        self.assertGreaterEqual(report.column_count, 170)

    def test_data_contract_rejects_non_skincare_rows(self):
        df = pd.read_csv(OUTPUT_PATH)
        df.loc[0, "product_category"] = "haircare"
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad_catalog.csv"
            df.to_csv(bad_path, index=False)
            report = validate_catalog_dataset(bad_path)

        self.assertFalse(report.valid)
        self.assertTrue(any("product_category" in error for error in report.errors))

    def test_fastapi_recommend_and_validation_endpoints(self):
        client = TestClient(app)

        health = client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        recommendation = client.post(
            "/recommend",
            json={
                "query": "tell me retinols to use . My current age is 20",
                "use_saved_history": False,
                "save_history": False,
            },
        )
        self.assertEqual(recommendation.status_code, 200, recommendation.text)
        self.assertEqual(
            recommendation.json()["catalogs"][0]["products"][0]["title"],
            "Retinol Renewal Night Serum",
        )
        self.assertIn("components", recommendation.json())

        validation = client.get("/validate-data")
        self.assertEqual(validation.status_code, 200)
        self.assertTrue(validation.json()["valid"])

    def test_fastapi_recommend_ui_endpoint_returns_ui_only_contract(self):
        client = TestClient(app)
        response = client.post(
            "/recommend-ui",
            json={
                "query": "oily skin sunscreen for summer under 800",
                "use_saved_history": False,
                "save_history": False,
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["response_type"], "ui_components")
        self.assertIn("components", data)
        self.assertNotIn("profile", data)
        self.assertNotIn("catalogs", data)
        self.assertNotIn("previous_queries", json.dumps(data))


class UIComponentBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path(OUTPUT_PATH).exists():
            write_dataset()
        cls.extractor = IntentExtractor()
        cls.engine = CatalogEngine(OUTPUT_PATH)
        cls.builder = UIComponentBuilder()

    def test_components_include_cards_routine_safety_and_comparison(self):
        profile = self.extractor.extract("tell me retinols to use . My current age is 20")
        recommendation = self.engine.recommend(profile)
        components = self.builder.build(profile, recommendation)
        component_types = {component["component_type"] for component in components}

        self.assertIn("safety_banner", component_types)
        self.assertIn("hero_product_carousel", component_types)
        self.assertIn("routine_timeline", component_types)
        self.assertIn("comparison_table", component_types)

    def test_product_cards_have_frontend_contract_fields(self):
        profile = self.extractor.extract("oily skin sunscreen for summer under 800")
        recommendation = self.engine.recommend(profile)
        components = self.builder.build(profile, recommendation)
        carousel = next(component for component in components if component["component_type"].endswith("carousel"))
        card = carousel["cards"][0]

        self.assertIn("card_variant", card)
        self.assertIn("badges", card)
        self.assertIn("explanation", card)
        self.assertIn("analytics", card)
        self.assertIn("actions", card)
        self.assertGreaterEqual(card["analytics"]["rank"], 1)

    def test_service_payload_components_are_json_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RecommendationService(
                dataset_path=OUTPUT_PATH,
                history_store=Path(temp_dir) / "history.json",
            )
            payload = service.recommend(
                "pregnancy safe dark spot treatment without retinol",
                use_saved_history=False,
            )

        safety_component = next(
            component for component in payload["components"] if component["component_type"] == "safety_banner"
        )
        self.assertEqual(safety_component["severity"], "caution")
        self.assertTrue(any(component["priority"] >= 1 for component in payload["components"]))

    def test_ui_response_builder_removes_backend_debug_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RecommendationService(
                dataset_path=OUTPUT_PATH,
                history_store=Path(temp_dir) / "history.json",
            )
            payload = service.recommend(
                "tell me retinols to use . My current age is 20",
                history={"previous_queries": ["old sunscreen query"]},
                use_saved_history=False,
            )
            ui_response = service.build_ui_response(payload, request_id="test_request")

        self.assertEqual(ui_response["request_id"], "test_request")
        self.assertEqual(ui_response["response_type"], "ui_components")
        self.assertNotIn("profile", ui_response)
        self.assertNotIn("catalogs", ui_response)
        self.assertNotIn("old sunscreen query", json.dumps(ui_response))

    def test_product_card_display_fields_are_present(self):
        profile = self.extractor.extract("tell me retinols to use . My current age is 20")
        recommendation = self.engine.recommend(profile)
        components = self.builder.build(profile, recommendation)
        carousel = next(component for component in components if "carousel" in component["component_type"])
        card = carousel["cards"][0]

        self.assertIn("display", card)
        self.assertIn("price_text", card["display"])
        self.assertIn("rating_text", card["display"])
        self.assertIn("events", card["analytics"])

    def test_ui_schema_and_samples_are_valid(self):
        self.assertTrue(Path("ui_response.schema.json").exists())
        sample_paths = [
            Path("samples/retinol_query_ui_response.json"),
            Path("samples/sunscreen_query_ui_response.json"),
            Path("samples/pregnancy_safe_ui_response.json"),
            Path("samples/no_result_ui_response.json"),
        ]

        for sample_path in sample_paths:
            with self.subTest(sample=sample_path):
                self.assertTrue(sample_path.exists())
                data = json.loads(sample_path.read_text(encoding="utf-8"))
                parsed = UIResponse.model_validate(data)
                self.assertEqual(parsed.response_type, "ui_components")


class UIArtifactCLITests(unittest.TestCase):
    def test_cli_writes_ui_response_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            history_path = temp_path / "history.json"
            output_path = temp_path / "output.json"
            ui_output_path = temp_path / "ui_response.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--query",
                    "oily skin sunscreen for summer under 800",
                    "--skip-visualization",
                    "--history-store",
                    str(history_path),
                    "--output",
                    str(output_path),
                    "--ui-output",
                    str(ui_output_path),
                    "--no-save-history",
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            self.assertTrue(ui_output_path.exists())
            data = json.loads(ui_output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["response_type"], "ui_components")
            self.assertIn("components", data)
            self.assertNotIn("profile", data)


if __name__ == "__main__":
    unittest.main()
