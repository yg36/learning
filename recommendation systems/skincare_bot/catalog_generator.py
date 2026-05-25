from ranker import number, split_terms, term_tokens
from rules import CATALOG_TYPES


class CatalogGenerator:
    def products_from_rows(self, user, products, limit=40):
        if products.empty:
            return []

        catalog_rule = {"title": "Routine Source", "type": "routine_source", "limit": limit}
        payloads = []
        used_titles = set()
        for _, row in products.iterrows():
            title = row.get("product_title")
            if title in used_titles:
                continue
            used_titles.add(title)
            payloads.append(self._product_payload(row, user, catalog_rule))
            if len(payloads) == limit:
                break
        return payloads

    def generate(self, user, products):
        catalogs = []

        for catalog_rule in CATALOG_TYPES:
            used_titles = set()
            items = self._select_items(catalog_rule["type"], products, user)
            if items.empty:
                continue

            items = self._sort_items(catalog_rule["type"], items, user)
            catalog_products = []

            for _, row in items.iterrows():
                title = row.get("product_title")
                if title in used_titles:
                    continue

                used_titles.add(title)
                catalog_products.append(self._product_payload(row, user, catalog_rule))

                if len(catalog_products) == catalog_rule.get("limit", 4):
                    break

            if not catalog_products:
                continue

            first = items.iloc[0]
            catalogs.append(
                {
                    "catalog_title": catalog_rule["title"],
                    "catalog_type": catalog_rule["type"],
                    "theme": first.get("theme", "clean"),
                    "layout": first.get("layout_type", "grid"),
                    "total_products": len(catalog_products),
                    "products": catalog_products,
                }
            )

        return catalogs

    def _sort_items(self, catalog_type, items, user):
        items = items.copy()
        items["_catalog_sort_score"] = items.apply(
            lambda row: self._catalog_sort_score(catalog_type, row, user),
            axis=1,
        )
        return items.sort_values(["_catalog_sort_score", "score"], ascending=False)

    def _catalog_sort_score(self, catalog_type, row, user):
        if catalog_type == "history_match":
            history_tokens = term_tokens(
                split_terms(user.get("previous_clicked_product_titles"))
                + split_terms(user.get("previous_clicked_tags"))
                + split_terms(user.get("previous_hovered_product_titles"))
                + split_terms(user.get("previous_hovered_tags"))
                + split_terms(user.get("previous_queries"))
                + split_terms(user.get("favorite_ingredients"))
            )
            product_tokens = self._row_tokens(row)
            explicit_history_boost = min(len(history_tokens & product_tokens) * 12, 60)
            return number(row.get("score")) + number(row.get("history_affinity_score")) * 50 + explicit_history_boost

        if catalog_type == "query_match":
            product_type = user.get("product_type")
            product_type_boost = 35 if product_type and product_type in split_terms(row.get("product_type")) else 0
            query_tokens = term_tokens([user.get("query", ""), user.get("normalized_query", "")])
            title_tokens = term_tokens([row.get("product_title", ""), row.get("product_subcategory", "")])
            ingredient_overlap = len(
                term_tokens(split_terms(user.get("requested_ingredients")))
                & term_tokens(split_terms(row.get("key_ingredients")) + split_terms(row.get("product_tags")))
            )
            return (
                number(row.get("score")) * 0.45
                + number(row.get("query_match_score")) * 120
                + number(row.get("semantic_similarity_score")) * 140
                + product_type_boost
                + min(len(query_tokens & title_tokens) * 14, 56)
                + min(ingredient_overlap * 20, 40)
            )

        if catalog_type == "concern_solution":
            concerns = term_tokens(split_terms(user.get("skin_concerns")))
            concern_overlap = len(concerns & term_tokens(split_terms(row.get("target_concerns")) + split_terms(row.get("product_tags"))))
            return number(row.get("score")) * 0.7 + number(row.get("concern_affinity_score")) * 90 + concern_overlap * 18

        if catalog_type == "budget_friendly":
            price = max(number(row.get("product_price"), 999999), 1)
            return number(row.get("score")) + max(0, 1000 - price) / 20

        if catalog_type == "weather_ready":
            return number(row.get("score")) + number(row.get("spf_rating")) * 0.5

        return number(row.get("score"))

    def _select_items(self, catalog_type, products, user):
        if catalog_type == "history_match":
            if not self._has_user_history(user):
                return products.head(0)
            return products[products["history_affinity_score"].fillna(0) >= 0.45]

        if catalog_type == "query_match":
            query_tokens = term_tokens([user.get("query", ""), user.get("normalized_query", "")])
            product_type = user.get("product_type")

            return products[
                products.apply(
                    lambda row: (
                        number(row.get("query_match_score")) >= 0.25
                        or (product_type and product_type in split_terms(row.get("product_type")))
                        or bool(query_tokens & self._row_tokens(row))
                    ),
                    axis=1,
                )
            ]

        if catalog_type == "concern_solution":
            concerns = term_tokens(split_terms(user.get("skin_concerns")))
            if not concerns:
                return products[products["concern_affinity_score"].fillna(0) >= 0.45]
            candidate = products[
                products.apply(
                    lambda row: bool(concerns & term_tokens(split_terms(row.get("target_concerns")) + split_terms(row.get("product_tags")))),
                    axis=1,
                )
            ]
            return candidate if self._unique_product_count(candidate) >= 3 else products

        if catalog_type == "routine_next_step":
            return products.sort_values(["score", "routine_step"], ascending=[False, True])

        if catalog_type == "weather_ready":
            weather = user.get("weather")
            if weather == "hot":
                return self._contains_any(products, ["spf", "summer", "sun-protection"])
            if weather == "humid":
                return self._contains_any(products, ["oil-control", "matte", "lightweight", "gel"])
            if weather == "cold":
                return self._contains_any(products, ["barrier", "repair", "ceramide", "hydration"])
            return products.head(0)

        if catalog_type == "budget_friendly":
            budget_max = user.get("budget_max")
            if budget_max:
                return products[products["product_price"].fillna(999999) <= budget_max]
            return products[products["price_tier"].isin(["budget", "mid"])]

        if catalog_type == "trending":
            return products.sort_values(["popularity_score", "rating"], ascending=False)

        if catalog_type == "beginner_safe":
            return products[
                (products["fragrance_free"].fillna(0).astype(int) == 1)
                | (products["comedogenic_risk"].fillna("").str.lower() == "low")
            ]

        return products

    def _unique_product_count(self, products):
        if products.empty:
            return 0
        if "product_title" not in products.columns:
            return len(products)
        return products["product_title"].nunique()

    def _has_user_history(self, user):
        history_fields = [
            "previous_queries",
            "previous_hovered_product_titles",
            "previous_hovered_tags",
            "previous_clicked_product_titles",
            "previous_clicked_tags",
            "favorite_ingredients",
        ]
        return any(split_terms(user.get(field)) for field in history_fields)

    def _contains_any(self, products, terms):
        wanted = term_tokens(terms)
        return products[
            products.apply(
                lambda row: bool(
                    wanted
                    & term_tokens(
                        split_terms(row.get("product_tags"))
                        + split_terms(row.get("key_ingredients"))
                        + split_terms(row.get("product_type"))
                        + split_terms(row.get("target_concerns"))
                    )
                ),
                axis=1,
            )
        ]

    def _row_tokens(self, row):
        return term_tokens(
            split_terms(row.get("product_title"))
            + split_terms(row.get("product_subcategory"))
            + split_terms(row.get("product_type"))
            + split_terms(row.get("key_ingredients"))
            + split_terms(row.get("ingredient_tags"))
            + split_terms(row.get("product_tags"))
            + split_terms(row.get("target_concerns"))
        )

    def _product_payload(self, row, user, catalog_rule):
        tags = split_terms(row.get("product_tags"))
        ingredients = split_terms(row.get("key_ingredients"))
        concerns = split_terms(row.get("target_concerns"))

        return {
            "product_id": row.get("product_id"),
            "title": row.get("product_title"),
            "brand": row.get("product_brand"),
            "category": row.get("product_category"),
            "subcategory": row.get("product_subcategory"),
            "product_type": row.get("product_type"),
            "score": number(row.get("score")),
            "price": number(row.get("product_price")),
            "price_tier": row.get("price_tier"),
            "discount_percentage": number(row.get("discount_percentage")),
            "rating": number(row.get("rating")),
            "review_count": int(number(row.get("review_count"))),
            "inventory_status": row.get("inventory_status"),
            "redirect_url": row.get("redirect_url"),
            "tags": tags,
            "ingredients": ingredients,
            "target_concerns": concerns,
            "suitable_skin_types": split_terms(row.get("suitable_skin_types")),
            "usage_time": row.get("usage_time"),
            "routine_step": row.get("routine_step"),
            "texture": row.get("texture"),
            "finish": row.get("finish"),
            "active_strength_level": row.get("active_strength_level"),
            "recommended_frequency": row.get("recommended_frequency"),
            "minimum_recommended_age": int(number(row.get("minimum_recommended_age"))),
            "max_usage_per_week": int(number(row.get("max_usage_per_week"))),
            "routine_metadata": {
                "stage_order": int(number(row.get("routine_stage_order"), 99)),
                "am_fit": bool(number(row.get("am_routine_fit"))),
                "pm_fit": bool(number(row.get("pm_routine_fit"))),
                "compatible_with_steps": split_terms(row.get("compatible_with_steps")),
            },
            "spf_rating": int(number(row.get("spf_rating"))),
            "pa_rating": row.get("pa_rating"),
            "safety_flags": {
                "alcohol_free": bool(number(row.get("alcohol_free"))),
                "fragrance_free": bool(number(row.get("fragrance_free"))),
                "essential_oil_free": bool(number(row.get("essential_oil_free"))),
                "non_comedogenic": bool(number(row.get("non_comedogenic"))),
                "pregnancy_safe": bool(number(row.get("pregnancy_safe"))),
                "vegan": bool(number(row.get("vegan"))),
                "cruelty_free": bool(number(row.get("cruelty_free"))),
            },
            "scores": {
                "overall": number(row.get("score")),
                "recommendation": number(row.get("recommendation_score")),
                "personalization": number(row.get("personalization_score")),
                "history_affinity": number(row.get("history_affinity_score")),
                "query_match": number(row.get("query_match_score")),
                "concern_affinity": number(row.get("concern_affinity_score")),
                "ingredient_affinity": number(row.get("ingredient_affinity_score")),
                "semantic_similarity": number(row.get("semantic_similarity_score")),
            },
            "retrieval_context": {
                "semantic_backend": row.get("semantic_backend"),
            },
            "ui_context": {
                "layout": row.get("layout_type"),
                "theme": row.get("theme"),
                "rank_position": int(number(row.get("rank_position"), 999)),
            },
            "analytics": {
                "shown": bool(number(row.get("shown"))),
                "hovered": bool(number(row.get("hovered"))),
                "clicked": bool(number(row.get("clicked"))),
                "purchased": bool(number(row.get("purchased"))),
                "added_to_cart": bool(number(row.get("added_to_cart"))),
                "wishlisted": bool(number(row.get("wishlisted"))),
                "shared": bool(number(row.get("shared"))),
                "watch_time_seconds": int(number(row.get("watch_time_seconds"))),
                "hover_time_seconds": int(number(row.get("hover_time_seconds"))),
                "scroll_depth": int(number(row.get("scroll_depth"))),
                "dwell_time_seconds": int(number(row.get("dwell_time_seconds"))),
                "feedback_rating": number(row.get("feedback_rating"), None),
                "conversion": bool(number(row.get("conversion"))),
                "negative_feedback": bool(number(row.get("negative_feedback"))),
            },
            "history_context": {
                "previous_queries": split_terms(row.get("previous_queries")),
                "previous_hovered_titles": split_terms(row.get("previous_hovered_product_titles")),
                "previous_clicked_titles": split_terms(row.get("previous_clicked_product_titles")),
                "previous_clicked_tags": split_terms(row.get("previous_clicked_tags")),
                "last_interaction_type": row.get("last_interaction_type"),
            },
            "recommendation_reason": self._reason(row, user, catalog_rule),
            "next_best_action": row.get("next_best_action"),
        }

    def _reason(self, row, user, catalog_rule):
        product_terms = term_tokens(
            split_terms(row.get("product_tags"))
            + split_terms(row.get("key_ingredients"))
            + split_terms(row.get("target_concerns"))
        )
        user_history = term_tokens(
            split_terms(user.get("previous_clicked_product_titles"))
            + split_terms(user.get("previous_clicked_tags"))
            + split_terms(user.get("previous_hovered_product_titles"))
            + split_terms(user.get("previous_hovered_tags"))
            + split_terms(user.get("previous_queries"))
        )
        concerns = term_tokens(split_terms(user.get("skin_concerns")))
        ingredients = term_tokens(split_terms(user.get("requested_ingredients")))
        matched_catalog_product = str(user.get("matched_catalog_product") or "").strip().lower()

        if matched_catalog_product and matched_catalog_product == str(row.get("product_title", "")).strip().lower():
            return "Directly matches the product intent detected from your query."
        if product_terms & ingredients:
            return "Matches the ingredient intent in your query."
        if product_terms & concerns:
            return "Targets the skin concern detected from your query."
        if product_terms & user_history:
            return "Matches your previous clicks, hovers, or searches."
        if catalog_rule["type"] == "weather_ready":
            return "Fits the weather context detected for this session."
        return row.get("recommendation_reason", "Recommended from skincare affinity signals.")
