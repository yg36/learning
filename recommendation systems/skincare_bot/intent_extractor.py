from pathlib import Path
import re
import unicodedata

import pandas as pd


class IntentExtractor:
    DEFAULT_CATALOG_PATH = Path("data/skincare_history_catalog_500rows.csv")
    MODEL_NAME = "hybrid_catalog_retrieval_intent_v2"

    PRODUCT_ALIASES = {
        "serum": ["serum", "ampoule"],
        "toner": ["toner"],
        "moisturizer": ["moisturizer", "moisturiser", "cream", "gel cream"],
        "sunscreen": ["sunscreen", "spf", "sun protection", "sunblock"],
        "cleanser": ["cleanser", "face wash", "wash"],
        "face oil": ["face oil"],
        "mask": ["mask", "sleeping mask", "clay mask"],
        "exfoliant": ["exfoliant", "exfoliator", "peel"],
        "treatment": ["treatment", "spot corrector", "spot treatment"],
        "mist": ["mist", "face mist"],
        "lip balm": ["lip balm", "lip care", "lip spf"],
        "acne patch": ["acne patch", "pimple patch"],
        "essence": ["essence"],
    }

    CONCERN_ALIASES = {
        "acne": ["acne", "pimples", "pimple", "breakout", "whiteheads", "munhase"],
        "pores": ["pores", "large pores"],
        "oiliness": ["oily", "oiliness", "greasy", "sebum", "oil control"],
        "dryness": ["dry", "dryness", "dehydrated", "flaky", "flaking", "chapped", "chapped lips"],
        "barrier damage": ["barrier", "damaged barrier", "skin barrier"],
        "dullness": ["dull", "dullness", "glow", "brightening"],
        "dark spots": ["dark spots", "spots", "marks", "hyperpigmentation", "pigmentation", "daag"],
        "redness": ["redness", "red", "calm", "calming"],
        "sensitivity": ["sensitive", "sensitivity", "irritation", "irritated"],
        "texture": ["texture", "bumpy", "rough"],
        "fine lines": ["fine lines", "wrinkles", "anti aging", "anti-aging"],
        "sun protection": ["sun", "spf", "sunscreen", "tanning", "uv"],
        "blackheads": ["blackheads", "black heads"],
        "uneven tone": ["uneven tone", "tone"],
    }

    INGREDIENT_ALIASES = {
        "vitamin-c": ["vitamin c", "vitamin-c", "ascorbic"],
        "niacinamide": ["niacinamide"],
        "salicylic-acid": ["salicylic", "bha", "salicylic acid"],
        "glycolic-acid": ["glycolic", "aha", "glycolic acid"],
        "hyaluronic-acid": ["hyaluronic", "hyaluronic acid"],
        "ceramide": ["ceramide", "ceramides"],
        "centella": ["centella", "cica"],
        "retinol": ["retinol", "retinols", "retinoid", "retinoids", "retinal"],
        "peptide": ["peptide", "peptides"],
        "squalane": ["squalane"],
        "green-tea": ["green tea", "green-tea"],
        "oat": ["oat", "oats"],
        "azelaic-acid": ["azelaic", "azelaic acid"],
        "kojic-acid": ["kojic", "kojic acid"],
        "rice-extract": ["rice", "rice extract"],
        "fragrance": ["fragrance", "perfume"],
        "alcohol": ["alcohol"],
        "essential-oils": ["essential oil", "essential oils"],
    }

    SKIN_TYPES = ["oily", "dry", "combination", "sensitive", "normal"]
    GENERIC_PRODUCT_ALIASES = {"cream", "gel cream", "spf", "sun protection", "wash"}

    def __init__(self, catalog_path=None):
        path = Path(catalog_path) if catalog_path else self.DEFAULT_CATALOG_PATH
        self.catalog_entries = self._load_catalog_entries(path)

    def extract(self, text, history=None):
        normalized = self._normalize(text)
        history = history or {}
        catalog_match = self._best_catalog_match(normalized)

        product_type, product_confidence, product_alias = self._detect_product_type(normalized)
        if self._should_use_catalog_product_type(catalog_match, product_type, product_confidence, product_alias):
            product_type = catalog_match["product_type"]
            product_confidence = max(product_confidence, catalog_match["confidence"])

        requested, avoided = self._detect_ingredients(normalized)
        requested = self._merge_catalog_ingredients(requested, avoided, normalized, catalog_match)

        concerns = self._detect_many(normalized, self.CONCERN_ALIASES)
        concerns = self._merge_catalog_concerns(concerns, normalized, catalog_match)

        profile = {
            "semantic_category": "skincare",
            "preferred_category": "skincare",
            "query": text.strip(),
            "normalized_query": normalized,
            "intent": self._classify_intent(normalized),
            "query_language": self._detect_language(normalized),
            "intent_model": self.MODEL_NAME,
            "product_type": product_type,
            "time_of_day": self._detect_time(normalized),
            "weather": self._detect_weather(normalized),
            "skin_type": self._detect_skin_type(normalized),
            "user_age": self._detect_age(normalized),
            "age_group": self._age_group(self._detect_age(normalized)),
            "skin_concerns": concerns,
            "requested_ingredients": requested,
            "avoided_ingredients": avoided,
            "active_strength_preference": self._active_strength_preference(normalized, requested),
            "active_safety_notes": self._active_safety_notes(self._detect_age(normalized), requested),
            "budget_min": None,
            "budget_max": self._detect_budget_max(normalized),
            "pregnancy_safe_required": self._detect_any(normalized, ["pregnancy safe", "pregnant", "pregnancy-safe"]),
            "vegan_preference": self._detect_any(normalized, ["vegan"]),
            "cruelty_free_preference": self._detect_any(normalized, ["cruelty free", "cruelty-free"]),
            "previous_queries": [],
            "previous_hovered_product_titles": [],
            "previous_hovered_tags": [],
            "previous_clicked_product_titles": [],
            "previous_clicked_tags": [],
            "favorite_ingredients": [],
            "disliked_ingredients": [],
            "matched_catalog_product": catalog_match["title"] if catalog_match else None,
            "confidence_scores": {
                "product_type": round(product_confidence, 3),
                "catalog_match": round(catalog_match["confidence"], 3) if catalog_match else 0,
                "concerns": round(min(0.98, 0.35 + len(concerns) * 0.18), 3) if concerns else 0,
                "ingredients": round(min(0.98, 0.35 + len(requested + avoided) * 0.2), 3)
                if requested or avoided
                else 0,
            },
        }

        self._merge_history(profile, history)

        if not profile["skin_type"]:
            profile["skin_type"] = self._skin_type_from_history(profile)

        if not profile["skin_concerns"] and self._should_infer_concerns_from_history(profile):
            profile["skin_concerns"] = self._concerns_from_history(profile)

        if not profile["requested_ingredients"]:
            profile["requested_ingredients"] = profile["favorite_ingredients"][:3]

        if not profile["avoided_ingredients"]:
            profile["avoided_ingredients"] = profile["disliked_ingredients"][:3]

        return profile

    def _load_catalog_entries(self, path):
        if not path.exists():
            return []

        try:
            df = pd.read_csv(path)
        except (OSError, pd.errors.ParserError):
            return []

        required = {"product_title", "product_type"}
        if not required.issubset(df.columns):
            return []

        optional_columns = ["key_ingredients", "product_tags", "target_concerns", "product_subcategory"]
        for column in optional_columns:
            if column not in df.columns:
                df[column] = ""

        entries = []
        for _, row in df.drop_duplicates("product_title").iterrows():
            title = str(row.get("product_title", ""))
            entries.append(
                {
                    "title": title,
                    "title_tokens": self._tokens(title),
                    "product_type": str(row.get("product_type", "")).lower(),
                    "subcategory": str(row.get("product_subcategory", "")).lower(),
                    "ingredients": self._split_terms(row.get("key_ingredients")),
                    "tags": self._split_terms(row.get("product_tags")),
                    "concerns": self._split_terms(row.get("target_concerns")),
                }
            )
        return entries

    def _best_catalog_match(self, text):
        if not self.catalog_entries:
            return None

        query_tokens = self._tokens(text)
        if not query_tokens:
            return None

        best = None
        for entry in self.catalog_entries:
            title_overlap = len(query_tokens & entry["title_tokens"])
            ingredient_overlap = len(query_tokens & self._tokens(entry["ingredients"]))
            concern_overlap = len(query_tokens & self._tokens(entry["concerns"]))
            tag_overlap = len(query_tokens & self._tokens(entry["tags"]))

            title_score = title_overlap / max(len(entry["title_tokens"]), 1)
            score = (
                title_score * 0.58
                + min(ingredient_overlap * 0.13, 0.26)
                + min(concern_overlap * 0.1, 0.2)
                + min(tag_overlap * 0.04, 0.12)
            )

            if score < 0.28:
                continue

            candidate = {
                "title": entry["title"],
                "product_type": entry["product_type"],
                "ingredients": entry["ingredients"],
                "concerns": entry["concerns"],
                "confidence": min(score, 0.98),
            }
            if not best or candidate["confidence"] > best["confidence"]:
                best = candidate

        return best

    def _detect_product_type(self, text):
        match = self._best_alias_match(text, self.PRODUCT_ALIASES)
        if not match:
            return None, 0, None
        return match["canonical"], match["confidence"], match["alias"]

    def _should_use_catalog_product_type(self, catalog_match, product_type, confidence, alias):
        if not catalog_match:
            return False
        if not product_type:
            return True
        if alias in self.GENERIC_PRODUCT_ALIASES and catalog_match["confidence"] >= 0.38:
            return True
        if catalog_match["confidence"] >= confidence + 0.18:
            return True
        return False

    def _detect_skin_type(self, text):
        for skin_type in self.SKIN_TYPES:
            if self._contains_phrase(text, skin_type):
                return skin_type
        return None

    def _detect_many(self, text, alias_map):
        matches = []
        for canonical, aliases in alias_map.items():
            if any(self._contains_phrase(text, alias) for alias in aliases):
                matches.append(canonical)
        return self._dedupe(matches)

    def _detect_ingredients(self, text):
        requested = []
        avoided = []
        for canonical, aliases in self.INGREDIENT_ALIASES.items():
            if not any(self._contains_phrase(text, alias) for alias in aliases):
                continue

            if self._is_avoided_ingredient(text, aliases):
                avoided.append(canonical)
            else:
                requested.append(canonical)

        return self._dedupe(requested), self._dedupe(avoided)

    def _merge_catalog_ingredients(self, requested, avoided, text, catalog_match):
        if not catalog_match:
            return requested

        query_tokens = self._tokens(text)
        inferred = []
        for ingredient in catalog_match["ingredients"]:
            ingredient_tokens = self._tokens(ingredient)
            if ingredient in avoided:
                continue
            if ingredient_tokens and ingredient_tokens.issubset(query_tokens):
                inferred.append(ingredient)

        return self._dedupe(requested + inferred)

    def _merge_catalog_concerns(self, concerns, text, catalog_match):
        if not catalog_match:
            return concerns

        query_tokens = self._tokens(text)
        inferred = []
        for concern in catalog_match["concerns"]:
            if query_tokens & self._tokens(concern):
                inferred.append(concern)

        return self._dedupe(concerns + inferred)

    def _detect_budget_max(self, text):
        patterns = [
            r"(?:under|below|less than|within|upto|up to)\s*(?:rs\.?|inr)?\s*(\d{2,5})",
            r"(?:rs\.?|inr)\s*(\d{2,5})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _detect_age(self, text):
        patterns = [
            r"(?:my\s+)?(?:current\s+)?age\s*(?:is|=|:)?\s*(\d{1,2})\b",
            r"\bi\s*(?:am|'m)\s*(\d{1,2})\b",
            r"\b(\d{1,2})\s*(?:years?\s*old|yrs?\s*old|yo)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            age = int(match.group(1))
            if 8 <= age <= 90:
                return age
        return None

    def _age_group(self, age):
        if age is None:
            return None
        if age < 18:
            return "teen"
        if age <= 24:
            return "young_adult"
        if age <= 39:
            return "adult"
        return "mature"

    def _active_strength_preference(self, text, requested):
        active_ingredients = {"retinol", "retinoid", "retinal", "salicylic-acid", "glycolic-acid"}
        if "beginner" in text or "first time" in text or "start" in text:
            return "beginner"
        if "retinol" in requested or self._tokens(requested) & active_ingredients:
            return "beginner"
        return None

    def _active_safety_notes(self, age, requested):
        notes = []
        if "retinol" in requested:
            notes.append("Use retinol at night and pair it with daily sunscreen.")
            notes.append("Start slowly and avoid combining it with strong exfoliating acids in the same routine.")
            if age is not None and age < 18:
                notes.append("Retinol under 18 should be treated as dermatologist-guided care.")
            elif age is not None and age <= 21:
                notes.append("At this age, prefer beginner-strength retinol only if there is a clear concern.")
        return notes

    def _detect_weather(self, text):
        if any(word in text for word in ["summer", "hot", "sweat", "sunny"]):
            return "hot"
        if any(word in text for word in ["humid", "monsoon", "sticky"]):
            return "humid"
        if any(word in text for word in ["winter", "cold", "chapped"]):
            return "cold"
        if "rain" in text:
            return "rainy"
        return "normal"

    def _detect_time(self, text):
        if any(word in text for word in ["night", "pm", "sleep"]):
            return "night"
        if "evening" in text:
            return "evening"
        if "afternoon" in text:
            return "afternoon"
        return "morning"

    def _classify_intent(self, text):
        if any(word in text for word in ["compare", " vs ", "versus", "better than"]):
            return "comparison"
        if any(word in text for word in ["routine", "steps", "am routine", "pm routine"]):
            return "routine_building"
        if any(word in text for word in ["repurchase", "again", "reorder", "same as"]):
            return "repurchase"
        if any(word in text for word in ["safe", "pregnant", "without", "avoid", "free"]):
            return "safety_check"
        if any(word in text for word in ["recommend", "suggest", "best", "need", "tell me", "show me"]):
            return "recommendation"
        return "search"

    def _detect_language(self, text):
        hinglish_terms = {"daag", "munhase", "chehra", "twacha"}
        if self._tokens(text) & hinglish_terms:
            return "hinglish"
        return "english"

    def _detect_any(self, text, phrases):
        return any(self._contains_phrase(text, phrase) for phrase in phrases)

    def _merge_history(self, profile, history):
        mapping = {
            "previous_queries": ["previous_queries", "queries", "recent_searches"],
            "previous_hovered_product_titles": ["previous_hovered_product_titles", "hovered_titles", "hovers"],
            "previous_hovered_tags": ["previous_hovered_tags", "hovered_tags"],
            "previous_clicked_product_titles": ["previous_clicked_product_titles", "clicked_titles", "clicks", "recent_clicks"],
            "previous_clicked_tags": ["previous_clicked_tags", "clicked_tags"],
            "favorite_ingredients": ["favorite_ingredients", "liked_ingredients"],
            "disliked_ingredients": ["disliked_ingredients", "avoided_ingredients"],
        }

        for target_key, source_keys in mapping.items():
            values = []
            for source_key in source_keys:
                values.extend(self._as_list(history.get(source_key)))
            normalized_values = [self._normalize(value) for value in values]
            profile[target_key] = self._dedupe(profile[target_key] + normalized_values)

    def _skin_type_from_history(self, profile):
        history_text = " ".join(profile["previous_queries"])
        return self._detect_skin_type(history_text)

    def _concerns_from_history(self, profile):
        history_text = " ".join(
            profile["previous_queries"]
            + profile["previous_hovered_product_titles"]
            + profile["previous_hovered_tags"]
            + profile["previous_clicked_product_titles"]
            + profile["previous_clicked_tags"]
        )
        return self._detect_many(history_text, self.CONCERN_ALIASES)

    def _should_infer_concerns_from_history(self, profile):
        current_query_has_strong_signal = any(
            [
                profile.get("product_type"),
                profile.get("requested_ingredients"),
                profile.get("avoided_ingredients"),
                profile.get("matched_catalog_product"),
                profile.get("budget_max"),
                profile.get("pregnancy_safe_required"),
                profile.get("vegan_preference"),
                profile.get("cruelty_free_preference"),
            ]
        )
        return not current_query_has_strong_signal

    def _best_alias_match(self, text, alias_map):
        matches = []
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                if not self._contains_phrase(text, alias):
                    continue
                word_bonus = min(len(alias.split()) * 0.12, 0.28)
                char_bonus = min(len(alias) / 45, 0.2)
                confidence = min(0.98, 0.42 + word_bonus + char_bonus)
                matches.append(
                    {
                        "canonical": canonical,
                        "alias": alias,
                        "confidence": confidence,
                        "specificity": (len(alias.split()), len(alias)),
                    }
                )

        if not matches:
            return None

        return sorted(matches, key=lambda item: (item["confidence"], item["specificity"]), reverse=True)[0]

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return re.split(r"[|;,]", str(value))

    def _split_terms(self, value):
        return [self._normalize(term) for term in self._as_list(value) if self._normalize(term)]

    def _dedupe(self, values):
        result = []
        seen = set()
        for value in values:
            value = self._normalize(str(value))
            if value and value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def _tokens(self, value):
        if isinstance(value, (list, tuple, set)):
            value = " ".join(str(item) for item in value)
        value = self._normalize(value).replace("-", " ")
        tokens = set(re.findall(r"[a-z0-9]+", value))
        variants = set(tokens)
        for token in tokens:
            if len(token) > 3 and token.endswith("s"):
                variants.add(token[:-1])
        return variants

    def _normalize(self, text):
        text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
        text = text.lower().replace("&", " and ")
        text = re.sub(r"[^a-z0-9+\-./\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _contains_phrase(self, text, phrase):
        normalized_phrase = self._normalize(phrase)
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    def _is_avoided_ingredient(self, text, aliases):
        for alias in aliases:
            normalized_alias = re.escape(self._normalize(alias))
            patterns = [
                rf"(?:without|avoid|avoiding|no)\s+{normalized_alias}(?![a-z0-9])",
                rf"(?<![a-z0-9]){normalized_alias}\s*[- ]?free",
            ]
            if any(re.search(pattern, text) for pattern in patterns):
                return True
        return False
