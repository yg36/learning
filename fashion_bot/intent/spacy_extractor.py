import re
import spacy

nlp = spacy.load("en_core_web_sm")


# =========================
# CATEGORY MAP
# =========================

CATEGORY_MAP = {
    "jacket": "jackets",
    "hoodie": "jackets",
    "coat": "jackets",
    "windbreaker": "jackets",

    "shirt": "shirts",
    "tshirt": "shirts",
    "tee": "shirts",

    "jean": "jeans",
    "denim": "jeans",

    "shoe": "shoes",
    "sneaker": "shoes",
    "boot": "shoes",
}


# =========================
# COLOR MAP
# =========================

COLOR_MAP = {
    "black": "black",
    "blue": "blue",
    "red": "red",
    "white": "white",
    "green": "green",
    "navy": "navy",
    "grey": "grey",
}


# =========================
# STYLE MAP
# =========================

STYLE_MAP = {
    "premium": "premium",
    "luxury": "premium",

    "trendy": "trendy",
    "stylish": "trendy",
    "fashionable": "trendy",

    "casual": "casual",

    "sporty": "sports",
    "sports": "sports",

    "minimal": "minimal",

    "oversized": "trendy",
    "streetwear": "trendy",
}


# =========================
# PRICE NORMALIZER
# =========================

def normalize_price(value, has_k=False):

    value = int(value)

    if has_k:
        value *= 1000

    return value


# =========================
# INTENT EXTRACTOR
# =========================

def extract_intent(query):

    doc = nlp(query.lower())

    intent = {}

    detected_styles = []

    # -------------------------
    # TOKEN ANALYSIS
    # -------------------------

    for token in doc:

        lemma = token.lemma_

        # CATEGORY
        if lemma in CATEGORY_MAP:
            intent["category"] = CATEGORY_MAP[lemma]

        # COLOR
        if lemma in COLOR_MAP:
            intent["color"] = COLOR_MAP[lemma]

        # STYLE
        if lemma in STYLE_MAP:
            detected_styles.append(
                STYLE_MAP[lemma]
            )

    # REMOVE DUPLICATES
    if detected_styles:
        intent["styles"] = list(
            set(detected_styles)
        )

    # -------------------------
    # PRICE UNDER
    # -------------------------

    under_match = re.search(
        r'under\s+(\d+)(k)?',
        query.lower()
    )

    if under_match:

        has_k = under_match.group(2) is not None

        intent["max_price"] = normalize_price(
            under_match.group(1),
            has_k
        )

    # -------------------------
    # PRICE ABOVE
    # -------------------------

    above_match = re.search(
        r'(above|over)\s+(\d+)(k)?',
        query.lower()
    )

    if above_match:

        has_k = above_match.group(3) is not None

        intent["min_price"] = normalize_price(
            above_match.group(2),
            has_k
        )

    return intent