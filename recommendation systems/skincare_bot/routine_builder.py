from ranker import split_terms, term_tokens


class RoutineBuilder:
    AM_STEPS = [
        ("cleanse", "Cleanser"),
        ("tone", "Toner"),
        ("treat", "Serum/Treatment"),
        ("moisturize", "Moisturizer"),
        ("protect", "Sunscreen"),
    ]
    PM_STEPS = [
        ("cleanse", "Cleanser"),
        ("tone", "Toner"),
        ("treat", "Treatment"),
        ("moisturize", "Moisturizer"),
        ("seal", "Face Oil/Seal"),
    ]

    def build(self, profile, catalogs):
        products = self._dedupe_products(catalogs)
        requested_tokens = term_tokens(split_terms(profile.get("requested_ingredients")))

        morning = self._build_period("morning", self.AM_STEPS, products, requested_tokens)
        night = self._build_period("night", self.PM_STEPS, products, requested_tokens)

        notes = []
        if "retinol" in requested_tokens:
            notes.append("Place retinol in the night treatment step, not the morning routine.")
            notes.append("Use sunscreen every morning while using retinol.")
        if profile.get("active_strength_preference") == "beginner":
            notes.append("Start active treatments slowly and keep barrier-support steps consistent.")

        return {
            "morning": morning,
            "night": night,
            "notes": notes,
        }

    def _build_period(self, period, steps, products, requested_tokens):
        routine = []
        used = set()
        for step_key, label in steps:
            product = self._select_product(period, step_key, products, requested_tokens, used)
            if not product:
                continue
            used.add(product["title"])
            routine.append(
                {
                    "step": step_key,
                    "label": label,
                    "product_id": product.get("product_id"),
                    "title": product["title"],
                    "product_type": product.get("product_type"),
                    "usage_time": product.get("usage_time"),
                    "why": self._why(period, step_key, product, requested_tokens),
                }
            )
        return routine

    def _select_product(self, period, step_key, products, requested_tokens, used):
        candidates = []
        for product in products:
            if product["title"] in used:
                continue

            routine_step = str(product.get("routine_step", "")).lower()
            product_type = str(product.get("product_type", "")).lower()
            usage_time = str(product.get("usage_time", "")).lower()
            product_tokens = term_tokens(
                split_terms(product.get("ingredients"))
                + split_terms(product.get("tags"))
                + split_terms(product.get("target_concerns"))
                + [product_type]
            )

            if period == "night" and "retinol" in requested_tokens:
                exfoliant_tokens = {"salicylic", "glycolic", "acid", "aha", "bha", "exfoliation"}
                if exfoliant_tokens & product_tokens and "retinol" not in product_tokens:
                    continue

            if step_key == "protect":
                step_match = product_type == "sunscreen" or product.get("spf_rating", 0) > 0
            elif step_key == "cleanse":
                step_match = product_type == "cleanser" or routine_step == "cleanse"
            elif step_key == "tone":
                step_match = product_type == "toner" or routine_step == "tone"
            elif step_key == "moisturize":
                step_match = product_type == "moisturizer" or routine_step == "moisturize"
            elif step_key == "seal":
                step_match = product_type == "face oil" or routine_step == "seal"
            else:
                step_match = routine_step in {"treat", "mask"} or product_type in {"serum", "treatment", "exfoliant", "acne patch"}

            if not step_match:
                continue

            if period == "morning" and usage_time == "night":
                continue
            if period == "night" and routine_step == "protect" and product_type != "lip balm":
                continue

            score = product.get("score", 0)
            if requested_tokens and requested_tokens & product_tokens:
                score += 80
            if period == "morning" and step_key == "protect":
                score += 50
                if product_type == "sunscreen":
                    score += 90
                elif product_type == "lip balm":
                    score -= 25
            if period == "night" and step_key == "treat":
                score += 35
            candidates.append((score, product))

        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item[0], reverse=True)[0][1]

    def _why(self, period, step_key, product, requested_tokens):
        product_tokens = term_tokens(split_terms(product.get("ingredients")) + split_terms(product.get("tags")))
        if requested_tokens and requested_tokens & product_tokens:
            return "Matches the active ingredient requested in the query."
        if period == "morning" and step_key == "protect":
            return "Protects the routine with SPF."
        if step_key == "moisturize":
            return "Supports the barrier and reduces irritation risk."
        return "Fits the routine step and current recommendation context."

    def _dedupe_products(self, catalogs):
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
