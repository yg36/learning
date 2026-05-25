from ranker import number
from ranker import split_terms
from ranker import term_tokens


class UIComponentBuilder:
    """Build UI-ready blocks from recommendation results.

    This does not render frontend. It gives the frontend a stable contract for
    cards, catalogs, banners, routine timelines, and comparison tables.
    """

    def build(self, profile, recommendation):
        catalogs = recommendation.get("catalogs", [])
        routine = recommendation.get("routine", {})
        safety_summary = recommendation.get("safety_summary", {})

        components = []
        priority = 1

        safety_component = self._safety_banner(safety_summary, profile, priority)
        if safety_component:
            components.append(safety_component)
            priority += 1

        for catalog in catalogs:
            component = self._catalog_component(catalog, priority)
            if component:
                components.append(component)
                priority += 1

        routine_component = self._routine_component(routine, priority)
        if routine_component:
            components.append(routine_component)
            priority += 1

        comparison_component = self._comparison_component(catalogs, priority)
        if comparison_component:
            components.append(comparison_component)

        if not components:
            components.append(self._empty_state())

        return components

    def _safety_banner(self, safety_summary, profile, priority):
        notes = safety_summary.get("notes", [])
        if not notes:
            return None

        severity = "info"
        requested = set(split_terms(profile.get("requested_ingredients")))
        constraints = safety_summary.get("hard_constraints_applied", {})
        if constraints.get("teen_retinoid_guard") or constraints.get("pregnancy_safe"):
            severity = "caution"
        elif requested & {"retinol", "retinoid", "retinal", "salicylic-acid", "glycolic-acid"}:
            severity = "caution"

        return {
            "component_id": "safety-summary",
            "component_type": "safety_banner",
            "title": "Safety notes",
            "priority": priority,
            "layout": "full_width_banner",
            "severity": severity,
            "message": notes[0],
            "items": notes,
            "render_hints": {
                "icon": "shield",
                "tone": severity,
                "dismissible": False,
            },
        }

    def _catalog_component(self, catalog, priority):
        products = catalog.get("products", [])
        if not products:
            return None

        component_type = self._catalog_component_type(catalog.get("catalog_type"))
        return {
            "component_id": self._slug(catalog.get("catalog_type") or catalog.get("catalog_title")),
            "component_type": component_type,
            "title": catalog.get("catalog_title"),
            "priority": priority,
            "layout": self._layout_for_catalog(catalog),
            "catalog_type": catalog.get("catalog_type"),
            "theme": catalog.get("theme"),
            "cards": [
                self._product_card(product, catalog, index + 1)
                for index, product in enumerate(products)
            ],
            "render_hints": {
                "scroll": "horizontal",
                "max_visible_cards": 4,
                "show_reason": True,
            },
            "analytics": {
                "catalog_id": self._slug(catalog.get("catalog_type") or catalog.get("catalog_title")),
                "source": "recommendation_catalog",
            },
        }

    def _catalog_component_type(self, catalog_type):
        if catalog_type == "query_match":
            return "hero_product_carousel"
        if catalog_type == "history_match":
            return "personalized_product_carousel"
        if catalog_type == "routine_next_step":
            return "routine_product_carousel"
        if catalog_type == "budget_friendly":
            return "budget_product_carousel"
        return "product_carousel"

    def _layout_for_catalog(self, catalog):
        catalog_type = catalog.get("catalog_type")
        if catalog_type == "query_match":
            return "large_card_carousel"
        if catalog_type == "history_match":
            return "because_you_viewed_carousel"
        if catalog_type == "routine_next_step":
            return "step_based_row"
        return catalog.get("layout") or "horizontal_scroll"

    def _product_card(self, product, catalog, rank):
        return {
            "card_id": self._slug(product.get("title")),
            "card_variant": self._card_variant(product, catalog),
            "rank": rank,
            "title": product.get("title"),
            "subtitle": self._subtitle(product),
            "brand": product.get("brand"),
            "product_type": product.get("product_type"),
            "price": product.get("price"),
            "rating": product.get("rating"),
            "primary_tags": product.get("tags", [])[:4],
            "badges": self._badges(product),
            "display": self._display(product),
            "explanation": self._explanation(product),
            "actions": self._actions(product),
            "render_hints": {
                "desktop_layout": "product_card",
                "mobile_layout": "compact_product_card",
                "image_aspect_ratio": "1:1",
                "show_badges": True,
                "show_reason": True,
            },
            "analytics": {
                "catalog_id": self._slug(catalog.get("catalog_type") or catalog.get("catalog_title")),
                "slot_id": f"{self._slug(catalog.get('catalog_type'))}_{rank}",
                "rank": rank,
                "product_id": product.get("product_id"),
                "events": ["impression", "click", "save", "add_to_routine"],
            },
        }

    def _card_variant(self, product, catalog):
        catalog_type = catalog.get("catalog_type")
        if catalog_type == "routine_next_step":
            return "routine_step_card"
        if catalog_type == "history_match":
            return "history_match_card"
        if product.get("safety_guidance", {}).get("warnings"):
            return "safety_product_card"
        if number(product.get("discount_percentage")) > 0 or product.get("price_tier") == "budget":
            return "budget_card"
        return "product_card"

    def _subtitle(self, product):
        parts = [
            product.get("brand"),
            product.get("product_type"),
        ]
        return " - ".join(str(part).title() for part in parts if part)

    def _display(self, product):
        rating = product.get("rating")
        return {
            "title": product.get("title"),
            "subtitle": self._subtitle(product),
            "price_text": self._price_label(product) if product.get("price") is not None else "",
            "rating_text": f"{rating} rating" if rating is not None else "",
            "reason_text": product.get("recommendation_reason") or "",
            "badge_text": " / ".join(self._badges(product)[:3]),
        }

    def _badges(self, product):
        badges = []
        ingredients = set(split_terms(product.get("ingredients")))
        safety = product.get("safety_flags", {})

        if product.get("active_strength_level") == "beginner":
            badges.append("Beginner friendly")
        if product.get("usage_time") == "night" or ingredients & {"retinol", "retinoid", "retinal"}:
            badges.append("Night use")
        if number(product.get("spf_rating")) > 0:
            badges.append(f"SPF {int(number(product.get('spf_rating')))}")
        if safety.get("pregnancy_safe"):
            badges.append("Pregnancy safe")
        if safety.get("fragrance_free"):
            badges.append("Fragrance free")
        if safety.get("non_comedogenic"):
            badges.append("Non-comedogenic")
        if product.get("price_tier") == "budget":
            badges.append("Budget pick")
        if number(product.get("rating")) >= 4.7:
            badges.append("Top rated")

        return self._dedupe(badges)[:5]

    def _explanation(self, product):
        scores = product.get("scores", {})
        matched_signals = []
        matched_signals.extend(product.get("ingredients", [])[:3])
        matched_signals.extend(product.get("target_concerns", [])[:2])
        confidence = min(
            0.98,
            (
                number(scores.get("query_match"))
                + number(scores.get("semantic_similarity"))
                + number(scores.get("ingredient_affinity"))
            )
            / 3,
        )

        return {
            "main_reason": product.get("recommendation_reason"),
            "matched_signals": self._dedupe(matched_signals)[:5],
            "confidence": round(confidence, 3),
            "score": scores.get("overall"),
        }

    def _actions(self, product):
        actions = [
            {"action_type": "view_product", "label": "View product"},
            {"action_type": "save_product", "label": "Save"},
        ]
        if product.get("routine_step"):
            actions.append({"action_type": "add_to_routine", "label": "Add to routine"})
        if product.get("redirect_url"):
            actions[0]["url"] = product.get("redirect_url")
        return actions

    def _routine_component(self, routine, priority):
        morning = routine.get("morning", [])
        night = routine.get("night", [])
        if not morning and not night:
            return None

        return {
            "component_id": "routine-timeline",
            "component_type": "routine_timeline",
            "title": "Suggested routine",
            "priority": priority,
            "layout": "two_lane_timeline",
            "sections": [
                self._routine_section("Morning", morning),
                self._routine_section("Night", night),
            ],
            "notes": routine.get("notes", []),
            "render_hints": {
                "show_step_numbers": True,
                "group_by_period": True,
            },
        }

    def _routine_section(self, title, steps):
        return {
            "title": title,
            "steps": [
                {
                    "step_id": f"{self._slug(title)}_{index + 1}",
                    "step": step.get("step"),
                    "label": step.get("label"),
                    "title": step.get("title"),
                    "product_type": step.get("product_type"),
                    "why": step.get("why"),
                }
                for index, step in enumerate(steps)
            ],
        }

    def _comparison_component(self, catalogs, priority):
        products = self._unique_products(catalogs)[:3]
        if len(products) < 2:
            return None

        rows = [
            {
                "label": "Price",
                "values": [self._price_label(product) for product in products],
            },
            {
                "label": "Rating",
                "values": [str(product.get("rating") or "-") for product in products],
            },
            {
                "label": "Key ingredients",
                "values": [", ".join(product.get("ingredients", [])[:3]) for product in products],
            },
            {
                "label": "Best for",
                "values": [", ".join(product.get("target_concerns", [])[:2]) for product in products],
            },
            {
                "label": "Use",
                "values": [str(product.get("usage_time") or "anytime").title() for product in products],
            },
        ]

        return {
            "component_id": "top-product-comparison",
            "component_type": "comparison_table",
            "title": "Quick comparison",
            "priority": priority,
            "layout": "responsive_table",
            "columns": [
                {
                    "product_id": product.get("product_id"),
                    "title": product.get("title"),
                    "card_variant": "comparison_card",
                    "badges": self._badges(product)[:3],
                }
                for product in products
            ],
            "rows": rows,
            "render_hints": {
                "sticky_first_column": True,
                "compact_on_mobile": True,
            },
        }

    def _unique_products(self, catalogs):
        products = []
        seen = set()
        for catalog in catalogs:
            for product in catalog.get("products", []):
                title = product.get("title")
                if not title or title in seen:
                    continue
                products.append(product)
                seen.add(title)
        return products

    def _price_label(self, product):
        price = product.get("price")
        if price is None:
            return "-"
        return f"INR {int(number(price))}"

    def _empty_state(self):
        return {
            "component_id": "no-results",
            "component_type": "empty_state",
            "title": "No exact match found",
            "priority": 1,
            "layout": "centered_message",
            "message": "Showing fallback skincare picks when available.",
        }

    def _dedupe(self, values):
        result = []
        seen = set()
        for value in values:
            value = str(value).strip()
            if not value or value.lower() in seen:
                continue
            result.append(value)
            seen.add(value.lower())
        return result

    def _slug(self, value):
        tokens = term_tokens([value or "component"])
        if not tokens:
            return "component"
        return "_".join(sorted(tokens))
