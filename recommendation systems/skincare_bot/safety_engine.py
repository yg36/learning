from ranker import split_terms, term_tokens


class SafetyEngine:
    STRONG_ACTIVES = {"retinol", "retinoid", "retinal", "salicylic-acid", "glycolic-acid"}

    def apply_filters(self, df, profile):
        filtered = df.copy()

        if profile.get("pregnancy_safe_required"):
            safe = filtered[filtered["pregnancy_safe"].fillna(0).astype(int) == 1]
            if not safe.empty:
                filtered = safe

        age = profile.get("user_age")
        requested = set(split_terms(profile.get("requested_ingredients")))
        if age is not None and age < 18 and requested & {"retinol", "retinoid", "retinal"}:
            teen_safe = filtered[
                ~filtered["key_ingredients"].fillna("").str.lower().str.contains("retinol|retinal|retinoid", regex=True)
            ]
            if not teen_safe.empty:
                filtered = teen_safe

        avoided = term_tokens(split_terms(profile.get("avoided_ingredients")))
        if avoided:
            candidate = filtered[
                filtered.apply(
                    lambda row: not bool(
                        avoided
                        & term_tokens(split_terms(row.get("key_ingredients")) + split_terms(row.get("product_tags")))
                    ),
                    axis=1,
                )
            ]
            if not candidate.empty:
                filtered = candidate

        return filtered

    def annotate_catalogs(self, catalogs, profile):
        for catalog in catalogs:
            for product in catalog.get("products", []):
                product["safety_guidance"] = self.product_guidance(product, profile)
        return catalogs

    def summarize(self, catalogs, profile):
        notes = []
        requested = set(split_terms(profile.get("requested_ingredients")))
        age = profile.get("user_age")

        if requested & {"retinol", "retinoid", "retinal"}:
            notes.append("Retinol should be used at night and paired with daily sunscreen.")
            notes.append("Start 1-2 nights per week, then increase only if skin tolerates it.")
            if age is not None and age < 18:
                notes.append("For users under 18, retinol should be treated as dermatologist-guided care.")
            elif age is not None and age <= 21:
                notes.append("At age 20 or nearby, prefer beginner-strength retinol and avoid using it without a clear concern.")

        if profile.get("pregnancy_safe_required"):
            notes.append("Pregnancy-safe mode is active: retinoids and salicylic-acid caution products are filtered out where possible.")

        if profile.get("skin_type") == "sensitive" or "sensitivity" in split_terms(profile.get("skin_concerns")):
            notes.append("Sensitive-skin mode: fragrance-free, low-comedogenic, and patch-test-friendly products are preferred.")

        if not notes:
            notes.append("No high-risk skincare safety constraints detected for this query.")

        return {
            "notes": notes,
            "hard_constraints_applied": {
                "pregnancy_safe": bool(profile.get("pregnancy_safe_required")),
                "teen_retinoid_guard": bool(age is not None and age < 18 and requested & {"retinol", "retinoid", "retinal"}),
                "avoided_ingredients": split_terms(profile.get("avoided_ingredients")),
            },
        }

    def product_guidance(self, product, profile):
        ingredients = set(split_terms(product.get("ingredients")))
        guidance = []
        warnings = []

        if "retinol" in ingredients:
            guidance.append("Use at night only.")
            guidance.append("Follow with moisturizer and use sunscreen the next morning.")
            warnings.append("Avoid combining with AHA/BHA exfoliants in the same routine.")
            if profile.get("user_age") is not None and profile["user_age"] <= 21:
                warnings.append("Beginner-strength use is preferred for this age profile.")

        if {"salicylic-acid", "glycolic-acid"} & ingredients:
            guidance.append("Use slowly and monitor dryness or stinging.")
            warnings.append("Avoid stacking with retinol on the same night.")

        if product.get("safety_flags", {}).get("pregnancy_safe") is False:
            warnings.append("Not marked pregnancy-safe.")

        if product.get("safety_flags", {}).get("fragrance_free") is False and profile.get("skin_type") == "sensitive":
            warnings.append("Fragrance-free alternative may be safer for sensitive skin.")

        return {
            "guidance": guidance,
            "warnings": warnings,
            "patch_test_recommended": bool(warnings or ingredients & self.STRONG_ACTIVES),
        }
