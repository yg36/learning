from pathlib import Path

import pandas as pd

from catalog_generator import CatalogGenerator
from embedding_engine import EmbeddingEngine
from ranker import Ranker, split_terms, term_tokens
from routine_builder import RoutineBuilder
from safety_engine import SafetyEngine


class CatalogEngine:
    DEFAULT_DATASET = Path("data/skincare_history_catalog_500rows.csv")

    def __init__(self, path=None):
        self.path = Path(path or self.DEFAULT_DATASET)
        self.df = pd.read_csv(self.path)
        self.generator = CatalogGenerator()
        self.ranker = Ranker()
        self.embedding_engine = EmbeddingEngine(self.df)
        self.safety_engine = SafetyEngine()
        self.routine_builder = RoutineBuilder()
        self._validate_dataset()

    def get_catalogs(self, user, limit=5):
        profile = self._normalize_user(user)
        return self._build_catalogs(profile, limit=limit)

    def recommend(self, user, limit=5):
        profile = self._normalize_user(user)
        catalogs = self._build_catalogs(profile, limit=limit)
        catalogs = self.safety_engine.annotate_catalogs(catalogs, profile)
        routine_products = self._routine_products(profile)
        routine = self.routine_builder.build(profile, catalogs + [{"products": routine_products}])
        safety_summary = self.safety_engine.summarize(catalogs, profile)

        return {
            "catalogs": catalogs,
            "routine": routine,
            "safety_summary": safety_summary,
        }

    def _build_catalogs(self, profile, limit=5):
        filtered = self._skincare_only(self.df)
        filtered = self._apply_hard_filters(filtered, profile)
        filtered = self.safety_engine.apply_filters(filtered, profile)

        if filtered.empty:
            fallback = self._skincare_only(self.df)
            filtered = self.safety_engine.apply_filters(fallback, profile)
            if filtered.empty:
                filtered = fallback

        filtered = self.embedding_engine.add_similarity_scores(filtered, profile)
        ranked_products = self.ranker.rank_products(filtered, profile)
        catalogs = self.generator.generate(profile, ranked_products)
        ranked_catalogs = self.ranker.rank(catalogs, profile)

        return ranked_catalogs[:limit]

    def _routine_products(self, profile):
        routine_profile = dict(profile)
        routine_profile["product_type"] = None
        routine_profile["requested_ingredients"] = []
        candidates = self._skincare_only(self.df)
        candidates = self.safety_engine.apply_filters(candidates, profile)
        if candidates.empty:
            candidates = self._skincare_only(self.df)
        candidates = self.embedding_engine.add_similarity_scores(candidates, routine_profile)
        ranked = self.ranker.rank_products(candidates, routine_profile)
        return self.generator.products_from_rows(routine_profile, ranked, limit=50)

    def _validate_dataset(self):
        required = {
            "product_category",
            "preferred_category",
            "semantic_category",
            "product_title",
            "product_type",
            "product_tags",
            "key_ingredients",
            "target_concerns",
            "history_affinity_score",
            "query_match_score",
            "recommendation_score",
            "routine_step",
        }
        missing = required - set(self.df.columns)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(f"Dataset {self.path} is missing required columns: {missing_columns}")

        skincare_rows = self._skincare_only(self.df)
        if skincare_rows.empty:
            raise ValueError(f"Dataset {self.path} does not contain skincare rows")

    def _normalize_user(self, user):
        profile = dict(user or {})
        profile.setdefault("semantic_category", "skincare")
        profile.setdefault("preferred_category", "skincare")
        profile.setdefault("skin_concerns", [])
        profile.setdefault("requested_ingredients", [])
        profile.setdefault("avoided_ingredients", [])
        profile.setdefault("previous_queries", [])
        profile.setdefault("previous_hovered_product_titles", [])
        profile.setdefault("previous_hovered_tags", [])
        profile.setdefault("previous_clicked_product_titles", [])
        profile.setdefault("previous_clicked_tags", [])
        profile.setdefault("favorite_ingredients", [])
        profile.setdefault("disliked_ingredients", [])
        profile.setdefault("pregnancy_safe_required", False)
        profile.setdefault("vegan_preference", False)
        profile.setdefault("cruelty_free_preference", False)
        profile.setdefault("weather", profile.get("weather_condition", "normal"))
        profile.setdefault("time_of_day", "morning")
        return profile

    def _skincare_only(self, df):
        mask = (
            df["product_category"].astype(str).str.lower().eq("skincare")
            & df["preferred_category"].astype(str).str.lower().eq("skincare")
            & df["semantic_category"].astype(str).str.lower().eq("skincare")
        )
        return df[mask].copy()

    def _apply_hard_filters(self, df, profile):
        filtered = df.copy()

        product_type = profile.get("product_type")
        if product_type:
            filtered = self._fallback_filter(
                filtered,
                lambda rows: rows[
                    rows.apply(
                        lambda row: product_type
                        in split_terms(row.get("product_type")) + split_terms(row.get("product_subcategory")),
                        axis=1,
                    )
                ],
            )

        skin_type = profile.get("skin_type")
        if skin_type:
            filtered = self._fallback_filter(
                filtered,
                lambda rows: rows[
                    rows["suitable_skin_types"].apply(
                        lambda value: skin_type in split_terms(value) or "all" in split_terms(value)
                    )
                ],
            )

        concerns = split_terms(profile.get("skin_concerns"))
        if concerns:
            concern_tokens = term_tokens(concerns)
            filtered = self._fallback_filter(
                filtered,
                lambda rows: rows[
                    rows.apply(
                        lambda row: bool(
                            concern_tokens
                            & term_tokens(split_terms(row.get("target_concerns")) + split_terms(row.get("product_tags")))
                        ),
                        axis=1,
                    )
                ],
            )

        ingredients = split_terms(profile.get("requested_ingredients"))
        if ingredients:
            ingredient_tokens = term_tokens(ingredients)
            filtered = self._fallback_filter(
                filtered,
                lambda rows: rows[
                    rows.apply(
                        lambda row: bool(
                            ingredient_tokens
                            & term_tokens(split_terms(row.get("key_ingredients")) + split_terms(row.get("product_tags")))
                        ),
                        axis=1,
                    )
                ],
            )

        avoided = split_terms(profile.get("avoided_ingredients"))
        if avoided:
            filtered = self._remove_avoided_ingredients(filtered, avoided)

        budget_max = profile.get("budget_max")
        if budget_max:
            filtered = self._fallback_filter(
                filtered,
                lambda rows: rows[rows["product_price"].fillna(999999).astype(float) <= float(budget_max)],
            )

        if profile.get("pregnancy_safe_required"):
            safe = filtered[filtered["pregnancy_safe"].fillna(0).astype(int) == 1]
            if not safe.empty:
                filtered = safe

        return filtered

    def _fallback_filter(self, current, filter_fn, minimum=8, minimum_unique=3):
        candidate = filter_fn(current)
        candidate_unique = self._unique_product_count(candidate)
        current_unique = self._unique_product_count(current)

        if len(candidate) >= minimum and candidate_unique >= minimum_unique:
            return candidate
        if len(candidate) > 0 and current_unique < minimum_unique:
            return candidate
        return current

    def _unique_product_count(self, df):
        if df.empty:
            return 0
        if "product_title" not in df.columns:
            return len(df)
        return df["product_title"].nunique()

    def _remove_avoided_ingredients(self, df, avoided):
        avoid_tokens = term_tokens(avoided)
        if not avoid_tokens:
            return df

        def is_safe(row):
            product_tokens = term_tokens(split_terms(row.get("key_ingredients")) + split_terms(row.get("product_tags")))
            if not (product_tokens & avoid_tokens):
                return True
            if "fragrance" in avoid_tokens and int(row.get("fragrance_free", 0)) == 1:
                return True
            if "alcohol" in avoid_tokens and int(row.get("alcohol_free", 0)) == 1:
                return True
            return False

        candidate = df[df.apply(is_safe, axis=1)]
        return candidate if len(candidate) >= 8 else df
