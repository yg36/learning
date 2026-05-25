import math
import re


def split_terms(value):
    if value is None:
        return []

    if isinstance(value, float) and math.isnan(value):
        return []

    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = re.split(r"[|;,]", str(value))

    terms = []
    for item in values:
        item = str(item).strip().lower()
        if not item or item == "nan":
            continue
        terms.append(item)

    return terms


def term_tokens(values):
    tokens = set()
    for value in values:
        normalized = re.sub(r"[^a-z0-9]+", " ", str(value).lower())
        tokens.update(token for token in normalized.split() if token)
    return tokens


def number(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str) and not value.strip():
            return default
        numeric = float(value)
        if math.isnan(numeric):
            return default
        return numeric
    except (TypeError, ValueError):
        return default


class Ranker:
    def rank_products(self, products, user):
        if products.empty:
            return products.copy()

        ranked = products.copy()
        ranked["score"] = ranked.apply(lambda row: self.score_row(row, user), axis=1)
        ranked = ranked.sort_values(["score", "rating", "popularity_score"], ascending=False)

        if "product_title" in ranked.columns:
            ranked = ranked.drop_duplicates("product_title", keep="first")

        return ranked

    def score_row(self, row, user):
        score = 0.0

        score += number(row.get("rating")) * 8
        score += number(row.get("popularity_score")) * 0.45
        score += number(row.get("recommendation_score")) * 45
        score += number(row.get("personalization_score")) * 35
        score += number(row.get("history_affinity_score")) * 35
        score += number(row.get("query_match_score")) * 30
        score += number(row.get("semantic_similarity_score")) * 90
        score += number(row.get("collaborative_signal_score")) * 15
        score += number(row.get("availability_score")) * 8
        score += number(row.get("reorder_rate")) * 10

        score += number(row.get("hovered")) * 4
        score += number(row.get("clicked")) * 8
        score += number(row.get("added_to_cart")) * 12
        score += number(row.get("purchased")) * 18
        score -= number(row.get("negative_feedback")) * 15

        product_terms = self._product_terms(row)
        product_tokens = term_tokens(product_terms)
        title_tokens = term_tokens([row.get("product_title", ""), row.get("product_subcategory", "")])

        matched_catalog_product = str(user.get("matched_catalog_product") or "").strip().lower()
        if matched_catalog_product and matched_catalog_product == str(row.get("product_title", "")).strip().lower():
            score += 55

        product_type = user.get("product_type")
        if product_type and product_type in product_terms:
            score += 25

        query_tokens = term_tokens([user.get("query", ""), user.get("normalized_query", "")])
        query_overlap = len(query_tokens & product_tokens)
        score += min(query_overlap * 3, 24)
        score += min(len(query_tokens & title_tokens) * 8, 32)

        requested_ingredients = split_terms(user.get("requested_ingredients"))
        ingredient_overlap = self._overlap_count(requested_ingredients, product_terms, token_mode=True)
        score += min(ingredient_overlap * 28, 70)

        skin_concerns = split_terms(user.get("skin_concerns"))
        concern_overlap = self._overlap_count(skin_concerns, product_terms, token_mode=True)
        score += min(concern_overlap * 14, 42)

        skin_type = user.get("skin_type")
        suitable_skin_types = set(split_terms(row.get("suitable_skin_types")))
        if skin_type:
            if skin_type in suitable_skin_types or "all" in suitable_skin_types:
                score += 14
            else:
                score -= 8

        avoided_ingredients = split_terms(user.get("avoided_ingredients"))
        avoid_overlap = self._overlap_count(avoided_ingredients, product_terms, token_mode=True)
        score -= avoid_overlap * 28

        if "fragrance" in avoided_ingredients and number(row.get("fragrance_free")):
            score += 8
        if "alcohol" in avoided_ingredients and number(row.get("alcohol_free")):
            score += 8
        if "essential-oils" in avoided_ingredients and number(row.get("essential_oil_free")):
            score += 8

        if user.get("pregnancy_safe_required"):
            if number(row.get("pregnancy_safe")):
                score += 18
            else:
                score -= 80

        if user.get("vegan_preference"):
            score += 8 if number(row.get("vegan")) else -4

        if user.get("cruelty_free_preference"):
            score += 8 if number(row.get("cruelty_free")) else -4

        budget_max = user.get("budget_max")
        if budget_max:
            product_price = number(row.get("product_price"))
            if product_price <= budget_max:
                score += 12
            else:
                score -= min((product_price - budget_max) / 80, 18)

        score += self._weather_boost(row, user.get("weather"))
        score += self._time_boost(row, user.get("time_of_day"))
        score += self._history_boost(row, user)

        return round(score, 3)

    def rank(self, catalogs, user):
        for catalog in catalogs:
            product_scores = [
                number(item.get("score", item.get("scores", {}).get("overall")))
                for item in catalog["products"]
            ]
            catalog["score"] = round(sum(product_scores) / max(len(product_scores), 1), 3)

            if catalog.get("catalog_type") == "history_match":
                catalog["score"] += 60 if self._catalog_aligns_current_query(catalog, user) else 10
            elif catalog.get("catalog_type") == "query_match":
                catalog["score"] += 80 if self._has_strong_current_query(user) else 30

        return sorted(catalogs, key=lambda item: item["score"], reverse=True)

    def _has_strong_current_query(self, user):
        return bool(
            user.get("product_type")
            or split_terms(user.get("requested_ingredients"))
            or split_terms(user.get("avoided_ingredients"))
            or user.get("matched_catalog_product")
        )

    def _catalog_aligns_current_query(self, catalog, user):
        if not self._has_strong_current_query(user):
            return True

        requested_tokens = term_tokens(split_terms(user.get("requested_ingredients")))
        product_type = user.get("product_type")
        matched_catalog_product = str(user.get("matched_catalog_product") or "").strip().lower()

        for item in catalog.get("products", []):
            item_terms = (
                split_terms(item.get("title"))
                + split_terms(item.get("product_type"))
                + split_terms(item.get("ingredients"))
                + split_terms(item.get("tags"))
                + split_terms(item.get("target_concerns"))
            )
            item_tokens = term_tokens(item_terms)
            if matched_catalog_product and matched_catalog_product == str(item.get("title", "")).strip().lower():
                return True
            if product_type and product_type in split_terms(item.get("product_type")):
                return True
            if requested_tokens and requested_tokens & item_tokens:
                return True
        return False

    def _product_terms(self, row):
        fields = [
            "product_title",
            "product_brand",
            "product_subcategory",
            "product_type",
            "key_ingredients",
            "ingredient_tags",
            "product_tags",
            "target_concerns",
            "suitable_skin_types",
            "usage_time",
            "routine_step",
            "texture",
            "finish",
            "semantic_document",
            "content_embedding_text",
            "routine_compatibility_tags",
        ]

        terms = []
        for field in fields:
            terms.extend(split_terms(row.get(field)))
        return terms

    def _history_boost(self, row, user):
        product_tokens = term_tokens(self._product_terms(row))
        clicked_tokens = term_tokens(
            split_terms(user.get("previous_clicked_product_titles"))
            + split_terms(user.get("previous_clicked_tags"))
            + split_terms(user.get("favorite_ingredients"))
        )
        hovered_tokens = term_tokens(
            split_terms(user.get("previous_hovered_product_titles"))
            + split_terms(user.get("previous_hovered_tags"))
            + split_terms(user.get("previous_queries"))
        )

        clicked_overlap = len(product_tokens & clicked_tokens)
        hovered_overlap = len(product_tokens & hovered_tokens)

        boost = min(clicked_overlap * 7, 35)
        boost += min(hovered_overlap * 4, 24)
        return boost

    def _weather_boost(self, row, weather):
        if not weather:
            return 0

        product_terms = set(self._product_terms(row))
        product_tokens = term_tokens(product_terms)

        if weather == "hot":
            return 10 if {"spf", "summer", "sun", "protection"} & product_tokens else 0
        if weather == "humid":
            return 10 if {"oil", "control", "matte", "lightweight"} & product_tokens else 0
        if weather == "cold":
            return 10 if {"barrier", "repair", "hydration", "dryness", "ceramide"} & product_tokens else 0
        if weather == "rainy":
            return 6 if {"lightweight", "gel", "non", "sticky"} & product_tokens else 0
        return 0

    def _time_boost(self, row, time_of_day):
        usage_time = str(row.get("usage_time", "")).strip().lower()
        if not time_of_day or not usage_time:
            return 0
        if usage_time == "anytime" or usage_time == str(time_of_day).lower():
            return 6
        return 0

    def _overlap_count(self, left_terms, right_terms, token_mode=False):
        if token_mode:
            return len(term_tokens(left_terms) & term_tokens(right_terms))
        return len(set(left_terms) & set(right_terms))
